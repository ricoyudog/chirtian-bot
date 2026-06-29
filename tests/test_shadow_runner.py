"""Integration tests for shadow observation runner and state store."""

from datetime import UTC, datetime, timedelta

import pytest

from src.config.settings import RiskConfig, RuntimeConfig
from src.shadow.metrics import MetricsCollector
from src.shadow.runner import (
    PipelineResult,
    ShadowObservationRunner,
    is_deferred_window,
    is_trading_day,
    next_trading_day,
)
from src.shadow.state import ObservationStateStore
from src.shadow.wiring import DryRunPipeline, build_shadow_stack
from src.state.ledger import AuditLedger


# A Wednesday — pinned so deferred-window (weekend) logic never makes these
# tests date-dependent / flaky.
def _wednesday():
    return datetime(2026, 6, 10, tzinfo=UTC)


@pytest.fixture
def ledger(tmp_path):
    return AuditLedger(tmp_path / "shadow_ledger.jsonl")


@pytest.fixture
def metrics(ledger):
    return MetricsCollector(ledger, source="test")


@pytest.fixture
def state_store(tmp_path):
    return ObservationStateStore(tmp_path / "shadow_state.db")


@pytest.fixture
def runner(state_store, metrics, ledger):
    return ShadowObservationRunner(state_store, metrics, ledger)


class TestObservationStateStore:
    def test_start_and_get(self, state_store):
        obs_id = state_store.start()
        state = state_store.get(obs_id)
        assert state is not None
        assert state["status"] == "active"
        assert state["signals_processed"] == 0

    def test_cannot_start_two_active(self, state_store):
        state_store.start()
        with pytest.raises(RuntimeError, match="already active"):
            state_store.start()

    def test_stop_completes(self, state_store):
        obs_id = state_store.start()
        result = state_store.stop()
        assert result["status"] == "completed"
        assert result["observation_id"] == obs_id

    def test_increment_signals(self, state_store):
        state_store.start()
        count = state_store.increment_signals()
        assert count == 1
        count = state_store.increment_signals()
        assert count == 2

    def test_get_active(self, state_store):
        obs_id = state_store.start()
        active = state_store.get_active()
        assert active is not None
        assert active["observation_id"] == obs_id

    def test_no_active_returns_none(self, state_store):
        assert state_store.get_active() is None

    def test_should_extend_false_when_under_one_week(self, state_store):
        state_store.start()
        assert state_store.should_extend() is False

    def test_persists_across_restart(self, tmp_path):
        db_path = tmp_path / "shadow_state.db"
        store1 = ObservationStateStore(db_path)
        obs_id = store1.start()

        store2 = ObservationStateStore(db_path)
        state = store2.get_active()
        assert state is not None
        assert state["observation_id"] == obs_id

    def test_auto_extend_when_past_one_week_insufficient_signals(self, state_store):
        """Scenario: 1 week passed but < 10 signals → should_extend returns True."""
        obs_id = state_store.start()
        # Manually backdate started_at by 8 days
        import sqlite3
        past = (datetime.now(UTC) - timedelta(days=8)).isoformat()
        with sqlite3.connect(state_store.db_path) as conn:
            conn.execute(
                "UPDATE observation_state SET started_at = ? WHERE observation_id = ?",
                (past, obs_id),
            )
        # Only 5 signals processed
        for _ in range(5):
            state_store.increment_signals()

        assert state_store.should_extend(min_signals=10) is True

    def test_max_duration_reached_at_four_weeks(self, state_store):
        """Scenario: 4 weeks passed → is_max_duration_reached returns True."""
        obs_id = state_store.start()
        import sqlite3
        past = (datetime.now(UTC) - timedelta(weeks=5)).isoformat()
        with sqlite3.connect(state_store.db_path) as conn:
            conn.execute(
                "UPDATE observation_state SET started_at = ? WHERE observation_id = ?",
                (past, obs_id),
            )
        assert state_store.is_max_duration_reached() is True

    def test_stop_marks_insufficient_when_past_week_low_signals(self, state_store):
        """Scenario: stop after 1 week with < 10 signals → status = insufficient_signals."""
        obs_id = state_store.start()
        import sqlite3
        past = (datetime.now(UTC) - timedelta(days=8)).isoformat()
        with sqlite3.connect(state_store.db_path) as conn:
            conn.execute(
                "UPDATE observation_state SET started_at = ? WHERE observation_id = ?",
                (past, obs_id),
            )
        for _ in range(3):
            state_store.increment_signals()

        result = state_store.stop()
        assert result["status"] == "insufficient_signals"

    def test_stop_completes_when_past_week_enough_signals(self, state_store):
        """Scenario: stop after 1 week with >= 10 signals → status = completed."""
        obs_id = state_store.start()
        import sqlite3
        past = (datetime.now(UTC) - timedelta(days=8)).isoformat()
        with sqlite3.connect(state_store.db_path) as conn:
            conn.execute(
                "UPDATE observation_state SET started_at = ? WHERE observation_id = ?",
                (past, obs_id),
            )
        for _ in range(10):
            state_store.increment_signals()

        result = state_store.stop()
        assert result["status"] == "completed"


class TestTradingDayHelpers:
    def test_weekday_is_trading_day(self):
        # 2026-06-10 is a Wednesday
        dt = datetime(2026, 6, 10)
        assert is_trading_day(dt) is True

    def test_saturday_not_trading_day(self):
        dt = datetime(2026, 6, 13)  # Saturday
        assert is_trading_day(dt) is False

    def test_sunday_not_trading_day(self):
        dt = datetime(2026, 6, 14)  # Sunday
        assert is_trading_day(dt) is False

    def test_deferred_window_weekend(self):
        dt = datetime(2026, 6, 13)  # Saturday
        assert is_deferred_window(dt) is True

    def test_next_trading_day_from_friday(self):
        # 2026-06-12 is a Friday
        friday = datetime(2026, 6, 12, tzinfo=UTC)
        next_day = next_trading_day(friday)
        assert next_day.weekday() == 0  # Monday
        assert next_day.hour == 9

    def test_next_trading_day_from_saturday(self):
        saturday = datetime(2026, 6, 13, tzinfo=UTC)
        next_day = next_trading_day(saturday)
        assert next_day.weekday() == 0  # Monday

    def test_holiday_not_trading_day(self):
        # 2026-12-25 is a Friday (Christmas)
        dt = datetime(2026, 12, 25)
        assert is_trading_day(dt) is False


class TestShadowObservationRunner:
    def test_process_signal_without_pipeline(self, state_store, metrics, ledger):
        # Pinned clock (Wednesday) so the deferred-window path can't flip this
        # to "deferred" on a weekend.
        runner = ShadowObservationRunner(
            state_store, metrics, ledger, now=_wednesday,
        )
        state_store.start()
        result = runner.process_signal("test signal", "sig-1")
        assert result.signal_id == "sig-1"
        assert result.outcome == "success"

    def test_process_signal_increments_count(self, runner, state_store):
        state_store.start()
        runner.process_signal("test", "sig-1")
        runner.process_signal("test", "sig-2")
        state = state_store.get_active()
        assert state["signals_processed"] == 2

    def test_process_signal_fails_without_active(self, runner):
        with pytest.raises(RuntimeError, match="No active observation"):
            runner.process_signal("test", "sig-1")

    def test_check_status(self, runner, state_store):
        state_store.start()
        status = runner.check_status()
        assert status["status"] == "active"
        assert status["min_duration_met"] is False
        assert status["min_signals_met"] is False

    def test_generate_summary(self, runner, state_store, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        state_store.start()
        runner.process_signal("buy AAPL", "sig-1")
        runner.process_signal("sell TSLA", "sig-2")

        content = runner.generate_summary()
        assert "Shadow Run Summary" in content
        assert "sig-1" not in content  # summary doesn't list individual signal IDs
        assert "Go/No-Go Readiness" in content

        # Verify file was written
        summary_files = list((tmp_path / "runtime/shadow_summaries").glob("*.md"))
        assert len(summary_files) == 1

    def test_deferred_signal_scheduled_for_next_trading_day(
        self, runner, state_store, metrics
    ):
        """Scenario: deferred signal includes deferred_until timestamp."""
        state_store.start()
        # Monkeypatch is_deferred_window to always return True
        import src.shadow.runner as runner_mod
        original = runner_mod.is_deferred_window
        runner_mod.is_deferred_window = lambda dt: True
        try:
            result = runner.process_signal("buy AAPL", "sig-deferred")
            assert result.outcome == "deferred"
            assert result.deferred_until is not None
            assert result.total_latency_ms == 0.0
        finally:
            runner_mod.is_deferred_window = original

    def test_check_status_shows_min_signals_met(self, runner, state_store):
        """Scenario: status reflects when min signals threshold is met."""
        state_store.start()
        for i in range(10):
            state_store.increment_signals()

        status = runner.check_status()
        assert status["min_signals_met"] is True
        assert status["min_duration_met"] is False


class TestFakePipeline:
    """Test with a fake pipeline that records stages."""

    def test_pipeline_stages_recorded(self, state_store, metrics, ledger):
        class FakePipeline:
            def run(self, text, signal_id):
                return PipelineResult(
                    signal_id=signal_id,
                    stages=[
                        {"stage": "detection", "latency_ms": 50.0, "outcome": "success"},
                        {"stage": "parse", "latency_ms": 200.0, "outcome": "success"},
                        {"stage": "broker", "latency_ms": 800.0, "outcome": "success"},
                    ],
                    total_latency_ms=1050.0,
                    outcome="success",
                )

        runner = ShadowObservationRunner(
            state_store, metrics, ledger, pipeline=FakePipeline(), now=_wednesday,
        )
        state_store.start()
        result = runner.process_signal("buy AAPL 1%", "sig-1")
        assert result.outcome == "success"

        # Verify metrics recorded
        report = metrics.generate_report()
        assert "detection" in report.stages
        assert "parse" in report.stages
        assert "broker" in report.stages


def _shadow_config() -> RuntimeConfig:
    return RuntimeConfig(
        mode="shadow",
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


class TestShadowStackSafety:
    def test_dry_run_pipeline_default_is_safe(self, tmp_path, monkeypatch):
        """Bare build_shadow_stack (no pipeline/dry_run/env) must stay dry-run.

        Safety invariant: never construct a real Webull-backed TradingPipeline
        without explicit opt-in.
        """
        monkeypatch.delenv("SHADOW_LIVE", raising=False)
        config = _shadow_config()

        with pytest.warns(UserWarning, match="dry-run mode"):
            stack = build_shadow_stack(
                config,
                ledger_path=str(tmp_path / "shadow_ledger.jsonl"),
                state_db_path=str(tmp_path / "shadow_state.db"),
                incidents_dir=str(tmp_path / "incidents"),
            )

        assert isinstance(stack["pipeline"], DryRunPipeline)
        assert stack["trading_stack"] is None
        assert stack["adapter"] is None
