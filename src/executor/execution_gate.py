"""ExecutionGate — safety checks before and during broker interactions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from dataclasses import asdict

from src.config.settings import RuntimeConfig
from src.executor.exceptions import DuplicateExecutionError, EnvironmentBlockedError
from src.executor.models import ExecutionAttempt, ExecutionIntent
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent


class ExecutionGate:
    """Enforces pre-flight and in-flight safety checks for broker operations.

    Parameters
    ----------
    config : RuntimeConfig
        Active runtime configuration (used for environment checks).
    ledger : AuditLedger
        Append-only audit ledger for recording attempts and querying history.
    """

    def __init__(self, config: RuntimeConfig, ledger: AuditLedger) -> None:
        self._config = config
        self._ledger = ledger

    # ------------------------------------------------------------------
    # Environment guard
    # ------------------------------------------------------------------

    def check_environment(self) -> None:
        """Raise EnvironmentBlockedError if environment is not ``uat``.

        Raises
        ------
        EnvironmentBlockedError
            When the runtime environment is anything other than ``uat``.
        """
        if self._config.environment != "uat":
            raise EnvironmentBlockedError(
                f"Execution blocked: environment is '{self._config.environment}', "
                f"expected 'uat'",
            )

    # ------------------------------------------------------------------
    # Idempotency guard
    # ------------------------------------------------------------------

    def check_idempotency(self, idempotency_key: str) -> None:
        """Check whether a successful execution with the same key already exists.

        Queries the audit ledger for ``execution_attempt`` events whose
        ``idempotency_key`` matches and whose ``operation`` is
        ``place_order``.  If a matching event with ``status == "success"``
        is found, a DuplicateExecutionError is raised.

        Parameters
        ----------
        idempotency_key : str
            The idempotency key to check for prior successful execution.

        Raises
        ------
        DuplicateExecutionError
            When a prior successful ``place_order`` attempt is found for
            the given key.
        """
        prior_events = self._ledger.query(event_type="execution_attempt")
        for event in prior_events:
            data = event.data
            if (
                data.get("idempotency_key") == idempotency_key
                and data.get("operation") == "place_order"
                and data.get("status") == "success"
            ):
                raise DuplicateExecutionError(
                    f"Duplicate execution blocked: a successful place_order "
                    f"attempt already exists for idempotency_key "
                    f"'{idempotency_key}'",
                )

    # ------------------------------------------------------------------
    # Attempt recording
    # ------------------------------------------------------------------

    def record_attempt(self, attempt: ExecutionAttempt) -> None:
        """Write an ExecutionAttempt to the audit ledger.

        Parameters
        ----------
        attempt : ExecutionAttempt
            The attempt record to persist.
        """
        event = AuditEvent(
            event_type="execution_attempt",
            source="ExecutionGate",
            data=attempt.model_dump(),
            correlation_id=attempt.execution_id,
        )
        self._ledger.append(event)

    # ------------------------------------------------------------------
    # Unknown status handler
    # ------------------------------------------------------------------

    def handle_unknown(self, intent: ExecutionIntent) -> ExecutionIntent:
        """Mark an intent as ``unknown`` status.

        The caller must ensure that only ``get_order_status`` or reconcile
        operations follow after this method returns.

        Parameters
        ----------
        intent : ExecutionIntent
            The execution intent to update.

        Returns
        -------
        ExecutionIntent
            A copy of the intent with ``status`` set to ``"unknown"``.
        """
        return intent.model_copy(update={"status": "unknown"})
