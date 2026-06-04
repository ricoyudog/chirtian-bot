"""Tests for Reconciler and ReconcileGate — all 13 required scenarios."""

from datetime import UTC, datetime

import pytest

from src.config.settings import RiskConfig, RuntimeConfig
from src.portfolio.ledger import PortfolioLedger
from src.portfolio.models import (
    OpenOrder,
    PortfolioSnapshot,
    Position,
)
from src.portfolio.reconcile import ReconcileGate, Reconciler
from src.safety.runtime_guard import ReconcileBlockedError, ReconcileStatus, RuntimeGuard

# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _runtime(**overrides) -> RuntimeConfig:
    defaults = dict(
        mode="offline_replay",
        environment="uat",
        region="US",
        account_ids=["test"],
        confirmation_mode="skip",
        risk=RiskConfig(max_notional_usd=10000, max_quantity=1000, max_concentration_pct=10.0),
    )
    defaults.update(overrides)
    return RuntimeConfig(**defaults)


def _snapshot(**overrides) -> PortfolioSnapshot:
    defaults = dict(
        account_id="test",
        equity_usd=50000.0,
        buying_power_usd=10000.0,
        positions=[],
        open_orders=[],
        snapshot_timestamp=datetime.now(UTC).isoformat(),
        source="fake",
    )
    defaults.update(overrides)
    return PortfolioSnapshot(**defaults)


def _position(symbol="AAPL", quantity=100, **kw) -> Position:
    defaults = dict(avg_cost=150.0, market_value_usd=15000.0, side="long")
    defaults.update(kw)
    return Position(symbol=symbol, quantity=quantity, **defaults)


def _order(order_id="ord_1", symbol="AAPL", side="BUY", quantity=10, **kw) -> OpenOrder:
    defaults = dict(order_type="MARKET", limit_price=None, status="pending")
    defaults.update(kw)
    return OpenOrder(order_id=order_id, symbol=symbol, side=side, quantity=quantity, **defaults)


# ---------------------------------------------------------------------------
# 1. Exact match -> status "ok", no differences
# ---------------------------------------------------------------------------


class TestExactMatch:
    def test_identical_snapshots_ok(self):
        """Identical local and broker snapshots produce status 'ok' with no differences."""
        positions = [_position("AAPL", 100), _position("MSFT", 50)]
        orders = [_order("ord_1", "AAPL")]
        local = _snapshot(
            buying_power_usd=10000.0, positions=positions, open_orders=orders,
        )
        broker = _snapshot(
            buying_power_usd=10000.0, positions=positions, open_orders=orders,
        )

        reconciler = Reconciler()
        result = reconciler.reconcile(local, broker)

        assert result.status == "ok"
        assert result.differences == []
        assert result.action_taken == "none"
        assert result.requires_manual_clear is False


# ---------------------------------------------------------------------------
# 2. Position quantity mismatch -> status "mismatch", difference recorded
# ---------------------------------------------------------------------------


class TestPositionQuantityMismatch:
    def test_quantity_mismatch_detected(self):
        """Same symbol, different quantity -> mismatch with position difference."""
        local = _snapshot(positions=[_position("AAPL", 100)])
        broker = _snapshot(positions=[_position("AAPL", 90)])

        reconciler = Reconciler()
        result = reconciler.reconcile(local, broker)

        assert result.status == "mismatch"
        qty_diffs = [d for d in result.differences if "quantity" in d.field]
        assert len(qty_diffs) == 1
        assert qty_diffs[0].local_value == 100
        assert qty_diffs[0].broker_value == 90
        assert qty_diffs[0].exceeded is True
        assert result.action_taken == "blocked_all_execution"
        assert result.requires_manual_clear is True


# ---------------------------------------------------------------------------
# 3. Buying power within tolerance -> status "ok"
# ---------------------------------------------------------------------------


class TestBuyingPowerWithinTolerance:
    def test_delta_under_one_dollar_ok(self):
        """Buying power delta < $1 -> within tolerance -> ok."""
        local = _snapshot(buying_power_usd=10000.00)
        broker = _snapshot(buying_power_usd=10000.50)

        reconciler = Reconciler()
        result = reconciler.reconcile(local, broker)

        assert result.status == "ok"

    def test_delta_exactly_at_tolerance_boundary(self):
        """Delta exactly at $1 is NOT exceeded (strict >)."""
        local = _snapshot(buying_power_usd=10000.0)
        broker = _snapshot(buying_power_usd=10001.0)

        reconciler = Reconciler()
        result = reconciler.reconcile(local, broker)

        # delta == 1.0, tolerance = max(1.0, ...) => exceeded is delta > tolerance => False
        assert result.status == "ok"


# ---------------------------------------------------------------------------
# 4. Buying power exceeds tolerance -> status "mismatch"
# ---------------------------------------------------------------------------


class TestBuyingPowerExceedsTolerance:
    def test_large_delta_mismatch(self):
        """Buying power delta well above tolerance -> mismatch."""
        local = _snapshot(buying_power_usd=10000.0)
        broker = _snapshot(buying_power_usd=8000.0)

        reconciler = Reconciler()
        result = reconciler.reconcile(local, broker)

        assert result.status == "mismatch"
        bp_diffs = [d for d in result.differences if d.field == "buying_power"]
        assert len(bp_diffs) == 1
        assert bp_diffs[0].exceeded is True


# ---------------------------------------------------------------------------
# 5. Missing position in broker -> status "mismatch"
# ---------------------------------------------------------------------------


class TestMissingPositionInBroker:
    def test_local_position_missing_from_broker(self):
        """Local has a position that broker doesn't -> mismatch."""
        local = _snapshot(positions=[_position("AAPL", 100)])
        broker = _snapshot(positions=[])

        reconciler = Reconciler()
        result = reconciler.reconcile(local, broker)

        assert result.status == "mismatch"
        exists_diffs = [d for d in result.differences if "exists" in d.field]
        assert len(exists_diffs) == 1
        assert exists_diffs[0].local_value is True
        assert exists_diffs[0].broker_value is False


# ---------------------------------------------------------------------------
# 6. Extra open order in broker -> status "mismatch"
# ---------------------------------------------------------------------------


class TestExtraOpenOrderInBroker:
    def test_broker_has_extra_order(self):
        """Broker has an order local doesn't -> mismatch."""
        local = _snapshot(open_orders=[])
        broker = _snapshot(open_orders=[_order("ord_extra", "TSLA")])

        reconciler = Reconciler()
        result = reconciler.reconcile(local, broker)

        assert result.status == "mismatch"
        extra_diffs = [d for d in result.differences if "extra_in_broker" in d.field]
        assert len(extra_diffs) == 1
        assert "ord_extra" in extra_diffs[0].broker_value


# ---------------------------------------------------------------------------
# 7. ReconcileGate activates stop on mismatch
# ---------------------------------------------------------------------------


class TestGateActivatesStop:
    def test_mismatch_activates_stop(self, tmp_path):
        """check_and_gate with mismatching snapshots -> guard.is_stopped is True."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        local = _snapshot(buying_power_usd=10000.0, positions=[_position("AAPL", 100)])
        broker = _snapshot(buying_power_usd=8000.0, positions=[_position("AAPL", 50)])

        result = gate.check_and_gate(local, broker)

        assert result.status == "mismatch"
        assert guard.is_stopped is True
        assert guard.reconcile_status == ReconcileStatus.MISMATCH
        assert guard.stopped_reason is not None


# ---------------------------------------------------------------------------
# 8. assert_reconcile_ok() raises after mismatch
# ---------------------------------------------------------------------------


class TestAssertReconcileOkRaisesAfterMismatch:
    def test_blocked_after_mismatch(self, tmp_path):
        """After gate activates stop, assert_reconcile_ok raises ReconcileBlockedError."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        local = _snapshot(buying_power_usd=10000.0)
        broker = _snapshot(buying_power_usd=5000.0)

        gate.check_and_gate(local, broker)

        with pytest.raises(ReconcileBlockedError):
            guard.assert_reconcile_ok()

        with pytest.raises(ReconcileBlockedError):
            guard.assert_mutation_allowed()


# ---------------------------------------------------------------------------
# 9. assert_reconcile_ok() passes when OK
# ---------------------------------------------------------------------------


class TestAssertReconcileOkPassesWhenOK:
    def test_no_error_after_successful_reconcile(self, tmp_path):
        """After successful reconcile, assert_reconcile_ok does not raise."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        snap = _snapshot(buying_power_usd=10000.0)
        gate.check_and_gate(snap, snap)

        guard.assert_reconcile_ok()  # should not raise
        assert guard.reconcile_status == ReconcileStatus.OK


# ---------------------------------------------------------------------------
# 10. Mismatch -> ledger event written
# ---------------------------------------------------------------------------


class TestLedgerEventOnMismatch:
    def test_reconcile_mismatch_event_in_ledger(self, tmp_path):
        """check_and_gate writes a 'reconcile_mismatch' ledger event on mismatch."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        local = _snapshot(buying_power_usd=10000.0, positions=[_position("AAPL", 100)])
        broker = _snapshot(buying_power_usd=5000.0, positions=[])

        result = gate.check_and_gate(local, broker)

        events = ledger.query(event_type="reconcile_mismatch")
        assert len(events) == 1
        assert events[0]["data"]["reconcile_id"] == result.reconcile_id
        assert events[0]["data"]["differences_count"] > 0


# ---------------------------------------------------------------------------
# 11. Mismatch -> diff report file written
# ---------------------------------------------------------------------------


class TestDiffReportWritten:
    def test_diff_report_file_exists(self, tmp_path):
        """Provide reconciliations_dir -> file written on mismatch."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        recon_dir = tmp_path / "reconciliations"
        gate = ReconcileGate(guard, reconciler, ledger, reconciliations_dir=recon_dir)

        local = _snapshot(buying_power_usd=10000.0)
        broker = _snapshot(buying_power_usd=5000.0)

        result = gate.check_and_gate(local, broker)

        expected_file = recon_dir / f"{result.reconcile_id}.json"
        assert expected_file.exists()

        import json

        report = json.loads(expected_file.read_text())
        assert report["status"] == "mismatch"
        assert len(report["differences"]) > 0

    def test_no_report_when_ok(self, tmp_path):
        """No diff report written when reconcile is ok."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        recon_dir = tmp_path / "reconciliations"
        gate = ReconcileGate(guard, reconciler, ledger, reconciliations_dir=recon_dir)

        snap = _snapshot(buying_power_usd=10000.0)
        gate.check_and_gate(snap, snap)

        assert not recon_dir.exists() or list(recon_dir.iterdir()) == []


# ---------------------------------------------------------------------------
# 12. Manual clear restores UNKNOWN status
# ---------------------------------------------------------------------------


class TestManualClearRestoresUnknown:
    def test_manual_clear_sets_unknown(self, tmp_path):
        """manual_clear sets guard to UNKNOWN (not OK), requiring a subsequent reconcile."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        # Trigger mismatch
        local = _snapshot(buying_power_usd=10000.0)
        broker = _snapshot(buying_power_usd=5000.0)
        gate.check_and_gate(local, broker)
        assert guard.reconcile_status == ReconcileStatus.MISMATCH

        # Manual clear
        gate.manual_clear()
        assert guard.reconcile_status == ReconcileStatus.UNKNOWN
        assert guard.is_stopped is True  # UNKNOWN is still stopped
        assert guard.stopped_reason is None

    def test_manual_clear_writes_ledger_event(self, tmp_path):
        """manual_clear writes a 'reconcile_manual_clear' ledger event."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        local = _snapshot(buying_power_usd=10000.0)
        broker = _snapshot(buying_power_usd=5000.0)
        gate.check_and_gate(local, broker)

        gate.manual_clear()

        events = ledger.query(event_type="reconcile_manual_clear")
        assert len(events) == 1
        assert events[0]["data"]["cleared_by"] == "operator"

    def test_after_manual_clear_then_ok_reconcile_reaches_ok(self, tmp_path):
        """After manual_clear + successful reconcile -> guard reaches OK."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        # Trigger mismatch
        local = _snapshot(buying_power_usd=10000.0)
        broker = _snapshot(buying_power_usd=5000.0)
        gate.check_and_gate(local, broker)

        # Manual clear -> UNKNOWN
        gate.manual_clear()
        assert guard.reconcile_status == ReconcileStatus.UNKNOWN

        # Successful reconcile -> OK
        snap = _snapshot(buying_power_usd=10000.0)
        gate.check_and_gate(snap, snap)
        assert guard.reconcile_status == ReconcileStatus.OK
        assert guard.is_stopped is False


# ---------------------------------------------------------------------------
# 13. Auto-recovery does NOT happen
# ---------------------------------------------------------------------------


class TestNoAutoRecovery:
    def test_subsequent_ok_does_not_clear_mismatch(self, tmp_path):
        """After mismatch, a subsequent OK reconcile does NOT auto-clear.
        Guard stays MISMATCH until manual_clear + next OK reconcile."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        # First: trigger mismatch
        local_bad = _snapshot(buying_power_usd=10000.0)
        broker_bad = _snapshot(buying_power_usd=5000.0)
        gate.check_and_gate(local_bad, broker_bad)
        assert guard.reconcile_status == ReconcileStatus.MISMATCH

        # Second: send matching snapshots (would be OK on its own)
        snap = _snapshot(buying_power_usd=10000.0)
        result = gate.check_and_gate(snap, snap)
        assert result.status == "ok"

        # Guard should STILL be in MISMATCH — mark_reconcile_ok is a no-op when MISMATCH
        assert guard.reconcile_status == ReconcileStatus.MISMATCH
        assert guard.is_stopped is True

        # assert_reconcile_ok still raises
        with pytest.raises(ReconcileBlockedError):
            guard.assert_reconcile_ok()

    def test_full_recovery_requires_manual_clear_then_ok(self, tmp_path):
        """Full recovery path: mismatch -> manual_clear -> OK reconcile -> OK."""
        guard = RuntimeGuard(_runtime())
        reconciler = Reconciler()
        ledger = PortfolioLedger(tmp_path / "ledger.jsonl")
        gate = ReconcileGate(guard, reconciler, ledger)

        # Mismatch
        gate.check_and_gate(
            _snapshot(buying_power_usd=10000.0),
            _snapshot(buying_power_usd=5000.0),
        )
        assert guard.reconcile_status == ReconcileStatus.MISMATCH

        # OK alone does NOT fix it
        snap = _snapshot(buying_power_usd=10000.0)
        gate.check_and_gate(snap, snap)
        assert guard.reconcile_status == ReconcileStatus.MISMATCH

        # Manual clear -> UNKNOWN
        gate.manual_clear()
        assert guard.reconcile_status == ReconcileStatus.UNKNOWN

        # Now OK reconcile -> OK
        gate.check_and_gate(snap, snap)
        assert guard.reconcile_status == ReconcileStatus.OK
        assert guard.is_stopped is False
        guard.assert_reconcile_ok()  # no raise
