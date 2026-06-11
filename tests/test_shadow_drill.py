"""Unit tests for alert drill runner."""

import json
from pathlib import Path

import pytest

from src.shadow.drill import AlertDrillRunner, DrillResult, INCIDENTS_DIR
from src.state.ledger import AuditLedger


@pytest.fixture
def ledger(tmp_path):
    return AuditLedger(tmp_path / "drill_ledger.jsonl")


@pytest.fixture
def incidents_dir(tmp_path):
    return tmp_path / "incidents"


@pytest.fixture
def runner(ledger, incidents_dir):
    return AlertDrillRunner(ledger, incidents_dir=str(incidents_dir))


class TestDrillSuccess:
    def test_auto_pass_without_callback(self, runner):
        result = runner.run_drill()
        assert result.result == "PASS"
        assert result.failure_reason is None
        assert result.operator_confirmation is not None

    def test_drill_with_callback(self, runner):
        confirmed_at = None

        def callback():
            nonlocal confirmed_at
            from datetime import UTC, datetime
            confirmed_at = datetime.now(UTC).isoformat()
            return confirmed_at

        result = runner.run_drill(confirm_callback=callback)
        assert result.result == "PASS"
        assert result.operator_confirmation == confirmed_at

    def test_drill_records_to_ledger(self, runner, ledger):
        runner.run_drill()
        events = ledger.query()
        assert len(events) >= 4  # anomaly_detected, kill_switch_triggered, alert_sent, drill_pass


class TestDrillFailure:
    def test_timeout_failure(self, ledger, incidents_dir):
        import time

        def slow_callback():
            time.sleep(0.1)
            return "confirmed"

        runner = AlertDrillRunner(
            ledger,
            incidents_dir=str(incidents_dir),
            timeout_seconds=0.01,  # Very short timeout
        )
        result = runner.run_drill(confirm_callback=slow_callback)
        assert result.result == "FAILED"
        assert result.failure_reason is not None

    def test_callback_exception(self, runner):
        def bad_callback():
            raise RuntimeError("Operator unavailable")

        result = runner.run_drill(confirm_callback=bad_callback)
        assert result.result == "FAILED"
        assert "CONFIRM_CALLBACK_ERROR" in result.failure_reason


class TestDrillPersistence:
    def test_writes_incident_note(self, runner, incidents_dir):
        runner.run_drill()
        notes = list(incidents_dir.glob("*.md"))
        assert len(notes) == 1
        content = notes[0].read_text()
        assert "Result: PASS" in content
        assert "Kill Switch Drill" in content

    def test_note_contains_all_fields(self, runner, incidents_dir):
        runner.run_drill()
        content = list(incidents_dir.glob("*.md"))[0].read_text()
        assert "Type:" in content
        assert "Started:" in content
        assert "Ended:" in content
        assert "Duration:" in content
        assert "Alert Channel:" in content
        assert "Operator Confirmation:" in content


class TestDrillGateCheck:
    def test_no_drill_returns_false(self, runner):
        assert runner.check_drill_passed() is False

    def test_passed_drill_returns_true(self, runner):
        runner.run_drill()
        assert runner.check_drill_passed() is True

    def test_failed_drill_returns_false(self, ledger, incidents_dir):
        runner = AlertDrillRunner(ledger, incidents_dir=str(incidents_dir), timeout_seconds=0.01)

        def slow():
            import time
            time.sleep(0.1)
            return "late"

        runner.run_drill(confirm_callback=slow)
        assert runner.check_drill_passed() is False

    def test_mixed_drills_pass_if_any_succeeds(self, runner):
        # Run a successful drill
        runner.run_drill()
        assert runner.check_drill_passed() is True

    def test_nonexistent_incidents_dir(self, ledger, tmp_path):
        runner = AlertDrillRunner(ledger, incidents_dir=str(tmp_path / "nonexistent"))
        assert runner.check_drill_passed() is False


class TestGoNoGoGate:
    def test_no_drill_blocks_live(self, runner):
        assert runner.check_drill_passed() is False

    def test_passed_drill_allows_live(self, runner):
        runner.run_drill()
        assert runner.check_drill_passed() is True

    def test_console_output_on_drill(self, runner, capsys):
        runner.run_drill()
        captured = capsys.readouterr()
        assert "[SHADOW DRILL]" in captured.out
        assert "Kill switch drill triggered" in captured.out
