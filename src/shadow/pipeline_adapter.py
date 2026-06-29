"""Adapter bridging the shadow ``Pipeline.run`` contract to the trading orchestrator.

Shadow observation speaks the ``Pipeline.run(signal_text, signal_id) -> PipelineResult``
protocol (one signal_id = one result). The real execution path is
``TradingPipeline.process_post(post_id, raw_text, account_id) -> list[InstructionOutcome]``
(one post may yield several instructions). This adapter calls the orchestrator
through the real pipeline and *folds* the per-instruction outcomes into the single
``PipelineResult`` the shadow metrics expect.

Safety: the adapter never decides *whether* to trade live — that is the wiring
layer's job (``build_shadow_stack``). The adapter only translates once a real
``TradingPipeline`` has been handed to it.

Contract bridging (see wiki/decisions/2026-06-15-pipeline-orchestrator.md):
- Input:  ``signal_id`` is passed through as the orchestrator ``post_id``.
  Re-running the same signal therefore hits ``DUPLICATE_EXECUTION`` — i.e.
  ``signal_id`` is now an idempotency key (intended).
- Output: many ``InstructionOutcome`` → one ``PipelineResult`` (folded).
- Vocabulary: orchestrator outcomes → ``MetricsCollector`` stage outcomes.
- Timing: the orchestrator does not time per-stage, so the adapter measures the
  *overall* latency truthfully and splits it evenly across the emitted stage
  rows (honest about the uncertainty — never fabricated).
"""

from __future__ import annotations

import time
from typing import Callable, Optional

from src.pipeline.orchestrator import (
    OUTCOME_BLOCKED,
    OUTCOME_NEEDS_REVIEW,
    OUTCOME_PLACED,
    OUTCOME_REJECTED,
    OUTCOME_SKIPPED,
    InstructionOutcome,
)
from src.shadow.runner import PipelineResult

# ---------------------------------------------------------------------------
# Severity ordering for the overall rollup (low → high).
# Mirrors the worst-of ordering in the plan:
#   success < ta_skipped < deferred < stale < timeout < failure
# ---------------------------------------------------------------------------
_SEVERITY = {
    "success": 0,
    "ta_skipped": 1,
    "deferred": 2,
    "stale": 3,
    "timeout": 4,
    "failure": 5,
}


def _translate_outcome(o: InstructionOutcome) -> tuple[str, str, Optional[str]]:
    """Map one orchestrator outcome to a (stage, metrics_outcome, error_type) row.

    Returns values in the ``MetricsCollector`` vocabulary: ``stage`` is one of
    ``STAGE_NAMES`` and ``metrics_outcome`` is one of ``OUTCOMES``.
    """
    outcome, reason = o.outcome, o.reason or ""

    if outcome == OUTCOME_PLACED:
        return "broker", "success", None

    if outcome == OUTCOME_SKIPPED:
        # Parse-stage skip (non-actionable / needs review at parse time).
        if reason.startswith("PARSE_"):
            return "parse", "success", reason
        # Sizing-stage skip.
        if reason.startswith("SIZING_"):
            return "sizing", "success", reason
        # Confirmation path declined to place.
        if reason == "CONFIRMATION_NOT_APPROVED":
            return "broker", "success", reason
        # Unknown skip → observable event, not a failure.
        return "parse", "success", reason or None

    if outcome == OUTCOME_NEEDS_REVIEW:
        # ta_gateway=None passthrough — TA was intentionally skipped.
        if reason == "TA_SKIPPED":
            return "ta", "ta_skipped", None
        # Scope guards fire before fusion/sizing but read as a sizing-stage
        # rejection of the instrument.
        if reason in ("NON_US_MARKET", "SYMBOL_NOT_WHITELISTED"):
            return "sizing", "success", reason
        # Fusion needs-review (TA unavailable/opposed, etc.).
        return "ta", "success", f"NEEDS_REVIEW:{reason}" if reason else None

    if outcome == OUTCOME_REJECTED:
        # Fusion rejected the instruction.
        return "ta", "success", f"REJECTED:{reason}" if reason else None

    if outcome == OUTCOME_BLOCKED:
        if reason == "RECONCILE_MISMATCH":
            return "execution_gate", "failure", reason
        if reason == "DUPLICATE_EXECUTION":
            # Idempotent re-run — expected, not a failure.
            return "execution_gate", "success", reason
        if reason == "DATA_OR_SIZING_FAILED":
            return "sizing", "failure", reason
        if reason in ("PREVIEW_FAILED", "PLACE_FAILED"):
            return "broker", "failure", reason
        # Unknown blocked reason → fail closed.
        return "broker", "failure", reason or None

    # Unknown orchestrator outcome → fail closed rather than silently mislabel.
    return "broker", "failure", f"UNKNOWN_OUTCOME:{outcome}"


def _translate(
    signal_id: str,
    outcomes: list[InstructionOutcome],
    total_latency_ms: float,
) -> PipelineResult:
    """Fold orchestrator outcomes into a single shadow ``PipelineResult``.

    Pure function — no ``TradingPipeline`` needed, so it is unit-tested directly.

    Overall outcome rules:
    - any instruction ``placed`` → ``success``;
    - else any stage rolled to ``failure`` → ``failure``;
    - otherwise ``success`` (skipped/needs_review/rejected are observable
      events, not pipeline faults).

    Per-stage latency is the overall latency split evenly across the emitted
    rows (the orchestrator does not time stages individually).
    """
    stages: list[dict] = []
    any_placed = False
    any_failure = False

    for o in outcomes:
        stage, metrics_outcome, error_type = _translate_outcome(o)
        stages.append(
            {
                "stage": stage,
                "latency_ms": 0.0,  # filled after we know the row count
                "outcome": metrics_outcome,
                "error_type": error_type,
            }
        )
        if o.placed:
            any_placed = True
        if metrics_outcome == "failure":
            any_failure = True

    if any_placed:
        overall = "success"
    elif any_failure:
        overall = "failure"
    else:
        overall = "success"

    n = len(stages)
    if n:
        per_stage = total_latency_ms / n
        for row in stages:
            row["latency_ms"] = per_stage

    return PipelineResult(
        signal_id=signal_id,
        stages=stages,
        total_latency_ms=total_latency_ms,
        outcome=overall,
    )


class ShadowPipelineAdapter:
    """Adapts a ``TradingPipeline`` to the shadow ``Pipeline`` protocol.

    ``run(signal_text, signal_id)`` drives the real orchestrator
    (``process_post``) using ``signal_id`` as the post id / idempotency key,
    then folds the outcomes via :func:`_translate`.
    """

    def __init__(
        self,
        trading_pipeline,
        account_id: str,
        *,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._tp = trading_pipeline
        self._account_id = account_id
        self._now = now

    def run(self, signal_text: str, signal_id: str) -> PipelineResult:
        """Run one signal through the real orchestrator and translate the result."""
        t0 = self._now()
        try:
            outcomes = self._tp.process_post(signal_id, signal_text, self._account_id)
        except Exception as exc:
            # The orchestrator raised (parser/broker/…). Surface a truthful
            # failure with a broker-stage row and the exception type.
            total_latency_ms = (self._now() - t0) * 1000.0
            return PipelineResult(
                signal_id=signal_id,
                stages=[
                    {
                        "stage": "broker",
                        "latency_ms": total_latency_ms,
                        "outcome": "failure",
                        "error_type": type(exc).__name__,
                    }
                ],
                total_latency_ms=total_latency_ms,
                outcome="failure",
            )

        total_latency_ms = (self._now() - t0) * 1000.0
        return _translate(signal_id, outcomes, total_latency_ms)
