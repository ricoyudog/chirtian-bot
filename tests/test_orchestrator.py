"""Tests for the end-to-end trading orchestrator.

Uses FakeAccountProvider + a mock broker + StubTAGateway so the full
parse→fuse→size→gate→place flow is exercised without any external dependency.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from src.config.settings import RiskConfig, RuntimeConfig
from src.executor.execution_gate import ExecutionGate
from src.executor.order_builder import OrderBuilder
from src.pipeline.orchestrator import (
    OUTCOME_BLOCKED,
    OUTCOME_NEEDS_REVIEW,
    OUTCOME_PLACED,
    OUTCOME_SKIPPED,
    TradingPipeline,
)
from src.pipeline.wiring import StubTAGateway, make_direct_instruction
from src.portfolio.ledger import PortfolioLedger
from src.portfolio.models import PortfolioSnapshot, Quote
from src.portfolio.provider import FakeAccountProvider
from src.portfolio.reconcile import ReconcileGate, Reconciler
from src.portfolio.sizing import SizingEngine
from src.safety.runtime_guard import RuntimeGuard
from src.state.ledger import AuditLedger

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _config() -> RuntimeConfig:
    return RuntimeConfig(
        mode="uat_confirm",
        environment="uat",
        region="US",
        account_ids=["TEST001"],
        confirmation_mode="auto",
        risk=RiskConfig(
            max_notional_usd=10000,
            max_quantity=1000,
            max_concentration_pct=10.0,
            symbol_whitelist=["AAPL", "TSLA"],
        ),
    )


def _fresh_quote(symbol: str = "AAPL", price: float = 150.0) -> Quote:
    return Quote(symbol=symbol, price=price, timestamp=datetime.now(UTC).isoformat())


def _build_pipeline(
    tmp_path,
    *,
    ta_rating: str = "Buy",
    ta_available: bool = True,
    ta_skip: bool = False,
    equity: float = 50000.0,
    buying_power: float = 10000.0,
    quote_symbol: str = "AAPL",
    quote_price: float = 150.0,
    require_reconcile: bool = False,
) -> tuple[TradingPipeline, MagicMock, PortfolioLedger, AuditLedger]:
    config = _config()
    audit = AuditLedger(tmp_path / "audit.jsonl")
    pledger = PortfolioLedger(tmp_path / "portfolio.jsonl")

    provider = FakeAccountProvider(
        equity_usd=equity,
        buying_power_usd=buying_power,
        quotes={quote_symbol: _fresh_quote(quote_symbol, quote_price)},
        account_id="TEST001",
    )
    guard = RuntimeGuard(config)
    sizing = SizingEngine(config.risk, config.portfolio, pledger)
    gate = ExecutionGate(config, audit)
    reconcile_gate = ReconcileGate(guard, Reconciler(), pledger)

    broker = MagicMock()
    broker.preview_order.return_value = {"status": "preview_ok"}
    broker.place_order.return_value = {"order_id": "ORD-1", "status": "submitted"}

    ta = None if ta_skip else StubTAGateway(rating=ta_rating, available=ta_available)

    pipeline = TradingPipeline(
        config=config,
        provider=provider,
        sizing_engine=sizing,
        execution_gate=gate,
        runtime_guard=guard,
        order_builder=OrderBuilder(),
        broker=broker,
        audit_ledger=audit,
        portfolio_ledger=pledger,
        ta_gateway=ta,
        reconcile_gate=reconcile_gate,
        require_reconcile=require_reconcile,
    )
    return pipeline, broker, pledger, audit


def _placed_order_json(broker: MagicMock) -> dict:
    return broker.place_order.call_args.args[1]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestApprovePlacesOrder:
    def test_places_preview_and_order(self, tmp_path):
        pipeline, broker, pledger, audit = _build_pipeline(tmp_path)
        inst = make_direct_instruction("AAPL", "BUY", 1.0)

        outcome = pipeline.process_instruction(inst, "TEST001")

        assert outcome.outcome == OUTCOME_PLACED
        assert outcome.broker_order_id == "ORD-1"
        assert outcome.order_quantity >= 1
        assert broker.preview_order.call_count == 1
        assert broker.place_order.call_count == 1

    def test_records_audit_and_portfolio_ledger(self, tmp_path):
        pipeline, broker, pledger, audit = _build_pipeline(tmp_path)
        inst = make_direct_instruction("AAPL", "BUY", 1.0)

        pipeline.process_instruction(inst, "TEST001")

        attempts = audit.query(event_type="execution_attempt")
        assert len(attempts) == 1
        assert attempts[0].data["operation"] == "place_order"
        assert attempts[0].data["status"] == "success"
        assert attempts[0].data["broker_order_id"] == "ORD-1"

        placements = pledger.query(event_type="order_placed")
        assert len(placements) == 1
        assert placements[0]["data"]["broker_order_id"] == "ORD-1"

    def test_bootstrap_sync_recorded_on_first_run(self, tmp_path):
        pipeline, _broker, pledger, audit = _build_pipeline(tmp_path)
        inst = make_direct_instruction("AAPL", "BUY", 1.0)

        pipeline.process_instruction(inst, "TEST001")

        bootstraps = audit.query(event_type="bootstrap_sync")
        assert len(bootstraps) == 1
        assert pledger.has_baseline() is True


# ---------------------------------------------------------------------------
# Fusion gating (fail-closed)
# ---------------------------------------------------------------------------


class TestFusionGating:
    def test_ta_unavailable_needs_review(self, tmp_path):
        pipeline, broker, _pledger, _audit = _build_pipeline(
            tmp_path,
            ta_available=False,
        )
        outcome = pipeline.process_instruction(
            make_direct_instruction("AAPL", "BUY", 1.0),
            "TEST001",
        )
        assert outcome.outcome == OUTCOME_NEEDS_REVIEW
        assert outcome.reason == "TA_UNAVAILABLE"
        assert broker.place_order.call_count == 0

    def test_ta_opposes_buy_needs_review(self, tmp_path):
        pipeline, broker, _pledger, _audit = _build_pipeline(
            tmp_path,
            ta_rating="Sell",
        )
        outcome = pipeline.process_instruction(
            make_direct_instruction("AAPL", "BUY", 1.0),
            "TEST001",
        )
        assert outcome.outcome == OUTCOME_NEEDS_REVIEW
        assert outcome.reason == "TA_OPPOSES_BUY"
        assert broker.place_order.call_count == 0

    def test_modify_halves_order_quantity(self, tmp_path):
        # Neutral TA on a BUY → MODIFY → quantity_pct halved before sizing.
        mod_pipe, mod_broker, _, _ = _build_pipeline(
            tmp_path,
            ta_rating="Hold",
            quote_price=150.0,
        )
        app_pipe, app_broker, _, _ = _build_pipeline(
            tmp_path,
            ta_rating="Buy",
            quote_price=150.0,
        )

        mod_pipe.process_instruction(make_direct_instruction("AAPL", "BUY", 2.0), "TEST001")
        app_pipe.process_instruction(make_direct_instruction("AAPL", "BUY", 2.0), "TEST001")

        mod_qty = _placed_order_json(mod_broker)["quantity"]
        app_qty = _placed_order_json(app_broker)["quantity"]
        assert mod_qty > 0
        assert mod_qty < app_qty  # halved by fusion MODIFY factor


# ---------------------------------------------------------------------------
# Sizing skip
# ---------------------------------------------------------------------------


class TestSizingSkip:
    def test_insufficient_buying_power_skips(self, tmp_path):
        pipeline, broker, _, _ = _build_pipeline(
            tmp_path,
            buying_power=10.0,
        )
        outcome = pipeline.process_instruction(
            make_direct_instruction("AAPL", "BUY", 1.0),
            "TEST001",
        )
        assert outcome.outcome == OUTCOME_SKIPPED
        assert outcome.reason.startswith("SIZING_SKIP")
        assert broker.place_order.call_count == 0


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_duplicate_execution_blocked(self, tmp_path):
        pipeline, broker, _, _ = _build_pipeline(tmp_path)
        inst = make_direct_instruction("AAPL", "BUY", 1.0)

        first = pipeline.process_instruction(inst, "TEST001")
        second = pipeline.process_instruction(inst, "TEST001")

        assert first.outcome == OUTCOME_PLACED
        assert second.outcome == OUTCOME_BLOCKED
        assert second.reason == "DUPLICATE_EXECUTION"
        assert broker.place_order.call_count == 1  # no second place


# ---------------------------------------------------------------------------
# Reconcile
# ---------------------------------------------------------------------------


class TestReconcile:
    def test_bootstrap_unblocks_first_order(self, tmp_path):
        # require_reconcile=True but no prior baseline → bootstrap → places.
        pipeline, broker, _, _ = _build_pipeline(
            tmp_path,
            require_reconcile=True,
        )
        outcome = pipeline.process_instruction(
            make_direct_instruction("AAPL", "BUY", 1.0),
            "TEST001",
        )
        assert outcome.outcome == OUTCOME_PLACED
        assert broker.place_order.call_count == 1

    def test_mismatch_blocks_execution(self, tmp_path):
        pipeline, broker, pledger, _ = _build_pipeline(
            tmp_path,
            require_reconcile=True,
        )
        # Seed a baseline that diverges from the live snapshot.
        bogus = PortfolioSnapshot(
            account_id="TEST001",
            equity_usd=50000.0,
            buying_power_usd=99999.0,  # differs from provider's 10000
            positions=[],
            open_orders=[],
        )
        pledger.record_baseline(bogus)

        outcome = pipeline.process_instruction(
            make_direct_instruction("AAPL", "BUY", 1.0),
            "TEST001",
        )
        assert outcome.outcome == OUTCOME_BLOCKED
        assert outcome.reason == "RECONCILE_MISMATCH"
        assert broker.place_order.call_count == 0


# ---------------------------------------------------------------------------
# Scope guards
# ---------------------------------------------------------------------------


class TestScopeGuards:
    def test_non_whitelisted_symbol_needs_review(self, tmp_path):
        pipeline, broker, _, _ = _build_pipeline(tmp_path)
        outcome = pipeline.process_instruction(
            make_direct_instruction("MSFT", "BUY", 1.0),
            "TEST001",
        )
        assert outcome.outcome == OUTCOME_NEEDS_REVIEW
        assert outcome.reason == "SYMBOL_NOT_WHITELISTED"
        assert broker.place_order.call_count == 0


# ---------------------------------------------------------------------------
# Place failure (e.g. broker rejects: non-trading day, insufficient funds)
# ---------------------------------------------------------------------------


class TestPlaceFailure:
    def test_broker_reject_returns_blocked(self, tmp_path):
        from src.executor.exceptions import BrokerError

        pipeline, broker, _, _ = _build_pipeline(tmp_path)
        # Preview succeeds, place is rejected by the broker.
        broker.place_order.side_effect = BrokerError(
            "OAUTH_OPENAPI_NO_TRADING_DAY: Non-trading day."
        )

        outcome = pipeline.process_instruction(
            make_direct_instruction("AAPL", "BUY", 1.0),
            "TEST001",
        )

        assert outcome.outcome == OUTCOME_BLOCKED
        assert outcome.reason == "PLACE_FAILED"
        assert outcome.sizing_status == "EXECUTABLE"
        assert outcome.order_quantity >= 1  # sizing produced a real qty
        assert "Non-trading day" in outcome.error

