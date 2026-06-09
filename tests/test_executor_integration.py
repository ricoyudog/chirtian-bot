"""Integration tests for the executor pipeline — end-to-end flows with mock broker."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config.settings import RiskConfig, RuntimeConfig
from src.executor.confirmation import ConfirmationManager
from src.executor.exceptions import DuplicateExecutionError
from src.executor.execution_gate import ExecutionGate
from src.executor.factory import build_execution_intent
from src.executor.models import ExecutionAttempt
from src.executor.order_builder import OrderBuilder, compute_request_hash
from src.executor.webull_adapter import WebullCLIAdapter
from src.portfolio.models import SizingDecision
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent
from src.state.queue import WorkQueue

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _record_attempt_with_key(
    gate: ExecutionGate,
    attempt: ExecutionAttempt,
    idempotency_key: str,
) -> None:
    """Record an ExecutionAttempt with idempotency_key embedded for idempotency guard.

    The ExecutionGate.record_attempt doesn't include idempotency_key (it's on
    ExecutionIntent, not ExecutionAttempt).  This helper manually appends an
    AuditEvent with the key in data, matching the pattern used in
    test_order_builder.py.
    """
    event = AuditEvent(
        event_type="execution_attempt",
        source="ExecutionGate",
        data={**attempt.model_dump(), "idempotency_key": idempotency_key},
        correlation_id=attempt.execution_id,
    )
    gate._ledger.append(event)


def _make_sizing(**overrides) -> SizingDecision:
    defaults = dict(
        instruction_id="instr_001",
        symbol="AAPL",
        action="BUY",
        sizing_status="EXECUTABLE",
        basis="portfolio_equity",
        portfolio_equity_usd=50000.0,
        available_buying_power_usd=10000.0,
        estimated_price=180.0,
        lot_size=1,
        min_quantity=1,
        order_quantity=10,
        estimated_order_notional_usd=1800.0,
        unfilled_residual_usd=0.0,
        reason_codes=["BUYING_POWER_OK"],
    )
    defaults.update(overrides)
    return SizingDecision(**defaults)


def _make_config(**overrides) -> RuntimeConfig:
    defaults = dict(
        mode="uat_confirm",
        environment="uat",
        region="us",
        account_ids=["ACC001"],
        confirmation_mode="confirm",
        risk=RiskConfig(
            max_notional_usd=10000,
            max_quantity=1000,
            max_concentration_pct=25.0,
        ),
    )
    defaults.update(overrides)
    return RuntimeConfig(**defaults)


def _make_mock_broker(
    preview_response: dict | None = None,
    place_response: dict | None = None,
    status_response: dict | None = None,
) -> MagicMock:
    """Create a mock broker implementing BrokerClient Protocol."""
    broker = MagicMock(spec=WebullCLIAdapter)
    broker.preview_order.return_value = preview_response or {
        "preview_id": "prev_001",
    }
    broker.place_order.return_value = place_response or {
        "order_id": "ORD123",
        "status": "submitted",
    }
    broker.get_order_status.return_value = status_response or {
        "status": "filled",
    }
    return broker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def work_queue(tmp_path: Path) -> WorkQueue:
    return WorkQueue(tmp_path / "integration_queue.db")


@pytest.fixture
def ledger(tmp_path: Path) -> AuditLedger:
    return AuditLedger(tmp_path / "integration_ledger.jsonl")


@pytest.fixture
def config() -> RuntimeConfig:
    return _make_config()


# ===========================================================================
# 6.1 — End-to-end: SizingDecision → ExecutionIntent → OrderBuilder
#       → preview → confirm → place (mock broker)
# ===========================================================================


class TestEndToEndHappyPath:
    """Full happy-path flow from SizingDecision through broker placement."""

    def test_e2e_buy_flow(
        self, work_queue: WorkQueue, ledger: AuditLedger, config: RuntimeConfig,
    ):
        broker = _make_mock_broker()
        gate = ExecutionGate(config, ledger)
        builder = OrderBuilder()
        confirmation = ConfirmationManager(work_queue, ledger)
        account_id = "ACC001"

        # Step 1: SizingDecision → ExecutionIntent
        sizing = _make_sizing()
        intent = build_execution_intent(sizing, config)
        assert intent is not None
        assert intent.symbol == "AAPL"
        assert intent.quantity == 10

        # Step 2: ExecutionGate — environment check
        gate.check_environment()

        # Step 3: ExecutionGate — idempotency check (first run)
        gate.check_idempotency(intent.idempotency_key)

        # Step 4: OrderBuilder → order JSON
        order_json = builder.build_order_json(intent)
        assert order_json["symbol"] == "AAPL"
        assert order_json["quantity"] == 10
        assert order_json["side"] == "BUY"

        # Step 5: Compute request hash for audit
        req_hash = compute_request_hash(order_json)
        assert len(req_hash) == 64

        # Step 6: Preview order via broker
        preview = broker.preview_order(account_id, order_json)
        assert preview["preview_id"] == "prev_001"

        # Step 7: Record preview attempt
        preview_attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=1,
            operation="preview_order",
            request_hash=req_hash,
            status="success",
            response=preview,
        )
        gate.record_attempt(preview_attempt)

        # Step 8: Enter manual confirmation
        intent = intent.model_copy(update={"status": "previewed"})
        confirmation.enter_review(intent)

        # Step 9: Confirm
        confirmed = confirmation.confirm(intent.execution_id)
        assert confirmed.status == "ready"

        # Step 10: Place order via broker
        place_result = broker.place_order(account_id, order_json)
        assert place_result["order_id"] == "ORD123"

        # Step 11: Record place attempt
        place_attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=2,
            operation="place_order",
            request_hash=req_hash,
            status="success",
            broker_order_id=place_result["order_id"],
            response=place_result,
        )
        gate.record_attempt(place_attempt)

        # Step 12: Verify audit trail
        events = ledger.query(event_type="execution_attempt")
        assert len(events) == 2
        assert events[0].data["operation"] == "preview_order"
        assert events[1].data["operation"] == "place_order"
        assert events[1].data["broker_order_id"] == "ORD123"

    def test_e2e_sell_flow(
        self, work_queue: WorkQueue, ledger: AuditLedger, config: RuntimeConfig,
    ):
        broker = _make_mock_broker()
        builder = OrderBuilder()

        sizing = _make_sizing(action="SELL", symbol="NVDA", order_quantity=5)
        intent = build_execution_intent(sizing, config)
        assert intent is not None
        assert intent.side == "SELL"

        order_json = builder.build_order_json(intent)
        assert order_json["side"] == "SELL"

        # Preview → skip confirmation in auto mode
        preview = broker.preview_order("ACC001", order_json)
        assert preview["preview_id"] == "prev_001"

        place_result = broker.place_order("ACC001", order_json)
        assert place_result["order_id"] == "ORD123"


# ===========================================================================
# 6.2 — Idempotency double-place guard
# ===========================================================================


class TestIdempotencyDoublePlaceGuard:
    """Verify that a second place_order with the same idempotency_key is blocked."""

    def test_second_place_blocked(
        self, ledger: AuditLedger, config: RuntimeConfig,
    ):
        gate = ExecutionGate(config, ledger)
        builder = OrderBuilder()

        # First execution: successful place
        sizing = _make_sizing()
        intent = build_execution_intent(sizing, config)
        assert intent is not None

        order_json = builder.build_order_json(intent)
        req_hash = compute_request_hash(order_json)

        gate.check_idempotency(intent.idempotency_key)

        # Simulate recording a successful place_order attempt with idempotency key
        attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=1,
            operation="place_order",
            request_hash=req_hash,
            status="success",
            broker_order_id="ORD_FIRST",
        )
        _record_attempt_with_key(gate, attempt, intent.idempotency_key)

        # Second execution: same idempotency_key → must be blocked
        with pytest.raises(DuplicateExecutionError, match=intent.idempotency_key):
            gate.check_idempotency(intent.idempotency_key)

    def test_preview_then_place_not_blocked(
        self, ledger: AuditLedger, config: RuntimeConfig,
    ):
        """A preview_order attempt should NOT block a subsequent place_order."""
        gate = ExecutionGate(config, ledger)
        builder = OrderBuilder()

        sizing = _make_sizing()
        intent = build_execution_intent(sizing, config)
        assert intent is not None

        order_json = builder.build_order_json(intent)
        req_hash = compute_request_hash(order_json)

        # Record a preview attempt
        preview_attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=1,
            operation="preview_order",
            request_hash=req_hash,
            status="success",
        )
        gate.record_attempt(preview_attempt)

        # Place should NOT be blocked — preview doesn't count
        gate.check_idempotency(intent.idempotency_key)


# ===========================================================================
# 6.3 — ORDER_UNKNOWN integration: timeout → get_order_status → reconcile
# ===========================================================================


class TestOrderUnknownIntegration:
    """place_order timeout/unknown → only get_order_status or reconcile allowed."""

    def test_timeout_to_unknown_to_status_check(
        self, ledger: AuditLedger, config: RuntimeConfig,
    ):
        gate = ExecutionGate(config, ledger)
        builder = OrderBuilder()
        broker = _make_mock_broker()

        sizing = _make_sizing()
        intent = build_execution_intent(sizing, config)
        assert intent is not None

        order_json = builder.build_order_json(intent)
        req_hash = compute_request_hash(order_json)

        # Step 1: Simulate a timeout during place_order
        timeout_attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=1,
            operation="place_order",
            request_hash=req_hash,
            status="timeout",
        )
        gate.record_attempt(timeout_attempt)

        # Step 2: Mark intent as unknown
        intent = gate.handle_unknown(intent)
        assert intent.status == "unknown"

        # Step 3: Only allowed operation is get_order_status
        status = broker.get_order_status("ACC001", "ORD123")
        assert status["status"] == "filled"

        # Step 4: Record the status check
        status_attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=2,
            operation="get_order_status",
            request_hash=req_hash,
            status="success",
            response=status,
        )
        gate.record_attempt(status_attempt)

        # Step 5: Verify audit trail shows both attempts
        events = ledger.query(event_type="execution_attempt")
        assert len(events) == 2
        assert events[0].data["status"] == "timeout"
        assert events[0].data["operation"] == "place_order"
        assert events[1].data["operation"] == "get_order_status"
        assert events[1].data["status"] == "success"

    def test_unknown_intent_cannot_place_again(
        self, ledger: AuditLedger, config: RuntimeConfig,
    ):
        """After ORDER_UNKNOWN, a new place_order with the same idempotency_key
        should be blocked because the original may have succeeded."""
        gate = ExecutionGate(config, ledger)
        builder = OrderBuilder()

        sizing = _make_sizing()
        intent = build_execution_intent(sizing, config)
        assert intent is not None
        key = intent.idempotency_key

        order_json = builder.build_order_json(intent)
        req_hash = compute_request_hash(order_json)

        # Simulate a timeout — the attempt may or may not have succeeded
        attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=1,
            operation="place_order",
            request_hash=req_hash,
            status="timeout",
        )
        gate.record_attempt(attempt)

        # Now simulate: status check reveals the order actually went through
        status_attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=2,
            operation="get_order_status",
            request_hash=req_hash,
            status="success",
            broker_order_id="ORD_FOUND",
            response={"status": "filled"},
        )
        gate.record_attempt(status_attempt)

        # Also record as a "success" with the idempotency key
        success_attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            attempt_no=3,
            operation="place_order",
            request_hash=req_hash,
            status="success",
            broker_order_id="ORD_FOUND",
        )
        _record_attempt_with_key(gate, success_attempt, key)

        # Second place attempt must be blocked
        with pytest.raises(DuplicateExecutionError, match=key):
            gate.check_idempotency(key)


# ===========================================================================
# 6.4 — Manual confirmation timeout → EXPIRED_REVIEW
# ===========================================================================


class TestManualConfirmationTimeout:
    """15 min review timeout transitions intent to expired_review."""

    def test_confirm_then_timeout_flow(
        self, work_queue: WorkQueue, ledger: AuditLedger, config: RuntimeConfig,
    ):
        confirmation = ConfirmationManager(work_queue, ledger)
        broker = _make_mock_broker()
        builder = OrderBuilder()

        # Create intent
        sizing = _make_sizing()
        intent = build_execution_intent(sizing, config)
        assert intent is not None

        # Preview
        order_json = builder.build_order_json(intent)
        broker.preview_order("ACC001", order_json)

        # Enter review
        intent = intent.model_copy(update={"status": "previewed"})
        job_id = confirmation.enter_review(intent)

        # Simulate 15 min timeout by expiring the deadline
        confirmation._deadlines[intent.execution_id] = (
            datetime.now(UTC) - timedelta(seconds=1)
        )

        # Check timeouts
        expired = confirmation.check_timeouts()
        assert len(expired) == 1
        assert expired[0].status == "expired_review"
        assert expired[0].execution_id == intent.execution_id

        # WorkQueue job should be dead-lettered
        job = work_queue.get(job_id)
        assert job is not None
        assert job.status == "dead_lettered"

        # Cannot confirm an expired intent
        with pytest.raises(ValueError, match="expected 'human_review_pending'"):
            confirmation.confirm(intent.execution_id)

        # Cannot place order for an expired intent
        tracked = confirmation.get_intent(intent.execution_id)
        assert tracked is not None
        assert tracked.status == "expired_review"

    def test_multiple_intents_partial_timeout(
        self, work_queue: WorkQueue, ledger: AuditLedger, config: RuntimeConfig,
    ):
        """Two intents enter review, one expires, one is confirmed."""
        confirmation = ConfirmationManager(work_queue, ledger)

        intent_a = build_execution_intent(
            _make_sizing(instruction_id="instr_a", symbol="AAPL"),
            config,
        )
        intent_b = build_execution_intent(
            _make_sizing(instruction_id="instr_b", symbol="NVDA", order_quantity=5),
            config,
        )
        assert intent_a is not None
        assert intent_b is not None

        confirmation.enter_review(intent_a)
        confirmation.enter_review(intent_b)

        # Expire only intent_a
        confirmation._deadlines[intent_a.execution_id] = (
            datetime.now(UTC) - timedelta(seconds=1)
        )

        expired = confirmation.check_timeouts()
        assert len(expired) == 1
        assert expired[0].execution_id == intent_a.execution_id

        # intent_b should still be confirmable
        confirmed = confirmation.confirm(intent_b.execution_id)
        assert confirmed.status == "ready"

    def test_timeout_then_reduce_rejected(
        self, work_queue: WorkQueue, ledger: AuditLedger, config: RuntimeConfig,
    ):
        """After timeout, reduce_quantity must be rejected."""
        confirmation = ConfirmationManager(work_queue, ledger)

        intent = build_execution_intent(_make_sizing(), config)
        assert intent is not None
        confirmation.enter_review(intent)

        # Expire
        confirmation._deadlines[intent.execution_id] = (
            datetime.now(UTC) - timedelta(seconds=1)
        )
        confirmation.check_timeouts()

        with pytest.raises(ValueError, match="expected 'human_review_pending'"):
            confirmation.reduce_quantity(intent.execution_id, 5, "operator")
