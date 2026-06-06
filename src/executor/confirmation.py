"""ConfirmationManager — state-machine driven manual confirmation flow.

Integrates with WorkQueue for durable job tracking and AuditLedger for
operator-override audit trail.  Review timeout is tracked via an internal
deadline dict (``_deadlines``) rather than WorkQueue leases, ensuring
deterministic per-intent timeout independent of queue ordering.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Optional

from src.executor.models import ExecutionIntent
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent
from src.state.queue import WorkQueue

# 15-minute review window.
_REVIEW_TTL = timedelta(minutes=15)


class ConfirmationManager:
    """Manages the manual confirmation flow for ``ExecutionIntent`` objects.

    When a ``confirmation_mode = "confirm"`` runtime requires human review,
    the ``ConfirmationManager`` transitions an intent through the review
    lifecycle:  ``ready`` → ``human_review_pending`` → ``ready | cancelled |
    expired_review``.

    Review timeout is tracked via an internal ``_deadlines`` dict that maps
    each ``execution_id`` to an absolute deadline (``entered_at + 15 min``).
    ``check_timeouts()`` compares the stored deadline against the current
    time — no WorkQueue lease involved.

    Parameters
    ----------
    work_queue : WorkQueue
        Durable work queue used for job tracking (enqueue / ack / dead_letter).
    ledger : AuditLedger
        Append-only audit ledger for recording operator overrides.
    """

    def __init__(self, work_queue: WorkQueue, ledger: AuditLedger) -> None:
        self._queue = work_queue
        self._ledger = ledger
        # execution_id → ExecutionIntent (in-memory tracking)
        self._intents: dict[str, ExecutionIntent] = {}
        # execution_id → WorkQueue job_id
        self._job_map: dict[str, str] = {}
        # execution_id → absolute deadline (datetime) for the 15-min review
        self._deadlines: dict[str, datetime] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enter_review(self, intent: ExecutionIntent) -> str:
        """Transition an intent to ``human_review_pending`` and enqueue it.

        Parameters
        ----------
        intent : ExecutionIntent
            The intent to enter for human review.  Must currently be in
            ``ready`` or ``previewed`` status.

        Returns
        -------
        str
            The WorkQueue ``job_id`` for the new confirmation job.

        Raises
        ------
        ValueError
            If the intent status is not ``ready`` or ``previewed``.
        """
        if intent.status not in ("ready", "previewed"):
            raise ValueError(
                f"Cannot enter review from status '{intent.status}'; "
                f"expected 'ready' or 'previewed'"
            )

        updated = intent.model_copy(update={"status": "human_review_pending"})
        self._intents[intent.execution_id] = updated

        job_id = self._queue.enqueue(
            job_type="confirmation",
            idempotency_key=f"confirm:{intent.execution_id}",
            payload={
                "execution_id": intent.execution_id,
                "original_quantity": intent.quantity,
            },
        )
        self._job_map[intent.execution_id] = job_id

        # Record the absolute deadline for the 15-min review window.
        entered_at = datetime.now(UTC)
        self._deadlines[intent.execution_id] = entered_at + _REVIEW_TTL

        return job_id

    def confirm(self, execution_id: str) -> ExecutionIntent:
        """Confirm the intent: status → ``ready``.

        Acks the WorkQueue job so the lease is released.

        Parameters
        ----------
        execution_id : str
            The ``execution_id`` of the intent to confirm.

        Returns
        -------
        ExecutionIntent
            The updated intent with ``status='ready'``.

        Raises
        ------
        ValueError
            If the intent is not in ``human_review_pending`` status.
        """
        intent = self._require_pending(execution_id)
        job_id = self._job_map[execution_id]
        self._queue.ack(job_id)
        updated = intent.model_copy(update={"status": "ready"})
        self._intents[execution_id] = updated
        return updated

    def skip(self, execution_id: str) -> ExecutionIntent:
        """Skip the intent: status → ``cancelled``.

        Acks the WorkQueue job so the lease is released.

        Parameters
        ----------
        execution_id : str
            The ``execution_id`` of the intent to skip.

        Returns
        -------
        ExecutionIntent
            The updated intent with ``status='cancelled'``.

        Raises
        ------
        ValueError
            If the intent is not in ``human_review_pending`` status.
        """
        intent = self._require_pending(execution_id)
        job_id = self._job_map[execution_id]
        self._queue.ack(job_id)
        updated = intent.model_copy(update={"status": "cancelled"})
        self._intents[execution_id] = updated
        return updated

    def reduce_quantity(
        self, execution_id: str, new_qty: int, operator: str
    ) -> ExecutionIntent:
        """Reduce the quantity of a pending intent and write an audit trail.

        Parameters
        ----------
        execution_id : str
            The ``execution_id`` of the intent to modify.
        new_qty : int
            The new quantity (**must** be less than the current quantity).
        operator : str
            Identifier of the operator making the change.

        Returns
        -------
        ExecutionIntent
            The updated intent with the reduced quantity.

        Raises
        ------
        ValueError
            If ``new_qty < 1``, ``new_qty >= current quantity``, or intent
            not in review.
        """
        intent = self._require_pending(execution_id)

        if new_qty < 1:
            raise ValueError(f"new_qty must be at least 1, got {new_qty}")

        if new_qty >= intent.quantity:
            raise ValueError(
                f"new_qty ({new_qty}) must be less than current quantity "
                f"({intent.quantity})"
            )

        original_qty = intent.quantity
        updated = intent.model_copy(update={"quantity": new_qty})
        self._intents[execution_id] = updated

        # Audit trail
        event = AuditEvent(
            event_type="manual_override",
            source="ConfirmationManager",
            data={
                "execution_id": execution_id,
                "operator": operator,
                "field": "quantity",
                "original_value": original_qty,
                "new_value": new_qty,
            },
            correlation_id=execution_id,
        )
        self._ledger.append(event)
        return updated

    def check_timeouts(self) -> list[ExecutionIntent]:
        """Scan for expired review deadlines and mark intents as ``expired_review``.

        Iterates all tracked intents that are still in
        ``human_review_pending`` status.  If the stored deadline has passed,
        the intent is transitioned to ``expired_review`` and the associated
        WorkQueue job is dead-lettered.

        Returns
        -------
        list[ExecutionIntent]
            Intents that were marked as expired during this check.
        """
        expired: list[ExecutionIntent] = []
        now = datetime.now(UTC)

        for exec_id in list(self._intents):
            intent = self._intents[exec_id]
            if intent.status != "human_review_pending":
                continue

            deadline = self._deadlines.get(exec_id)
            if not deadline:
                continue

            if now > deadline:
                updated = intent.model_copy(update={"status": "expired_review"})
                self._intents[exec_id] = updated
                job_id = self._job_map.get(exec_id)
                if job_id:
                    self._queue.dead_letter(job_id, "Review timeout expired")
                expired.append(updated)

        return expired

    def get_intent(self, execution_id: str) -> Optional[ExecutionIntent]:
        """Retrieve the tracked intent by ``execution_id``."""
        return self._intents.get(execution_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_pending(self, execution_id: str) -> ExecutionIntent:
        """Retrieve an intent and validate it is in ``human_review_pending``."""
        if execution_id not in self._intents:
            raise ValueError(f"No intent found for execution_id: {execution_id}")
        intent = self._intents[execution_id]
        if intent.status != "human_review_pending":
            raise ValueError(
                f"Intent {execution_id} is in '{intent.status}' status; "
                f"expected 'human_review_pending'"
            )
        return intent
