"""Unit tests for the shadow → orchestrator pipeline adapter.

Cases 1–6 exercise the pure :func:`_translate` folder directly (no
``TradingPipeline``). Cases 7–8 drive ``ShadowPipelineAdapter.run`` with a
spy/fake orchestrator to verify exception handling and the signal_id→post_id
bridge.
"""

from __future__ import annotations

import pytest

from src.pipeline.orchestrator import InstructionOutcome
from src.shadow.pipeline_adapter import ShadowPipelineAdapter, _translate


def _outcome(outcome: str, reason: str = "", **kw) -> InstructionOutcome:
    return InstructionOutcome(
        instruction_id=kw.get("instruction_id", "instr:0"),
        symbol=kw.get("symbol", "AAPL"),
        action=kw.get("action", "BUY"),
        outcome=outcome,
        reason=reason,
        **{k: v for k, v in kw.items() if k not in ("instruction_id", "symbol", "action")},
    )


# ---------------------------------------------------------------------------
# Pure _translate cases
# ---------------------------------------------------------------------------


def test_translate_placed_is_success_with_broker_row():
    result = _translate("sig-1", [_outcome("placed", "OK")], total_latency_ms=120.0)

    assert result.signal_id == "sig-1"
    assert result.outcome == "success"
    assert len(result.stages) == 1
    broker = result.stages[0]
    assert broker["stage"] == "broker"
    assert broker["outcome"] == "success"
    assert broker["error_type"] is None
    # even split across a single row preserves the overall latency
    assert broker["latency_ms"] == pytest.approx(120.0)
    assert result.total_latency_ms == pytest.approx(120.0)


def test_translate_reconcile_mismatch_is_failure():
    result = _translate(
        "sig-1",
        [_outcome("blocked", "RECONCILE_MISMATCH")],
        total_latency_ms=50.0,
    )

    assert result.outcome == "failure"
    gate = result.stages[0]
    assert gate["stage"] == "execution_gate"
    assert gate["outcome"] == "failure"
    assert gate["error_type"] == "RECONCILE_MISMATCH"


def test_translate_duplicate_execution_is_success():
    result = _translate(
        "sig-1",
        [_outcome("blocked", "DUPLICATE_EXECUTION")],
        total_latency_ms=50.0,
    )

    assert result.outcome == "success"
    gate = result.stages[0]
    assert gate["stage"] == "execution_gate"
    assert gate["outcome"] == "success"
    assert gate["error_type"] == "DUPLICATE_EXECUTION"


def test_translate_multi_instruction_mixed_overall_success():
    # One placed (success) + one broker PLACE_FAILED (failure). Overall success
    # because a placement happened; the failure row is still surfaced.
    result = _translate(
        "sig-1",
        [
            _outcome("placed", "OK", instruction_id="instr:0"),
            _outcome("blocked", "PLACE_FAILED", instruction_id="instr:1"),
        ],
        total_latency_ms=200.0,
    )

    assert result.outcome == "success"
    assert len(result.stages) == 2
    broker_rows = [s for s in result.stages if s["stage"] == "broker"]
    assert len(broker_rows) == 2
    outcomes = {row["outcome"] for row in broker_rows}
    assert outcomes == {"success", "failure"}
    failed = next(r for r in broker_rows if r["outcome"] == "failure")
    assert failed["error_type"] == "PLACE_FAILED"
    # even split: 200ms / 2 rows
    for row in result.stages:
        assert row["latency_ms"] == pytest.approx(100.0)


def test_translate_parse_skipped_only_parse_row():
    result = _translate(
        "sig-1",
        [_outcome("skipped", "PARSE_SKIP_NOT_ACTIONABLE")],
        total_latency_ms=10.0,
    )

    assert result.outcome == "success"
    assert len(result.stages) == 1
    assert result.stages[0]["stage"] == "parse"
    assert result.stages[0]["outcome"] == "success"
    assert result.stages[0]["error_type"] == "PARSE_SKIP_NOT_ACTIONABLE"


def test_translate_ta_skipped_is_ta_row():
    # ta_gateway=None passthrough → needs_review / TA_SKIPPED → ta_skipped row.
    result = _translate(
        "sig-1",
        [_outcome("needs_review", "TA_SKIPPED")],
        total_latency_ms=10.0,
    )

    assert result.outcome == "success"
    assert len(result.stages) == 1
    assert result.stages[0]["stage"] == "ta"
    assert result.stages[0]["outcome"] == "ta_skipped"
    assert result.stages[0]["error_type"] is None


# ---------------------------------------------------------------------------
# ShadowPipelineAdapter.run cases (spy/fake orchestrator)
# ---------------------------------------------------------------------------


class _SpyOrchestrator:
    """Records the post_id passed to process_post; returns canned outcomes."""

    def __init__(self, outcomes, *, raise_exc=None):
        self._outcomes = outcomes
        self._raise = raise_exc
        self.process_post_calls = []

    def process_post(self, post_id, raw_text, account_id):
        self.process_post_calls.append((post_id, raw_text, account_id))
        if self._raise is not None:
            raise self._raise
        return self._outcomes


def test_run_raises_surfaces_failure_with_error_type():
    spy = _SpyOrchestrator([], raise_exc=RuntimeError("boom"))
    # Deterministic clock: 0.0 → 0.005s elapsed → 5ms.
    ticks = iter([0.0, 0.005])
    adapter = ShadowPipelineAdapter(spy, "ACC1", now=lambda: next(ticks))

    result = adapter.run("加倉 AAPL 1%", "sig-9")

    assert result.outcome == "failure"
    assert len(result.stages) == 1
    assert result.stages[0]["stage"] == "broker"
    assert result.stages[0]["outcome"] == "failure"
    assert result.stages[0]["error_type"] == "RuntimeError"
    assert result.total_latency_ms == pytest.approx(5.0, rel=1e-6)


def test_signal_id_used_as_post_id():
    spy = _SpyOrchestrator([_outcome("placed", "OK")])
    adapter = ShadowPipelineAdapter(spy, "ACC1")

    result = adapter.run("加倉 AAPL 1%", "sig-post-42")

    assert result.outcome == "success"
    # signal_id is bridged through as the orchestrator post_id / idempotency key.
    assert spy.process_post_calls == [("sig-post-42", "加倉 AAPL 1%", "ACC1")]
