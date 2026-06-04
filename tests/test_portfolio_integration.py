"""Integration tests — full pipeline: snapshot -> reconcile -> size -> verify."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from src.analyzer.parser_schema import ParsedInstruction
from src.config.settings import RiskConfig, RuntimeConfig
from src.portfolio.ledger import PortfolioLedger
from src.portfolio.models import PortfolioSnapshot, Quote
from src.portfolio.reconcile import ReconcileGate, Reconciler
from src.portfolio.sizing import SizingEngine
from src.safety.runtime_guard import ReconcileBlockedError, ReconcileStatus, RuntimeGuard

FIXTURES_DIR = Path(__file__).parent / "portfolio_fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _runtime(**overrides) -> RuntimeConfig:
    defaults = dict(
        mode="offline_replay",
        environment="uat",
        region="US",
        account_ids=["test"],
        confirmation_mode="skip",
        risk=RiskConfig(
            max_notional_usd=10000, max_quantity=1000, max_concentration_pct=10.0
        ),
    )
    defaults.update(overrides)
    return RuntimeConfig(**defaults)


def _instruction(
    action: str = "BUY",
    symbol: str = "NVDA",
    pct: float | None = 1.0,
    qty_type: str = "pct",
) -> ParsedInstruction:
    return ParsedInstruction(
        post_id="test_post",
        sequence=0,
        action=action,
        symbol=symbol,
        quantity_type=qty_type,  # type: ignore[arg-type]
        quantity_pct=pct if qty_type == "pct" else None,
        confidence=0.95,
    ).compute_keys()


def _load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return yaml.safe_load(f)


def _snapshot_from_fixture(name: str) -> PortfolioSnapshot:
    return PortfolioSnapshot(**_load_fixture(name))


def _fresh_quote(symbol: str = "NVDA", price: float = 180.0) -> Quote:
    """Create a quote with a current timestamp to avoid stale-quote rejection."""
    return Quote(symbol=symbol, price=price, timestamp=datetime.now(UTC).isoformat())


# ===========================================================================
# 6.3.1  Happy path: snapshot -> reconcile OK -> size BUY -> EXECUTABLE
# ===========================================================================


class TestHappyPathBuy:
    """6.3.1 — Full pipeline for a BUY instruction."""

    def test_reconcile_ok_then_size_buy_executable(self, tmp_path):
        """Buy 1% NVDA with permissive concentration -> EXECUTABLE, qty > 0."""
        snapshot = _snapshot_from_fixture("medium_account.yaml")
        quote = _fresh_quote("NVDA", 180.0)

        # Use permissive concentration (25%) since NVDA is already 18% of portfolio
        config = _runtime(
            risk=RiskConfig(
                max_notional_usd=50000,
                max_quantity=1000,
                max_concentration_pct=25.0,
            )
        )
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(
            guard, reconciler, ledger, reconciliations_dir=tmp_path / "reconciliations"
        )
        engine = SizingEngine(config.risk, config.portfolio, ledger=ledger)

        # -- Step 1: Reconcile (identical local & broker) --------------------
        result = gate.check_and_gate(snapshot, snapshot)

        assert result.status == "ok"
        assert result.differences == []
        assert guard.reconcile_status == ReconcileStatus.OK
        assert not guard.is_stopped

        # -- Step 2: Guard allows execution ----------------------------------
        guard.assert_reconcile_ok()  # should not raise

        # -- Step 3: Size a BUY 1% NVDA -------------------------------------
        instruction = _instruction(action="BUY", symbol="NVDA", pct=1.0)
        decision = engine.size(instruction, snapshot, quote)

        # -- Verify ----------------------------------------------------------
        assert decision.sizing_status == "EXECUTABLE"
        assert decision.order_quantity > 0
        assert decision.action == "BUY"
        assert decision.symbol == "NVDA"
        assert decision.portfolio_equity_usd == snapshot.equity_usd

        # Verify sizing math:
        # equity = 50000, pct = 1% -> target_notional = 500
        # effective_price = 180 * (1 + 0.5/100) = 180.9
        # available = 10000 * 0.98 = 9800 (no clamp)
        # concentration_remaining: NVDA 9000/50000 = 18%, limit 25% -> 7% left
        #   = 7/100 * 50000 = 3500 (no clamp, 500 < 3500)
        # max_notional = 50000 (no clamp, 500 < 50000)
        # order_quantity = floor(500 / 180.9) = 2
        assert decision.order_quantity == 2
        assert decision.target_notional_usd == pytest.approx(500.0)

    def test_buy_into_symbol_within_concentration(self, tmp_path):
        """Buy 1% TSLA (5% exposure, 10% limit) -> EXECUTABLE, qty=1."""
        snapshot = _snapshot_from_fixture("medium_account.yaml")
        quote = _fresh_quote("TSLA", 250.0)

        config = _runtime()
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(guard, reconciler, ledger)

        engine = SizingEngine(config.risk, config.portfolio, ledger=ledger)

        # Reconcile OK
        gate.check_and_gate(snapshot, snapshot)

        # Size BUY 1% TSLA — TSLA exposure is 2500/50000 = 5%, limit 10% -> ok
        instruction = _instruction(action="BUY", symbol="TSLA", pct=1.0)
        decision = engine.size(instruction, snapshot, quote)

        # target_notional = 1% * 50000 = 500
        # effective_price = 250 * 1.005 = 251.25
        # concentration_remaining = 5% -> 2500 notional (500 < 2500, no clamp)
        # available = 9800 (500 < 9800, no clamp)
        # max_notional = 10000 (500 < 10000, no clamp)
        # order_quantity = floor(500 / 251.25) = 1
        assert decision.sizing_status == "EXECUTABLE"
        assert decision.order_quantity == 1


# ===========================================================================
# 6.3.2  Happy path: snapshot -> reconcile OK -> size SELL -> EXECUTABLE
# ===========================================================================


class TestHappyPathSell:
    """6.3.2 — Full pipeline for a SELL instruction."""

    def test_reconcile_ok_then_size_sell_executable(self, tmp_path):
        """Sell 50% NVDA -> EXECUTABLE, quantity = floor(50 * 0.5) = 25."""
        snapshot = _snapshot_from_fixture("medium_account.yaml")
        quote = _fresh_quote("NVDA", 180.0)

        config = _runtime()
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(guard, reconciler, ledger)

        engine = SizingEngine(config.risk, config.portfolio, ledger=ledger)

        # Reconcile OK
        result = gate.check_and_gate(snapshot, snapshot)
        assert result.status == "ok"
        assert guard.reconcile_status == ReconcileStatus.OK

        # Size SELL 50% NVDA — snapshot has qty=50 NVDA
        instruction = _instruction(action="SELL", symbol="NVDA", pct=50.0)
        decision = engine.size(instruction, snapshot, quote)

        # Verify: 50% of 50 shares = 25, floor(25/1)*1 = 25
        assert decision.sizing_status == "EXECUTABLE"
        assert decision.order_quantity == 25
        assert decision.action == "SELL"
        assert decision.symbol == "NVDA"
        assert decision.portfolio_equity_usd == snapshot.equity_usd

    def test_sell_all_shares(self, tmp_path):
        """Sell ALL NVDA shares -> EXECUTABLE, quantity = 50."""
        snapshot = _snapshot_from_fixture("medium_account.yaml")
        quote = _fresh_quote("NVDA", 180.0)

        config = _runtime()
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(guard, reconciler, ledger)

        engine = SizingEngine(config.risk, config.portfolio, ledger=ledger)

        # Reconcile OK
        gate.check_and_gate(snapshot, snapshot)

        # Sell ALL NVDA — quantity_type="all" -> target = full position quantity
        instruction = _instruction(action="SELL", symbol="NVDA", qty_type="all")
        decision = engine.size(instruction, snapshot, quote)

        assert decision.sizing_status == "EXECUTABLE"
        assert decision.order_quantity == 50  # all 50 shares


# ===========================================================================
# 6.3.3  Reconcile mismatch -> sizing blocked -> manual clear -> sizing works
# ===========================================================================


class TestReconcileMismatchRecovery:
    """6.3.3 — Mismatch blocks execution, manual clear + re-reconcile unblocks."""

    def test_mismatch_blocks_then_clear_then_sizing(self, tmp_path):
        """Full mismatch recovery cycle: mismatch -> blocked -> clear -> OK -> size."""
        snapshot = _snapshot_from_fixture("medium_account.yaml")
        quote = _fresh_quote("NVDA", 180.0)

        config = _runtime(
            risk=RiskConfig(
                max_notional_usd=50000,
                max_quantity=1000,
                max_concentration_pct=25.0,
            )
        )
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(guard, reconciler, ledger)

        engine = SizingEngine(config.risk, config.portfolio, ledger=ledger)

        # -- Step 1: Reconcile with MISMATCH (different buying power) --------
        broker_snapshot = snapshot.model_copy(
            update={"buying_power_usd": snapshot.buying_power_usd + 500.0}
        )
        result = gate.check_and_gate(snapshot, broker_snapshot)

        assert result.status == "mismatch"
        assert len(result.differences) > 0
        assert guard.reconcile_status == ReconcileStatus.MISMATCH
        assert guard.is_stopped

        # -- Step 2: Sizing should be blocked --------------------------------
        with pytest.raises(ReconcileBlockedError):
            guard.assert_reconcile_ok()

        # -- Step 3: Manual clear (operator intervention) --------------------
        gate.manual_clear()
        assert guard.reconcile_status == ReconcileStatus.UNKNOWN

        # Still blocked after clear — needs a successful reconcile
        with pytest.raises(ReconcileBlockedError):
            guard.assert_reconcile_ok()

        # -- Step 4: Re-reconcile with MATCHING snapshots --------------------
        result = gate.check_and_gate(snapshot, snapshot)
        assert result.status == "ok"
        assert guard.reconcile_status == ReconcileStatus.OK
        assert not guard.is_stopped

        # -- Step 5: Guard now allows execution ------------------------------
        guard.assert_reconcile_ok()  # should not raise

        # -- Step 6: Size BUY 1% NVDA -> EXECUTABLE -------------------------
        instruction = _instruction(action="BUY", symbol="NVDA", pct=1.0)
        decision = engine.size(instruction, snapshot, quote)

        assert decision.sizing_status == "EXECUTABLE"
        assert decision.order_quantity > 0

    def test_mismatch_writes_diff_report(self, tmp_path):
        """Mismatch produces a diff report file in reconciliations_dir."""
        recon_dir = tmp_path / "reconciliations"
        snapshot = _snapshot_from_fixture("medium_account.yaml")

        config = _runtime()
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(guard, reconciler, ledger, reconciliations_dir=recon_dir)

        # Trigger mismatch
        broker_snapshot = snapshot.model_copy(
            update={"buying_power_usd": snapshot.buying_power_usd + 500.0}
        )
        result = gate.check_and_gate(snapshot, broker_snapshot)

        assert result.status == "mismatch"
        report_path = recon_dir / f"{result.reconcile_id}.json"
        assert report_path.exists()

    def test_ledger_records_mismatch_and_clear(self, tmp_path):
        """Ledger records reconcile_mismatch and reconcile_manual_clear events."""
        snapshot = _snapshot_from_fixture("medium_account.yaml")

        config = _runtime()
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(guard, reconciler, ledger)

        # Mismatch
        broker_snapshot = snapshot.model_copy(
            update={"buying_power_usd": snapshot.buying_power_usd + 500.0}
        )
        gate.check_and_gate(snapshot, broker_snapshot)

        # Manual clear
        gate.manual_clear()

        # Verify ledger events
        mismatch_events = ledger.query(event_type="reconcile_mismatch")
        assert len(mismatch_events) == 1
        assert mismatch_events[0]["data"]["differences_count"] > 0

        clear_events = ledger.query(event_type="reconcile_manual_clear")
        assert len(clear_events) == 1
        assert clear_events[0]["data"]["cleared_by"] == "operator"

        # Reconcile OK
        gate.check_and_gate(snapshot, snapshot)
        ok_events = ledger.query(event_type="reconcile_ok")
        assert len(ok_events) == 1


# ===========================================================================
# 6.3.4  Full ledger trail for a sizing + reconcile cycle
# ===========================================================================


class TestLedgerTrail:
    """6.3.4 — Verify ledger captures the complete audit trail with correlation."""

    def test_full_cycle_ledger_events(self, tmp_path):
        """Reconcile OK + size BUY produces reconcile_ok + sizing_decision in ledger."""
        snapshot = _snapshot_from_fixture("medium_account.yaml")
        quote = _fresh_quote("NVDA", 180.0)

        config = _runtime(
            risk=RiskConfig(
                max_notional_usd=50000,
                max_quantity=1000,
                max_concentration_pct=25.0,
            )
        )
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(guard, reconciler, ledger)

        engine = SizingEngine(config.risk, config.portfolio, ledger=ledger)

        # -- Step 1: Reconcile OK -------------------------------------------
        result = gate.check_and_gate(snapshot, snapshot)
        assert result.status == "ok"

        # -- Step 2: Size BUY 1% NVDA ---------------------------------------
        instruction = _instruction(action="BUY", symbol="NVDA", pct=1.0)
        decision = engine.size(instruction, snapshot, quote)
        assert decision.sizing_status == "EXECUTABLE"

        # -- Step 3: Verify ledger events -----------------------------------
        all_events = ledger.query()
        assert len(all_events) == 2  # reconcile_ok + sizing_decision

        # Verify reconcile_ok event
        recon_events = ledger.query(event_type="reconcile_ok")
        assert len(recon_events) == 1
        recon_event = recon_events[0]
        assert "reconcile_id" in recon_event["data"]
        assert recon_event["correlation_id"] == recon_event["data"]["reconcile_id"]

        # Verify sizing_decision event
        sizing_events = ledger.query(event_type="sizing_decision")
        assert len(sizing_events) == 1
        sizing_event = sizing_events[0]
        assert sizing_event["data"]["symbol"] == "NVDA"
        assert sizing_event["data"]["action"] == "BUY"
        assert sizing_event["data"]["sizing_status"] == "EXECUTABLE"
        assert sizing_event["data"]["order_quantity"] > 0
        assert sizing_event["correlation_id"] == decision.instruction_id

        # Verify each event has a correlation_id
        for event in all_events:
            assert "correlation_id" in event
            assert event["correlation_id"] is not None

        # Verify each event has a timestamp
        for event in all_events:
            assert "ts" in event

        # Verify ledger integrity
        assert ledger.verify_integrity()

    def test_full_cycle_with_mismatch_and_recovery_ledger(self, tmp_path):
        """Full cycle: mismatch -> clear -> re-reconcile -> size -> 4 ledger events."""
        snapshot = _snapshot_from_fixture("medium_account.yaml")
        quote = _fresh_quote("NVDA", 180.0)

        config = _runtime(
            risk=RiskConfig(
                max_notional_usd=50000,
                max_quantity=1000,
                max_concentration_pct=25.0,
            )
        )
        guard = RuntimeGuard(config)
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        reconciler = Reconciler()
        gate = ReconcileGate(guard, reconciler, ledger)

        engine = SizingEngine(config.risk, config.portfolio, ledger=ledger)

        # Mismatch
        broker_snapshot = snapshot.model_copy(
            update={"buying_power_usd": snapshot.buying_power_usd + 500.0}
        )
        gate.check_and_gate(snapshot, broker_snapshot)

        # Manual clear
        gate.manual_clear()

        # Successful re-reconcile
        gate.check_and_gate(snapshot, snapshot)

        # Size
        instruction = _instruction(action="BUY", symbol="NVDA", pct=1.0)
        decision = engine.size(instruction, snapshot, quote)
        assert decision.sizing_status == "EXECUTABLE"

        # Verify complete ledger trail
        all_events = ledger.query()
        assert len(all_events) == 4  # mismatch + clear + ok + sizing

        assert len(ledger.query(event_type="reconcile_mismatch")) == 1
        assert len(ledger.query(event_type="reconcile_manual_clear")) == 1
        assert len(ledger.query(event_type="reconcile_ok")) == 1
        assert len(ledger.query(event_type="sizing_decision")) == 1

        # All events have timestamps
        for event in all_events:
            assert "ts" in event

        # Ledger integrity preserved through entire cycle
        assert ledger.verify_integrity()
