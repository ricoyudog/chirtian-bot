"""Tests for portfolio data models and ledger."""

import pytest

from src.portfolio.ledger import PortfolioLedger
from src.portfolio.models import (
    OpenOrder,
    PortfolioSnapshot,
    Position,
    Quote,
    ReconcileDifference,
    ReconcileResult,
    SizingDecision,
)

# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------


class TestPosition:
    def test_valid_long_position(self):
        pos = Position(symbol="AAPL", quantity=10, avg_cost=150.0, market_value_usd=1500.0)
        assert pos.symbol == "AAPL"
        assert pos.quantity == 10
        assert pos.side == "long"

    def test_valid_short_position(self):
        pos = Position(
            symbol="TSLA",
            quantity=5,
            avg_cost=200.0,
            market_value_usd=1000.0,
            side="short",
        )
        assert pos.side == "short"

    def test_negative_quantity_rejected(self):
        with pytest.raises(Exception):
            Position(symbol="AAPL", quantity=-1, avg_cost=150.0, market_value_usd=1500.0)

    def test_zero_quantity_allowed(self):
        pos = Position(symbol="AAPL", quantity=0, avg_cost=0, market_value_usd=0)
        assert pos.quantity == 0


# ---------------------------------------------------------------------------
# OpenOrder
# ---------------------------------------------------------------------------


class TestOpenOrder:
    def test_valid_buy_order(self):
        order = OpenOrder(order_id="ord_1", symbol="NVDA", side="BUY", quantity=2)
        assert order.side == "BUY"
        assert order.order_type == "MARKET"

    def test_limit_order(self):
        order = OpenOrder(
            order_id="ord_2",
            symbol="AAPL",
            side="SELL",
            quantity=5,
            order_type="LIMIT",
            limit_price=180.0,
        )
        assert order.limit_price == 180.0

    def test_zero_quantity_rejected(self):
        with pytest.raises(Exception):
            OpenOrder(order_id="ord_3", symbol="AAPL", side="BUY", quantity=0)


# ---------------------------------------------------------------------------
# Quote
# ---------------------------------------------------------------------------


class TestQuote:
    def test_valid_quote(self):
        q = Quote(symbol="NVDA", price=180.0, ask=180.5, bid=179.5)
        assert q.price == 180.0
        assert q.timestamp  # auto-generated

    def test_zero_price_rejected(self):
        with pytest.raises(Exception):
            Quote(symbol="NVDA", price=0)


# ---------------------------------------------------------------------------
# PortfolioSnapshot
# ---------------------------------------------------------------------------


class TestPortfolioSnapshot:
    def _make_snapshot(self, **overrides) -> PortfolioSnapshot:
        defaults = dict(
            account_id="test_account",
            equity_usd=50000.0,
            buying_power_usd=10000.0,
            positions=[
                Position(
                    symbol="AAPL",
                    quantity=10,
                    avg_cost=150.0,
                    market_value_usd=1500.0,
                ),
                Position(
                    symbol="NVDA",
                    quantity=5,
                    avg_cost=170.0,
                    market_value_usd=850.0,
                ),
            ],
            open_orders=[],
        )
        defaults.update(overrides)
        return PortfolioSnapshot(**defaults)

    def test_construction(self):
        snap = self._make_snapshot()
        assert snap.account_id == "test_account"
        assert snap.equity_usd == 50000.0
        assert len(snap.positions) == 2
        assert snap.source == "fake"

    def test_get_position_found(self):
        snap = self._make_snapshot()
        pos = snap.get_position("AAPL")
        assert pos is not None
        assert pos.quantity == 10

    def test_get_position_case_insensitive(self):
        snap = self._make_snapshot()
        pos = snap.get_position("aapl")
        assert pos is not None

    def test_get_position_not_found(self):
        snap = self._make_snapshot()
        assert snap.get_position("TSLA") is None

    def test_has_open_order_true(self):
        snap = self._make_snapshot(
            open_orders=[OpenOrder(order_id="ord_1", symbol="AAPL", side="BUY", quantity=2)]
        )
        assert snap.has_open_order("AAPL") is True

    def test_has_open_order_false(self):
        snap = self._make_snapshot()
        assert snap.has_open_order("AAPL") is False

    def test_has_open_order_case_insensitive(self):
        snap = self._make_snapshot(
            open_orders=[OpenOrder(order_id="ord_1", symbol="AAPL", side="BUY", quantity=2)]
        )
        assert snap.has_open_order("aapl") is True

    def test_negative_equity_rejected(self):
        with pytest.raises(Exception):
            self._make_snapshot(equity_usd=-1)


# ---------------------------------------------------------------------------
# SizingDecision
# ---------------------------------------------------------------------------


class TestSizingDecision:
    def test_executable_decision(self):
        d = SizingDecision(
            instruction_id="instr:test:0",
            symbol="NVDA",
            action="BUY",
            sizing_status="EXECUTABLE",
            portfolio_equity_usd=50000.0,
            available_buying_power_usd=10000.0,
            target_pct=1.0,
            target_notional_usd=500.0,
            capped_notional_usd=500.0,
            estimated_price=180.0,
            order_quantity=2,
            estimated_order_notional_usd=360.0,
            unfilled_residual_usd=140.0,
            reason_codes=[],
        )
        assert d.sizing_status == "EXECUTABLE"
        assert d.order_quantity == 2

    def test_skip_decision(self):
        d = SizingDecision(
            instruction_id="instr:test:0",
            symbol="NVDA",
            action="BUY",
            sizing_status="SKIP_TOO_SMALL",
            portfolio_equity_usd=50000.0,
            available_buying_power_usd=10000.0,
            target_pct=1.0,
            target_notional_usd=500.0,
            estimated_price=500.0,
            order_quantity=0,
            estimated_order_notional_usd=0,
            unfilled_residual_usd=0,
            reason_codes=["SKIP_TOO_SMALL"],
        )
        assert d.order_quantity == 0

    def test_sell_decision(self):
        d = SizingDecision(
            instruction_id="instr:test:0",
            symbol="AAPL",
            action="SELL",
            sizing_status="EXECUTABLE",
            portfolio_equity_usd=50000.0,
            available_buying_power_usd=10000.0,
            target_pct=50.0,
            target_quantity=5.0,
            estimated_price=150.0,
            order_quantity=5,
            estimated_order_notional_usd=750.0,
            unfilled_residual_usd=0,
            reason_codes=[],
        )
        assert d.action == "SELL"
        assert d.order_quantity == 5


# ---------------------------------------------------------------------------
# ReconcileResult
# ---------------------------------------------------------------------------


class TestReconcileResult:
    def test_ok_result(self):
        r = ReconcileResult(
            reconcile_id="recon_123",
            status="ok",
        )
        assert r.status == "ok"
        assert r.differences == []
        assert r.requires_manual_clear is False

    def test_mismatch_result(self):
        diff = ReconcileDifference(
            field="position.AAPL.quantity",
            local_value=10,
            broker_value=11,
            tolerance=0,
            exceeded=True,
        )
        r = ReconcileResult(
            reconcile_id="recon_456",
            status="mismatch",
            differences=[diff],
            action_taken="blocked_all_execution",
            requires_manual_clear=True,
        )
        assert r.status == "mismatch"
        assert len(r.differences) == 1
        assert r.differences[0].exceeded is True
        assert r.requires_manual_clear is True

    def test_timestamp_auto_generated(self):
        r = ReconcileResult(reconcile_id="recon_789", status="ok")
        assert r.timestamp  # not empty


# ---------------------------------------------------------------------------
# PortfolioLedger
# ---------------------------------------------------------------------------


class TestPortfolioLedger:
    def test_append_and_query(self, tmp_path):
        ledger = PortfolioLedger(tmp_path / "test_ledger.jsonl")
        ledger.append("sizing_decision", {"symbol": "NVDA", "qty": 2})
        ledger.append("reconcile_result", {"status": "ok"})

        results = ledger.query()
        assert len(results) == 2

    def test_query_by_type(self, tmp_path):
        ledger = PortfolioLedger(tmp_path / "test_ledger.jsonl")
        ledger.append("sizing_decision", {"symbol": "NVDA"})
        ledger.append("reconcile_result", {"status": "ok"})

        sizing = ledger.query(event_type="sizing_decision")
        assert len(sizing) == 1
        assert sizing[0]["type"] == "sizing_decision"

    def test_query_by_correlation_id(self, tmp_path):
        ledger = PortfolioLedger(tmp_path / "test_ledger.jsonl")
        ledger.append("sizing_decision", {"symbol": "NVDA"}, correlation_id="corr_1")
        ledger.append("sizing_decision", {"symbol": "AAPL"}, correlation_id="corr_2")

        results = ledger.query(correlation_id="corr_1")
        assert len(results) == 1
        assert results[0]["data"]["symbol"] == "NVDA"

    def test_verify_integrity(self, tmp_path):
        ledger = PortfolioLedger(tmp_path / "test_ledger.jsonl")
        ledger.append("test", {"key": "value"})
        assert ledger.verify_integrity() is True

    def test_verify_integrity_corrupt(self, tmp_path):
        ledger = PortfolioLedger(tmp_path / "test_ledger.jsonl")
        ledger.append("test", {"key": "value"})
        # Corrupt the file
        with open(ledger.ledger_path, "a") as f:
            f.write("NOT JSON\n")
        assert ledger.verify_integrity() is False

    def test_empty_ledger_query(self, tmp_path):
        ledger = PortfolioLedger(tmp_path / "test_ledger.jsonl")
        assert ledger.query() == []

    def test_creates_parent_directory(self, tmp_path):
        ledger = PortfolioLedger(tmp_path / "deep" / "nested" / "ledger.jsonl")
        ledger.append("test", {"key": "value"})
        assert ledger.ledger_path.exists()
