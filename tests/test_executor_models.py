"""Tests for executor data models, BrokerClient protocol, and factory function."""

import pytest

from src.config.settings import RiskConfig, RuntimeConfig
from src.executor.broker_client import BrokerClient
from src.executor.factory import build_execution_intent
from src.executor.models import (
    ExecutionAttempt,
    ExecutionIntent,
    compute_idempotency_key,
)
from src.portfolio.models import SizingDecision


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# ExecutionIntent
# ---------------------------------------------------------------------------


class TestExecutionIntent:
    def test_valid_execution_intent(self):
        intent = ExecutionIntent(
            instruction_id="instr_001",
            idempotency_key="abc123",
            symbol="AAPL",
            side="BUY",
            quantity=10,
            limit_price=180.0,
            environment="uat",
        )
        assert intent.order_type == "LIMIT"
        assert intent.status == "ready"
        assert intent.execution_id  # auto-generated UUID

    def test_quantity_must_be_positive(self):
        with pytest.raises(Exception):
            ExecutionIntent(
                instruction_id="instr_001",
                idempotency_key="abc123",
                symbol="AAPL",
                side="BUY",
                quantity=0,
                limit_price=180.0,
                environment="uat",
            )

    def test_limit_price_must_be_positive(self):
        with pytest.raises(Exception):
            ExecutionIntent(
                instruction_id="instr_001",
                idempotency_key="abc123",
                symbol="AAPL",
                side="BUY",
                quantity=10,
                limit_price=0.0,
                environment="uat",
            )

    def test_side_must_be_buy_or_sell(self):
        intent_buy = ExecutionIntent(
            instruction_id="instr_001",
            idempotency_key="abc123",
            symbol="AAPL",
            side="BUY",
            quantity=10,
            limit_price=180.0,
            environment="uat",
        )
        assert intent_buy.side == "BUY"

        intent_sell = ExecutionIntent(
            instruction_id="instr_001",
            idempotency_key="abc123",
            symbol="AAPL",
            side="SELL",
            quantity=10,
            limit_price=180.0,
            environment="uat",
        )
        assert intent_sell.side == "SELL"

    def test_status_values(self):
        for status in [
            "ready", "previewed", "submitting", "acked", "unknown",
            "rejected", "filled", "cancelled", "human_review_pending",
            "expired_review",
        ]:
            intent = ExecutionIntent(
                instruction_id="instr_001",
                idempotency_key="abc123",
                symbol="AAPL",
                side="BUY",
                quantity=10,
                limit_price=180.0,
                environment="uat",
                status=status,
            )
            assert intent.status == status


# ---------------------------------------------------------------------------
# ExecutionAttempt
# ---------------------------------------------------------------------------


class TestExecutionAttempt:
    def test_valid_attempt(self):
        attempt = ExecutionAttempt(
            execution_id="exec_001",
            attempt_no=1,
            operation="place_order",
            request_hash="sha256:abc",
            status="success",
            response={"order_id": "ORD123"},
        )
        assert attempt.attempt_id  # auto-generated UUID
        assert attempt.broker_order_id is None
        assert attempt.timestamp  # auto-generated

    def test_attempt_no_must_be_positive(self):
        with pytest.raises(Exception):
            ExecutionAttempt(
                execution_id="exec_001",
                attempt_no=0,
                operation="place_order",
                request_hash="sha256:abc",
                status="success",
            )

    def test_all_operations(self):
        for op in ["preview_order", "place_order", "get_order_status", "cancel_order"]:
            attempt = ExecutionAttempt(
                execution_id="exec_001",
                attempt_no=1,
                operation=op,
                request_hash="sha256:abc",
                status="success",
            )
            assert attempt.operation == op

    def test_all_attempt_statuses(self):
        for s in ["success", "timeout", "error", "unknown"]:
            attempt = ExecutionAttempt(
                execution_id="exec_001",
                attempt_no=1,
                operation="place_order",
                request_hash="sha256:abc",
                status=s,
            )
            assert attempt.status == s

    def test_with_broker_order_id(self):
        attempt = ExecutionAttempt(
            execution_id="exec_001",
            attempt_no=1,
            operation="place_order",
            request_hash="sha256:abc",
            broker_order_id="ORD789",
            status="success",
            response={"status": "filled"},
        )
        assert attempt.broker_order_id == "ORD789"


# ---------------------------------------------------------------------------
# Idempotency key
# ---------------------------------------------------------------------------


class TestIdempotencyKey:
    def test_deterministic(self):
        key1 = compute_idempotency_key("instr_001", "BUY", 10)
        key2 = compute_idempotency_key("instr_001", "BUY", 10)
        assert key1 == key2

    def test_different_inputs_produce_different_keys(self):
        key_a = compute_idempotency_key("instr_001", "BUY", 10)
        key_b = compute_idempotency_key("instr_001", "SELL", 10)
        key_c = compute_idempotency_key("instr_001", "BUY", 5)
        key_d = compute_idempotency_key("instr_002", "BUY", 10)
        assert len({key_a, key_b, key_c, key_d}) == 4

    def test_key_is_sha256_hex(self):
        key = compute_idempotency_key("instr_001", "BUY", 10)
        assert len(key) == 64  # sha256 hex digest length
        assert all(c in "0123456789abcdef" for c in key)


# ---------------------------------------------------------------------------
# BrokerClient protocol (structural subtyping)
# ---------------------------------------------------------------------------


class TestBrokerClientProtocol:
    def test_structural_subtyping(self):
        """A class implementing all BrokerClient methods satisfies the Protocol."""

        class FakeBroker:
            def preview_order(self, account_id: str, order_json: dict) -> dict:
                return {"preview": True}

            def place_order(self, account_id: str, order_json: dict) -> dict:
                return {"order_id": "ORD1"}

            def get_order_status(self, account_id: str, order_id: str) -> dict:
                return {"status": "filled"}

            def cancel_order(self, account_id: str, order_id: str) -> dict:
                return {"cancelled": True}

            def get_account_list(self) -> list[dict]:
                return [{"id": "ACC1"}]

            def get_balance(self, account_id: str) -> dict:
                return {"equity": 50000}

            def get_positions(self, account_id: str) -> list[dict]:
                return [{"symbol": "AAPL", "qty": 10}]

            def get_open_orders(self, account_id: str) -> list[dict]:
                return []

        broker: BrokerClient = FakeBroker()
        assert broker.preview_order("ACC1", {}) == {"preview": True}
        assert broker.get_account_list() == [{"id": "ACC1"}]


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


class TestBuildExecutionIntent:
    def test_build_from_executable_sizing(self):
        sizing = _make_sizing()
        config = _make_config()

        intent = build_execution_intent(sizing, config)

        assert intent is not None
        assert intent.instruction_id == "instr_001"
        assert intent.symbol == "AAPL"
        assert intent.side == "BUY"
        assert intent.quantity == 10
        assert intent.order_type == "LIMIT"
        assert intent.limit_price == 180.0
        assert intent.environment == "uat"
        assert intent.status == "ready"

    def test_idempotency_key_derived_from_sizing(self):
        sizing = _make_sizing()
        config = _make_config()

        intent = build_execution_intent(sizing, config)

        assert intent is not None
        expected_key = compute_idempotency_key("instr_001", "BUY", 10)
        assert intent.idempotency_key == expected_key

    def test_skip_non_executable_status(self):
        for status in [
            "MODIFY_SIZE",
            "SKIP_TOO_SMALL",
            "SKIP_INSUFFICIENT_BUYING_POWER",
            "SKIP_LOT_SIZE",
            "SKIP_NO_POSITION",
            "SIZING_NEEDS_REVIEW",
            "SKIP_STALE_QUOTE",
        ]:
            sizing = _make_sizing(sizing_status=status)
            config = _make_config()
            assert build_execution_intent(sizing, config) is None

    def test_skip_zero_quantity(self):
        sizing = _make_sizing(order_quantity=0)
        config = _make_config()
        assert build_execution_intent(sizing, config) is None

    def test_sell_side_mapping(self):
        sizing = _make_sizing(action="SELL")
        config = _make_config()

        intent = build_execution_intent(sizing, config)

        assert intent is not None
        assert intent.side == "SELL"

    def test_environment_from_config(self):
        sizing = _make_sizing()
        config = _make_config(environment="uat")

        intent = build_execution_intent(sizing, config)

        assert intent is not None
        assert intent.environment == "uat"
