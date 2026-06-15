"""Tests for TradingAgents gateway."""

import json
import os
import stat
import textwrap

import pytest

from src.analyzer.ta_gateway import TradingAgentsGateway
from src.analyzer.ta_models import TAResult


def _write_mock_script(script_path, output_dict):
    """Write a mock script that prints the given dict as JSON."""
    from pathlib import Path
    p = Path(script_path)
    output_json = json.dumps(output_dict)
    p.write_text(textwrap.dedent(f"""\
        import sys, json
        sys.stdin.read()
        print('{output_json}')
    """))
    p.chmod(p.stat().st_mode | stat.S_IEXEC)


def _write_failing_script(script_path, exit_code=1, stderr="error"):
    script_path.write_text(textwrap.dedent(f"""\
        import sys
        sys.stderr.write("{stderr}")
        sys.exit({exit_code})
    """))
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)


def _write_hanging_script(script_path):
    script_path.write_text("import time; time.sleep(9999)")
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)


@pytest.fixture
def runner(tmp_path):
    script = tmp_path / "mock_runner.py"
    return str(script), "python3"


class TestSuccessfulAnalysis:
    def test_buy_rating(self, runner):
        script, python = runner
        _write_mock_script(script, {"rating": "Buy", "final_decision": "summary", "error": None})

        gw = TradingAgentsGateway(ta_venv_python=python, runner_script=script, timeout_seconds=10)
        result = gw.analyze("NVDA", "2026-06-10")

        assert result.available is True
        assert result.rating == "Buy"
        assert result.raw_decision == "summary"
        assert result.error is None

    def test_all_valid_ratings(self, runner):
        script, python = runner
        for rating in ["Buy", "Overweight", "Hold", "Underweight", "Sell"]:
            _write_mock_script(script, {"rating": rating, "final_decision": "", "error": None})

            gw = TradingAgentsGateway(ta_venv_python=python, runner_script=script, timeout_seconds=10)
            result = gw.analyze("TEST", "2026-06-10")
            assert result.available is True
            assert result.rating == rating


class TestFailClosed:
    def test_timeout(self, tmp_path):
        script = tmp_path / "hang.py"
        _write_hanging_script(script)

        gw = TradingAgentsGateway(ta_venv_python="python3", runner_script=str(script), timeout_seconds=1)
        result = gw.analyze("NVDA", "2026-06-10")

        assert result.available is False
        assert "TIMEOUT" in result.error

    def test_nonzero_exit_code(self, tmp_path):
        script = tmp_path / "fail.py"
        _write_failing_script(script, exit_code=1, stderr="ImportError: no module")

        gw = TradingAgentsGateway(ta_venv_python="python3", runner_script=str(script), timeout_seconds=10)
        result = gw.analyze("NVDA", "2026-06-10")

        assert result.available is False
        assert "EXIT_1" in result.error

    def test_runner_script_not_found(self, tmp_path):
        gw = TradingAgentsGateway(
            ta_venv_python="python3",
            runner_script=str(tmp_path / "nonexistent.py"),
            timeout_seconds=5,
        )
        result = gw.analyze("NVDA", "2026-06-10")

        assert result.available is False
        assert "EXIT_" in result.error  # Python exits with code 2 for file not found

    def test_json_error_in_output(self, tmp_path):
        script = tmp_path / "bad_json.py"
        script.write_text("import sys; sys.stdin.read(); sys.stdout.write('not json')")
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

        gw = TradingAgentsGateway(ta_venv_python="python3", runner_script=str(script), timeout_seconds=10)
        result = gw.analyze("NVDA", "2026-06-10")

        assert result.available is False
        assert "JSON_PARSE_ERROR" in result.error

    def test_ta_internal_error(self, runner):
        script, python = runner
        _write_mock_script(script, {"rating": None, "final_decision": None, "error": "API_KEY_MISSING"})

        gw = TradingAgentsGateway(ta_venv_python=python, runner_script=script, timeout_seconds=10)
        result = gw.analyze("NVDA", "2026-06-10")

        assert result.available is False
        assert result.error == "API_KEY_MISSING"

    def test_no_rating_in_output(self, runner):
        script, python = runner
        _write_mock_script(script, {"rating": None, "final_decision": "text", "error": None})

        gw = TradingAgentsGateway(ta_venv_python=python, runner_script=script, timeout_seconds=10)
        result = gw.analyze("NVDA", "2026-06-10")

        assert result.available is False
        assert "NO_RATING_IN_OUTPUT" in result.error
