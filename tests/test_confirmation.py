"""Tests for ConfirmationManager — confirm/skip/reduce_quantity/timeout paths."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.executor.confirmation import ConfirmationManager
from src.executor.models import ExecutionIntent
from src.state.ledger import AuditLedger
from src.state.queue import WorkQueue

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_intent(**overrides) -> ExecutionIntent:
    defaults = dict(
        instruction_id="instr_001",
        idempotency_key="key_001",
        symbol="AAPL",
        side="BUY",
        quantity=10,
        limit_price=180.0,
        environment="uat",
        status="ready",
    )
    defaults.update(overrides)
    return ExecutionIntent(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def work_queue(tmp_path: Path) -> WorkQueue:
    return WorkQueue(tmp_path / "confirmation_queue.db")


@pytest.fixture
def ledger(tmp_path: Path) -> AuditLedger:
    return AuditLedger(tmp_path / "confirmation_ledger.jsonl")


@pytest.fixture
def manager(work_queue: WorkQueue, ledger: AuditLedger) -> ConfirmationManager:
    return ConfirmationManager(work_queue, ledger)


# ===========================================================================
# enter_review
# ===========================================================================


class TestEnterReview:
    def test_sets_status_to_human_review_pending(
        self, manager: ConfirmationManager,
    ):
        intent = _make_intent()
        manager.enter_review(intent)

        tracked = manager.get_intent(intent.execution_id)
        assert tracked is not None
        assert tracked.status == "human_review_pending"

    def test_enqueues_to_work_queue(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent = _make_intent()
        job_id = manager.enter_review(intent)

        job = work_queue.get(job_id)
        assert job is not None
        assert job.job_type == "confirmation"
        assert job.payload["execution_id"] == intent.execution_id
        assert job.payload["original_quantity"] == 10

    def test_returns_job_id(self, manager: ConfirmationManager):
        intent = _make_intent()
        job_id = manager.enter_review(intent)
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    def test_records_deadline(self, manager: ConfirmationManager):
        intent = _make_intent()
        before = datetime.now(UTC)
        manager.enter_review(intent)
        after = datetime.now(UTC)

        deadline = manager._deadlines[intent.execution_id]
        # Deadline should be ~15 min after entry
        assert before + timedelta(minutes=15) <= deadline
        assert deadline <= after + timedelta(minutes=15)

    def test_accepts_previewed_status(self, manager: ConfirmationManager):
        intent = _make_intent(status="previewed")
        job_id = manager.enter_review(intent)
        assert job_id is not None

        tracked = manager.get_intent(intent.execution_id)
        assert tracked.status == "human_review_pending"

    def test_rejects_cancelled_status(self, manager: ConfirmationManager):
        intent = _make_intent(status="cancelled")
        with pytest.raises(ValueError, match="Cannot enter review"):
            manager.enter_review(intent)

    def test_rejects_already_pending_status(self, manager: ConfirmationManager):
        intent = _make_intent()
        manager.enter_review(intent)
        tracked = manager.get_intent(intent.execution_id)
        with pytest.raises(ValueError, match="Cannot enter review"):
            manager.enter_review(tracked)

    def test_does_not_mutate_original_intent(self, manager: ConfirmationManager):
        intent = _make_intent()
        manager.enter_review(intent)
        assert intent.status == "ready"


# ===========================================================================
# confirm
# ===========================================================================


class TestConfirm:
    def test_confirm_sets_status_to_ready(self, manager: ConfirmationManager):
        intent = _make_intent()
        manager.enter_review(intent)

        result = manager.confirm(intent.execution_id)
        assert result.status == "ready"

    def test_confirm_acks_job(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent = _make_intent()
        job_id = manager.enter_review(intent)

        manager.confirm(intent.execution_id)

        job = work_queue.get(job_id)
        assert job is not None
        assert job.status == "completed"

    def test_confirm_preserves_other_fields(self, manager: ConfirmationManager):
        intent = _make_intent(quantity=25, symbol="NVDA")
        manager.enter_review(intent)

        result = manager.confirm(intent.execution_id)
        assert result.quantity == 25
        assert result.symbol == "NVDA"
        assert result.execution_id == intent.execution_id


# ===========================================================================
# skip
# ===========================================================================


class TestSkip:
    def test_skip_sets_status_to_cancelled(self, manager: ConfirmationManager):
        intent = _make_intent()
        manager.enter_review(intent)

        result = manager.skip(intent.execution_id)
        assert result.status == "cancelled"

    def test_skip_acks_job(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent = _make_intent()
        job_id = manager.enter_review(intent)

        manager.skip(intent.execution_id)

        job = work_queue.get(job_id)
        assert job is not None
        assert job.status == "completed"

    def test_skip_preserves_other_fields(self, manager: ConfirmationManager):
        intent = _make_intent(side="SELL")
        manager.enter_review(intent)

        result = manager.skip(intent.execution_id)
        assert result.side == "SELL"
        assert result.execution_id == intent.execution_id


# ===========================================================================
# reduce_quantity
# ===========================================================================


class TestReduceQuantity:
    def test_reduce_updates_quantity(self, manager: ConfirmationManager):
        intent = _make_intent(quantity=10)
        manager.enter_review(intent)

        result = manager.reduce_quantity(intent.execution_id, 5, "operator-1")
        assert result.quantity == 5

    def test_reduce_writes_audit_trail(
        self, manager: ConfirmationManager, ledger: AuditLedger,
    ):
        intent = _make_intent(quantity=10)
        manager.enter_review(intent)
        manager.reduce_quantity(intent.execution_id, 5, "operator-1")

        events = ledger.query(event_type="manual_override")
        assert len(events) == 1
        e = events[0]
        assert e.data["field"] == "quantity"
        assert e.data["original_value"] == 10
        assert e.data["new_value"] == 5
        assert e.data["operator"] == "operator-1"
        assert e.correlation_id == intent.execution_id
        assert e.source == "ConfirmationManager"

    def test_reduce_rejects_increase(self, manager: ConfirmationManager):
        intent = _make_intent(quantity=10)
        manager.enter_review(intent)

        with pytest.raises(ValueError, match="must be less than"):
            manager.reduce_quantity(intent.execution_id, 15, "operator-1")

    def test_reduce_rejects_equal_quantity(self, manager: ConfirmationManager):
        intent = _make_intent(quantity=10)
        manager.enter_review(intent)

        with pytest.raises(ValueError, match="must be less than"):
            manager.reduce_quantity(intent.execution_id, 10, "operator-1")

    def test_reduce_rejects_zero_quantity(self, manager: ConfirmationManager):
        """Zero is not a valid quantity — must be rejected."""
        intent = _make_intent(quantity=10)
        manager.enter_review(intent)

        with pytest.raises(ValueError, match="must be at least 1"):
            manager.reduce_quantity(intent.execution_id, 0, "operator-1")

    def test_reduce_can_be_called_multiple_times(self, manager: ConfirmationManager):
        intent = _make_intent(quantity=100)
        manager.enter_review(intent)

        manager.reduce_quantity(intent.execution_id, 50, "op-1")
        result = manager.reduce_quantity(intent.execution_id, 25, "op-2")
        assert result.quantity == 25

    def test_multiple_reduces_each_write_audit(
        self, manager: ConfirmationManager, ledger: AuditLedger,
    ):
        intent = _make_intent(quantity=100)
        manager.enter_review(intent)

        manager.reduce_quantity(intent.execution_id, 50, "op-1")
        manager.reduce_quantity(intent.execution_id, 25, "op-2")

        events = ledger.query(event_type="manual_override")
        assert len(events) == 2
        assert events[0].data["original_value"] == 100
        assert events[0].data["new_value"] == 50
        assert events[1].data["original_value"] == 50
        assert events[1].data["new_value"] == 25


# ===========================================================================
# timeout
# ===========================================================================


class TestTimeout:
    def test_timeout_sets_expired_review(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent = _make_intent()
        manager.enter_review(intent)

        # Expire the deadline by setting it to the past.
        manager._deadlines[intent.execution_id] = (
            datetime.now(UTC) - timedelta(seconds=1)
        )

        expired = manager.check_timeouts()
        assert len(expired) == 1
        assert expired[0].status == "expired_review"
        assert expired[0].execution_id == intent.execution_id

    def test_no_timeout_before_expiry(self, manager: ConfirmationManager):
        intent = _make_intent()
        manager.enter_review(intent)

        expired = manager.check_timeouts()
        assert len(expired) == 0

    def test_timeout_dead_letters_job(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent = _make_intent()
        manager.enter_review(intent)

        job_id = manager._job_map[intent.execution_id]
        manager._deadlines[intent.execution_id] = (
            datetime.now(UTC) - timedelta(seconds=1)
        )

        manager.check_timeouts()
        job = work_queue.get(job_id)
        assert job is not None
        assert job.status == "dead_lettered"

    def test_timeout_does_not_affect_confirmed(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent = _make_intent()
        manager.enter_review(intent)
        manager.confirm(intent.execution_id)

        # Expire the deadline — but intent is already confirmed
        manager._deadlines[intent.execution_id] = (
            datetime.now(UTC) - timedelta(seconds=1)
        )

        expired = manager.check_timeouts()
        assert len(expired) == 0
        tracked = manager.get_intent(intent.execution_id)
        assert tracked.status == "ready"

    def test_timeout_does_not_affect_skipped(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent = _make_intent()
        manager.enter_review(intent)
        manager.skip(intent.execution_id)

        manager._deadlines[intent.execution_id] = (
            datetime.now(UTC) - timedelta(seconds=1)
        )

        expired = manager.check_timeouts()
        assert len(expired) == 0
        tracked = manager.get_intent(intent.execution_id)
        assert tracked.status == "cancelled"

    def test_multiple_timeouts_detected(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent_a = _make_intent(
            instruction_id="instr_a", idempotency_key="key_a",
        )
        intent_b = _make_intent(
            instruction_id="instr_b", idempotency_key="key_b",
        )
        manager.enter_review(intent_a)
        manager.enter_review(intent_b)

        # Expire both deadlines
        past = datetime.now(UTC) - timedelta(seconds=1)
        manager._deadlines[intent_a.execution_id] = past
        manager._deadlines[intent_b.execution_id] = past

        expired = manager.check_timeouts()
        assert len(expired) == 2
        assert all(e.status == "expired_review" for e in expired)


# ===========================================================================
# Invalid transitions & error cases
# ===========================================================================


class TestInvalidTransitions:
    def test_confirm_rejects_wrong_status(self, manager: ConfirmationManager):
        intent = _make_intent()
        manager.enter_review(intent)
        manager.confirm(intent.execution_id)

        with pytest.raises(ValueError, match="expected 'human_review_pending'"):
            manager.confirm(intent.execution_id)

    def test_skip_rejects_wrong_status(self, manager: ConfirmationManager):
        intent = _make_intent()
        manager.enter_review(intent)
        manager.skip(intent.execution_id)

        with pytest.raises(ValueError, match="expected 'human_review_pending'"):
            manager.skip(intent.execution_id)

    def test_reduce_rejects_wrong_status(self, manager: ConfirmationManager):
        intent = _make_intent()
        manager.enter_review(intent)
        manager.skip(intent.execution_id)

        with pytest.raises(ValueError, match="expected 'human_review_pending'"):
            manager.reduce_quantity(intent.execution_id, 5, "operator-1")

    def test_unknown_execution_id_raises(self, manager: ConfirmationManager):
        with pytest.raises(ValueError, match="No intent found"):
            manager.confirm("nonexistent-id")

    def test_get_intent_returns_none_for_unknown(self, manager: ConfirmationManager):
        assert manager.get_intent("nonexistent") is None


# ===========================================================================
# Integration: confirm after reduce
# ===========================================================================


class TestConfirmAfterReduce:
    def test_confirm_preserves_reduced_quantity(
        self, manager: ConfirmationManager,
    ):
        intent = _make_intent(quantity=100)
        manager.enter_review(intent)
        manager.reduce_quantity(intent.execution_id, 50, "op-1")

        result = manager.confirm(intent.execution_id)
        assert result.status == "ready"
        assert result.quantity == 50

    def test_skip_after_reduce_does_not_place_order(
        self, manager: ConfirmationManager, work_queue: WorkQueue,
    ):
        intent = _make_intent(quantity=100)
        manager.enter_review(intent)
        manager.reduce_quantity(intent.execution_id, 50, "op-1")

        result = manager.skip(intent.execution_id)
        assert result.status == "cancelled"
        assert result.quantity == 50
