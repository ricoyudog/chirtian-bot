"""TradingAgents gateway — subprocess wrapper for TA analysis."""

from __future__ import annotations

import json
import subprocess

from src.analyzer.ta_models import TAResult

DEFAULT_TA_VENV = "/Users/chunsingyu/softwares/TradingAgents/.venv/bin/python"
DEFAULT_RUNNER_SCRIPT = "/Users/chunsingyu/softwares/TradingAgents/scripts/run_analysis.py"
DEFAULT_TIMEOUT = 1800  # 30 minutes


class TradingAgentsGateway:
    """Run TradingAgents analysis via subprocess in its own venv."""

    def __init__(
        self,
        ta_venv_python: str = DEFAULT_TA_VENV,
        runner_script: str = DEFAULT_RUNNER_SCRIPT,
        timeout_seconds: int = DEFAULT_TIMEOUT,
        depth: str = "deep",
    ):
        self._python = ta_venv_python
        self._script = runner_script
        self._timeout = timeout_seconds
        self._depth = depth

    def analyze(self, ticker: str, trade_date: str) -> TAResult:
        """Run TA analysis for a single ticker.

        Returns TAResult with available=False on any failure (fail-closed).
        """
        payload = json.dumps({
            "ticker": ticker,
            "date": trade_date,
            "depth": self._depth,
        })

        try:
            proc = subprocess.run(
                [self._python, self._script],
                input=payload,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired:
            return TAResult(
                ticker=ticker,
                available=False,
                error=f"TIMEOUT after {self._timeout}s",
            )
        except FileNotFoundError as e:
            return TAResult(
                ticker=ticker,
                available=False,
                error=f"RUNNER_NOT_FOUND: {e}",
            )

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()[:500]
            return TAResult(
                ticker=ticker,
                available=False,
                error=f"EXIT_{proc.returncode}: {stderr}",
            )

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            return TAResult(
                ticker=ticker,
                available=False,
                error=f"JSON_PARSE_ERROR: {e}",
            )

        if data.get("error"):
            return TAResult(
                ticker=ticker,
                available=False,
                error=data["error"],
            )

        rating = data.get("rating")
        if rating is None:
            return TAResult(
                ticker=ticker,
                available=False,
                error="NO_RATING_IN_OUTPUT",
            )

        return TAResult(
            ticker=ticker,
            rating=rating,
            available=True,
            raw_decision=data.get("final_decision"),
        )
