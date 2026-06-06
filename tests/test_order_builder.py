"""Tests for OrderBuilder and ExecutionGate."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.config.settings import RiskConfig, RuntimeConfig
from src.executor.execution_gate import ExecutionGate
from src.executor.exceptions import (
    DuplicateExecutionError,
    EnvironmentBlockedError,
)
from src.executor.models import (
    ExecutionAttempt,
    ExecutionIntent,
    compute_idempotency_key,
)
from src.executor.order_builder import OrderBuilder, OrderBuildError, compute_request_hash
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent


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
    )
    defaults.update(overrides)
    return ExecutionIntent(**defaults)


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


def _make_ledger() -> tuple[AuditLedger, Path]:
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    path = Path(tmp.name)
    ledger = AuditLedger(path)
    return ledger, path


# ===========================================================================
# OrderBuilder
# ===========================================================================


class TestOrderBuilder:
    def test_build_limit_buy_order(self):
        intent = _make_intent()
        builder = OrderBuilder()
        order = builder.build_order_json(intent)

        assert order["symbol"] == "AAPL"
        assert order["side"] == "BUY"
        assert order["order_type"] == "LIMIT"
        assert order["limit_price"] == 180.0
        assert order["quantity"] == 10
        assert order["instrument_type"] == "EQUITY"
        assert order["market"] == "US"
        assert order["time_in_force"] == "DAY"
        assert order["entrust_type"] == "QTY"
        assert order["support_trading_session"] == "CORE"
        assert order["combo_type"] == "NORMAL"

    def test_build_limit_sell_order(self):
        intent = _make_intent(side="SELL")
        builder = OrderBuilder()
        order = builder.build_order_json(intent)

        assert order["side"] == "SELL"

    def test_all_fields_present(self):
        intent = _make_intent()
        builder = OrderBuilder()
        order = builder.build_order_json(intent)

        expected_keys = {
            "symbol", "side", "order_type", "limit_price", "quantity",
            "instrument_type", "market", "time_in_force", "entrust_type",
            "support_trading_session", "combo_type",
        }
        assert set(order.keys()) == expected_keys

    def test_validation_rejects_empty_symbol(self):
        intent = _make_intent(symbol="   ")
        builder = OrderBuilder()
        with pytest.raises(OrderBuildError, match="symbol"):
            builder.build_order_json(intent)

    def test_validation_rejects_zero_quantity(self):
        # Use model_construct to bypass Pydantic field validators —
        # OrderBuilder provides defense-in-depth beyond model constraints.
        intent = ExecutionIntent.model_construct(
            instruction_id="instr_001",
            idempotency_key="key_001",
            symbol="AAPL",
            side="BUY",
            quantity=0,
            limit_price=180.0,
            environment="uat",
        )
        builder = OrderBuilder()
        with pytest.raises(OrderBuildError, match="quantity"):
            builder.build_order_json(intent)

    def test_validation_rejects_negative_quantity(self):
        intent = ExecutionIntent.model_construct(
            instruction_id="instr_001",
            idempotency_key="key_001",
            symbol="AAPL",
            side="BUY",
            quantity=-1,
            limit_price=180.0,
            environment="uat",
        )
        builder = OrderBuilder()
        with pytest.raises(OrderBuildError, match="quantity"):
            builder.build_order_json(intent)

    def test_validation_rejects_zero_price(self):
        intent = ExecutionIntent.model_construct(
            instruction_id="instr_001",
            idempotency_key="key_001",
            symbol="AAPL",
            side="BUY",
            quantity=10,
            limit_price=0,
            environment="uat",
        )
        builder = OrderBuilder()
        with pytest.raises(OrderBuildError, match="limit_price"):
            builder.build_order_json(intent)

    def test_validation_rejects_negative_price(self):
        intent = ExecutionIntent.model_construct(
            instruction_id="instr_001",
            idempotency_key="key_001",
            symbol="AAPL",
            side="BUY",
            quantity=10,
            limit_price=-1.0,
            environment="uat",
        )
        builder = OrderBuilder()
        with pytest.raises(OrderBuildError, match="limit_price"):
            builder.build_order_json(intent)


class TestComputeRequestHash:
    def test_deterministic(self):
        intent = _make_intent()
        builder = OrderBuilder()
        order = builder.build_order_json(intent)

        hash1 = compute_request_hash(order)
        hash2 = compute_request_hash(order)
        assert hash1 == hash2

    def test_different_orders_different_hashes(self):
        builder = OrderBuilder()
        order_a = builder.build_order_json(_make_intent(symbol="AAPL"))
        order_b = builder.build_order_json(_make_intent(symbol="NVDA"))

        assert compute_request_hash(order_a) != compute_request_hash(order_b)

    def test_hash_is_64_char_hex(self):
        builder = OrderBuilder()
        order = builder.build_order_json(_make_intent())
        h = compute_request_hash(order)

        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_order_independent(self):
        """Same key-value pairs in different insertion order → same hash."""
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 2, "a": 1}
        assert compute_request_hash(d1) == compute_request_hash(d2)


# ===========================================================================
# ExecutionGate
# ===========================================================================


class TestExecutionGateEnvironment:
    def test_uat_allows_execution(self):
        config = _make_config(environment="uat")
        ledger, path = _make_ledger()
        try:
            gate = ExecutionGate(config, ledger)
            gate.check_environment()  # should not raise
        finally:
            path.unlink(missing_ok=True)

    def test_prod_blocks_execution(self):
        config = _make_config(environment="prod")
        ledger, path = _make_ledger()
        try:
            gate = ExecutionGate(config, ledger)
            with pytest.raises(EnvironmentBlockedError, match="prod"):
                gate.check_environment()
        finally:
            path.unlink(missing_ok=True)


class TestExecutionGateIdempotency:
    def test_first_execution_proceeds(self):
        config = _make_config()
        ledger, path = _make_ledger()
        try:
            gate = ExecutionGate(config, ledger)
            gate.check_idempotency("key_001")  # no prior — should not raise
        finally:
            path.unlink(missing_ok=True)

    def test_duplicate_blocked(self):
        config = _make_config()
        ledger, path = _make_ledger()
        try:
            # Simulate a prior successful place_order
            prior_attempt = ExecutionAttempt(
                execution_id="exec_001",
                attempt_no=1,
                operation="place_order",
                request_hash="abc",
                status="success",
            )
            # Manually write with idempotency_key in data
            event = AuditEvent(
                event_type="execution_attempt",
                source="test",
                data={**prior_attempt.model_dump(), "idempotency_key": "key_001"},
                correlation_id="exec_001",
            )
            ledger.append(event)

            gate = ExecutionGate(config, ledger)
            with pytest.raises(DuplicateExecutionError, match="key_001"):
                gate.check_idempotency("key_001")
        finally:
            path.unlink(missing_ok=True)

    def test_failed_attempt_not_blocked(self):
        config = _make_config()
        ledger, path = _make_ledger()
        try:
            # A prior failed attempt should not block
            prior_attempt = ExecutionAttempt(
                execution_id="exec_001",
                attempt_no=1,
                operation="place_order",
                request_hash="abc",
                status="error",
            )
            event = AuditEvent(
                event_type="execution_attempt",
                source="test",
                data={**prior_attempt.model_dump(), "idempotency_key": "key_001"},
                correlation_id="exec_001",
            )
            ledger.append(event)

            gate = ExecutionGate(config, ledger)
            gate.check_idempotency("key_001")  # should not raise
        finally:
            path.unlink(missing_ok=True)

    def test_non_place_order_not_blocked(self):
        config = _make_config()
        ledger, path = _make_ledger()
        try:
            # A get_order_status attempt should not block
            prior_attempt = ExecutionAttempt(
                execution_id="exec_001",
                attempt_no=1,
                operation="get_order_status",
                request_hash="abc",
                status="success",
            )
            event = AuditEvent(
                event_type="execution_attempt",
                source="test",
                data={**prior_attempt.model_dump(), "idempotency_key": "key_001"},
                correlation_id="exec_001",
            )
            ledger.append(event)

            gate = ExecutionGate(config, ledger)
            gate.check_idempotency("key_001")  # should not raise
        finally:
            path.unlink(missing_ok=True)


class TestExecutionGateAttemptRecording:
    def test_record_attempt_writes_to_ledger(self):
        config = _make_config()
        ledger, path = _make_ledger()
        try:
            gate = ExecutionGate(config, ledger)

            attempt = ExecutionAttempt(
                execution_id="exec_001",
                attempt_no=1,
                operation="place_order",
                request_hash="sha256:abc",
                status="success",
                broker_order_id="ORD123",
                response={"status": "filled"},
            )
            gate.record_attempt(attempt)

            events = ledger.query(event_type="execution_attempt")
            assert len(events) == 1
            assert events[0].data["execution_id"] == "exec_001"
            assert events[0].data["broker_order_id"] == "ORD123"
            assert events[0].correlation_id == "exec_001"
        finally:
            path.unlink(missing_ok=True)

    def test_record_multiple_attempts(self):
        config = _make_config()
        ledger, path = _make_ledger()
        try:
            gate = ExecutionGate(config, ledger)

            for i in range(3):
                attempt = ExecutionAttempt(
                    execution_id=f"exec_{i:03d}",
                    attempt_no=i + 1,
                    operation="place_order",
                    request_hash=f"hash_{i}",
                    status="success",
                )
                gate.record_attempt(attempt)

            events = ledger.query(event_type="execution_attempt")
            assert len(events) == 3
        finally:
            path.unlink(missing_ok=True)


class TestExecutionGateUnknown:
    def test_handle_unknown_sets_status(self):
        config = _make_config()
        ledger, path = _make_ledger()
        try:
            gate = ExecutionGate(config, ledger)
            intent = _make_intent(status="submitting")

            result = gate.handle_unknown(intent)

            assert result.status == "unknown"
            assert result.execution_id == intent.execution_id
            assert result.symbol == intent.symbol
        finally:
            path.unlink(missing_ok=True)

    def test_handle_unknown_returns_copy(self):
        config = _make_config()
        ledger, path = _make_ledger()
        try:
            gate = ExecutionGate(config, ledger)
            intent = _make_intent(status="submitting")

            result = gate.handle_unknown(intent)

            # Original is not mutated
            assert intent.status == "submitting"
            assert result is not intent
        finally:
            path.unlink(missing_ok=True)
