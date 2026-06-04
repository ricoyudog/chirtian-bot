"""Tests for SizingEngine — all 8 required scenarios plus edge cases."""

from datetime import UTC, datetime, timedelta

import pytest

from src.analyzer.parser_schema import ParsedInstruction
from src.config.settings import RiskConfig, SizingConfig
from src.portfolio.ledger import PortfolioLedger
from src.portfolio.models import (
    OpenOrder,
    PortfolioSnapshot,
    Position,
    Quote,
)
from src.portfolio.sizing import (
    CLAMPED_BUYING_POWER,
    CLAMPED_CONCENTRATION,
    OPEN_ORDER_CONFLICT,
    SKIP_NO_POSITION,
    SKIP_STALE_QUOTE,
    SKIP_TOO_SMALL,
    SizingEngine,
)


def _risk(**overrides) -> RiskConfig:
    defaults = dict(max_notional_usd=10000, max_quantity=1000, max_concentration_pct=10.0)
    defaults.update(overrides)
    return RiskConfig(**defaults)


def _sizing(**overrides) -> SizingConfig:
    return SizingConfig(**overrides)


def _instruction(action="BUY", symbol="NVDA", pct=1.0, qty_type="pct") -> ParsedInstruction:
    return ParsedInstruction(
        post_id="test_post",
        sequence=0,
        action=action,
        symbol=symbol,
        quantity_type=qty_type,
        quantity_pct=pct if qty_type == "pct" else None,
        confidence=0.95,
    ).compute_keys()


def _engine(risk=None, sizing=None, ledger=None) -> SizingEngine:
    return SizingEngine(
        risk_config=risk or _risk(),
        sizing_config=sizing or _sizing(),
        ledger=ledger,
    )


def _fresh_quote(symbol="NVDA", price=180.0) -> Quote:
    return Quote(symbol=symbol, price=price, timestamp=datetime.now(UTC).isoformat())


def _make_snapshot(
    equity=50000.0,
    buying_power=10000.0,
    positions=None,
    open_orders=None,
) -> PortfolioSnapshot:
    if positions is None:
        positions = [
            Position(symbol="AAPL", quantity=10, avg_cost=150.0, market_value_usd=1500.0),
            Position(symbol="NVDA", quantity=5, avg_cost=170.0, market_value_usd=850.0),
        ]
    return PortfolioSnapshot(
        account_id="TEST",
        equity_usd=equity,
        buying_power_usd=buying_power,
        positions=positions,
        open_orders=open_orders or [],
    )


# ------------------------------------------------------------------
# 4.2.1: 1% < 1 share → SKIP_TOO_SMALL
# ------------------------------------------------------------------


class TestSkipTooSmall:
    def test_one_pct_less_than_one_share(self):
        """Equity $5,000, NVDA $500, 1% = $50 < $500 → SKIP_TOO_SMALL."""
        engine = _engine()
        snap = _make_snapshot(equity=5000.0, buying_power=5000.0, positions=[])
        quote = _fresh_quote("NVDA", price=500.0)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "SKIP_TOO_SMALL"
        assert result.order_quantity == 0
        assert SKIP_TOO_SMALL in result.reason_codes


# ------------------------------------------------------------------
# 4.2.2: Buying power insufficient → clip or SKIP_INSUFFICIENT_BUYING_POWER
# ------------------------------------------------------------------


class TestBuyingPowerInsufficient:
    def test_buying_power_clips(self):
        """1% of $50k = $500, but buying power only $200 → clip."""
        engine = _engine()
        snap = _make_snapshot(equity=50000.0, buying_power=200.0, positions=[])
        quote = _fresh_quote("NVDA", price=180.0)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status in ("EXECUTABLE", "MODIFY_SIZE")
        assert CLAMPED_BUYING_POWER in result.reason_codes
        assert result.capped_notional_usd is not None
        assert result.capped_notional_usd <= 200.0

    def test_buying_power_too_small_for_one_share(self):
        """Buying power $10, NVDA $180 → can't buy any → SKIP."""
        engine = _engine()
        snap = _make_snapshot(equity=50000.0, buying_power=10.0, positions=[])
        quote = _fresh_quote("NVDA", price=180.0)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        result = engine.size(instr, snap, quote)
        assert "SKIP" in result.sizing_status
        assert result.order_quantity == 0


# ------------------------------------------------------------------
# 4.2.3: Lot size restriction → floor to lot or SKIP_LOT_SIZE
# ------------------------------------------------------------------


class TestLotSize:
    def test_lot_size_100_floors(self):
        """Can afford 60 shares but lot_size=100 → floor to 0 → SKIP."""
        engine = _engine()
        snap = _make_snapshot(equity=50000.0, buying_power=10000.0, positions=[])
        quote = _fresh_quote("NVDA", price=180.0)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        result = engine.size(instr, snap, quote, lot_size=100)
        # 1% of 50k = $500 → $500/180.9 = 2.76 shares → floor(2.76/100)*100 = 0
        assert "SKIP" in result.sizing_status or result.order_quantity == 0

    def test_lot_size_exact_fit(self):
        """Can afford 200 shares, lot_size=100 → 200 shares."""
        engine = _engine(risk=_risk(max_notional_usd=100000))
        snap = _make_snapshot(equity=50000.0, buying_power=50000.0, positions=[])
        quote = _fresh_quote("NVDA", price=20.0)
        instr = _instruction("BUY", "NVDA", pct=10.0)
        result = engine.size(instr, snap, quote, lot_size=100)
        # 10% of $50k = $5000, effective_price ~$20.1 → ~248 shares → floor to 200
        assert result.sizing_status == "EXECUTABLE"
        assert result.order_quantity % 100 == 0
        assert result.order_quantity > 0


# ------------------------------------------------------------------
# 4.2.4: Concentration cap → clip + MODIFY_SIZE
# ------------------------------------------------------------------


class TestConcentrationCap:
    def test_concentration_cap_clips(self):
        """AAPL already 8%, cap 10%, buy 5% → clipped to 2% remaining."""
        engine = _engine(risk=_risk(max_concentration_pct=10.0))
        aapl_value = 50000.0 * 0.08  # 8% = $4000
        snap = _make_snapshot(
            equity=50000.0,
            buying_power=50000.0,
            positions=[
                Position(symbol="AAPL", quantity=26, avg_cost=153.0, market_value_usd=aapl_value),
            ],
        )
        quote = _fresh_quote("AAPL", price=155.0)
        instr = _instruction("BUY", "AAPL", pct=5.0)  # 5% = $2500, but only $1000 remaining
        result = engine.size(instr, snap, quote)
        assert CLAMPED_CONCENTRATION in result.reason_codes
        assert result.sizing_status == "MODIFY_SIZE"


# ------------------------------------------------------------------
# 4.2.5: Sell more than position → clip to available
# ------------------------------------------------------------------


class TestSellMoreThanPosition:
    def test_sell_more_than_held(self):
        """Hold 10 AAPL, try to sell 200% → clip to 10."""
        engine = _engine()
        snap = _make_snapshot(
            positions=[
                Position(symbol="AAPL", quantity=10, avg_cost=150.0, market_value_usd=1500.0),
            ]
        )
        quote = _fresh_quote("AAPL", price=150.0)
        instr = _instruction("SELL", "AAPL", pct=200.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "EXECUTABLE"
        assert result.order_quantity == 10


# ------------------------------------------------------------------
# 4.2.6: Open order conflict → SIZING_NEEDS_REVIEW
# ------------------------------------------------------------------


class TestOpenOrderConflict:
    def test_open_buy_blocks_new_buy(self):
        """Existing BUY order for NVDA → new NVDA sizing → NEEDS_REVIEW."""
        engine = _engine()
        snap = _make_snapshot(
            buying_power=10000.0,
            open_orders=[OpenOrder(order_id="ord_1", symbol="NVDA", side="BUY", quantity=2)],
        )
        quote = _fresh_quote("NVDA", price=180.0)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "SIZING_NEEDS_REVIEW"
        assert OPEN_ORDER_CONFLICT in result.reason_codes


# ------------------------------------------------------------------
# 4.2.7: Stale quote → SKIP_STALE_QUOTE
# ------------------------------------------------------------------


class TestStaleQuote:
    def test_stale_quote_skips(self):
        """Quote 30 min old → SKIP_STALE_QUOTE."""
        engine = _engine()
        snap = _make_snapshot()
        stale_ts = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
        quote = Quote(symbol="NVDA", price=180.0, timestamp=stale_ts)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "SKIP_STALE_QUOTE"
        assert SKIP_STALE_QUOTE in result.reason_codes


# ------------------------------------------------------------------
# 4.2.8: Normal buy → EXECUTABLE with correct quantity and residual
# ------------------------------------------------------------------


class TestNormalBuy:
    def test_normal_buy_executable(self):
        """1% of $50k = $500, NVDA $180 → 2 shares, residual ~$140."""
        engine = _engine()
        snap = _make_snapshot(buying_power=10000.0)
        quote = _fresh_quote("NVDA", price=180.0)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "EXECUTABLE"
        assert result.order_quantity == 2
        assert result.target_notional_usd == pytest.approx(500.0)
        assert result.estimated_order_notional_usd > 0
        assert result.unfilled_residual_usd >= 0

    def test_buy_quantity_correct(self):
        """5% of $50k = $2500, AAPL $150 → 16 shares."""
        engine = _engine(risk=_risk(max_notional_usd=100000))
        snap = _make_snapshot(buying_power=50000.0, positions=[])
        quote = _fresh_quote("AAPL", price=150.0)
        instr = _instruction("BUY", "AAPL", pct=5.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "EXECUTABLE"
        assert result.order_quantity == 16  # floor(2500/150.75) = 16


# ------------------------------------------------------------------
# 4.2.9: Normal sell → EXECUTABLE with correct quantity
# ------------------------------------------------------------------


class TestNormalSell:
    def test_normal_sell_executable(self):
        """Hold 10 AAPL, sell 50% → 5 shares."""
        engine = _engine()
        snap = _make_snapshot(
            positions=[
                Position(symbol="AAPL", quantity=10, avg_cost=150.0, market_value_usd=1500.0),
            ]
        )
        quote = _fresh_quote("AAPL", price=150.0)
        instr = _instruction("SELL", "AAPL", pct=50.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "EXECUTABLE"
        assert result.order_quantity == 5

    def test_sell_100_pct(self):
        """Hold 10 AAPL, sell 100% → 10 shares."""
        engine = _engine()
        snap = _make_snapshot(
            positions=[
                Position(symbol="AAPL", quantity=10, avg_cost=150.0, market_value_usd=1500.0),
            ]
        )
        quote = _fresh_quote("AAPL", price=150.0)
        instr = _instruction("SELL", "AAPL", pct=100.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "EXECUTABLE"
        assert result.order_quantity == 10


# ------------------------------------------------------------------
# 4.2.10: Sell with quantity_type "all" → sell full position
# ------------------------------------------------------------------


class TestSellAll:
    def test_sell_all(self):
        """quantity_type=all → sell entire position."""
        engine = _engine()
        snap = _make_snapshot(
            positions=[
                Position(symbol="AAPL", quantity=10, avg_cost=150.0, market_value_usd=1500.0),
            ]
        )
        quote = _fresh_quote("AAPL", price=150.0)
        instr = _instruction("SELL", "AAPL", qty_type="all")
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "EXECUTABLE"
        assert result.order_quantity == 10


# ------------------------------------------------------------------
# 4.2.11: Multiple clamp reasons recorded simultaneously
# ------------------------------------------------------------------


class TestMultipleClampReasons:
    def test_buying_power_and_concentration_both_clamp(self):
        """Both buying power AND concentration cap trigger → both in reason_codes."""
        engine = _engine(risk=_risk(max_concentration_pct=10.0))
        aapl_value = 50000.0 * 0.098  # 9.8%
        snap = _make_snapshot(
            equity=50000.0,
            buying_power=200.0,  # Very low
            positions=[
                Position(symbol="AAPL", quantity=32, avg_cost=153.0, market_value_usd=aapl_value),
            ],
        )
        quote = _fresh_quote("AAPL", price=155.0)
        instr = _instruction("BUY", "AAPL", pct=1.0)
        result = engine.size(instr, snap, quote)
        assert CLAMPED_BUYING_POWER in result.reason_codes
        assert CLAMPED_CONCENTRATION in result.reason_codes


# ------------------------------------------------------------------
# 4.2.12: Zero position sell → SKIP_NO_POSITION
# ------------------------------------------------------------------


class TestZeroPositionSell:
    def test_sell_with_no_position(self):
        """Try to sell AAPL but no AAPL position → SKIP_NO_POSITION."""
        engine = _engine()
        snap = _make_snapshot(
            positions=[
                Position(symbol="NVDA", quantity=5, avg_cost=170.0, market_value_usd=850.0),
            ]
        )
        quote = _fresh_quote("AAPL", price=150.0)
        instr = _instruction("SELL", "AAPL", pct=50.0)
        result = engine.size(instr, snap, quote)
        assert result.sizing_status == "SKIP_NO_POSITION"
        assert SKIP_NO_POSITION in result.reason_codes
        assert result.order_quantity == 0


# ------------------------------------------------------------------
# 4.2.13: Ledger event written for each sizing decision
# ------------------------------------------------------------------


class TestLedgerWriting:
    def test_ledger_records_sizing_decision(self, tmp_path):
        """SizingEngine writes to ledger when configured."""
        ledger = PortfolioLedger(tmp_path / "test.jsonl")
        engine = _engine(ledger=ledger)
        snap = _make_snapshot(buying_power=10000.0)
        quote = _fresh_quote("NVDA", price=180.0)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        engine.size(instr, snap, quote)

        events = ledger.query(event_type="sizing_decision")
        assert len(events) == 1
        assert events[0]["data"]["symbol"] == "NVDA"
        assert events[0]["data"]["sizing_status"] == "EXECUTABLE"

    def test_skip_also_writes_ledger(self, tmp_path):
        """Even skipped decisions are recorded."""
        ledger = PortfolioLedger(tmp_path / "test.jsonl")
        engine = _engine(ledger=ledger)
        snap = _make_snapshot(equity=5000.0, buying_power=5000.0, positions=[])
        quote = _fresh_quote("NVDA", price=500.0)
        instr = _instruction("BUY", "NVDA", pct=1.0)
        engine.size(instr, snap, quote)

        events = ledger.query(event_type="sizing_decision")
        assert len(events) == 1
        assert events[0]["data"]["order_quantity"] == 0
