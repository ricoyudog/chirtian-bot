"""Shadow observation runner — orchestrates pipeline in shadow mode."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Optional, Protocol

from src.shadow.metrics import MetricsCollector
from src.shadow.state import ObservationStateStore
from src.state.ledger import AuditLedger

US_MARKET_HOLIDAYS_2026 = frozenset({
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
    "2026-05-25", "2026-07-03", "2026-09-07", "2026-11-26",
    "2026-11-27", "2026-12-25",
})

MIN_SIGNALS = 10
MIN_DURATION_DAYS = 7
MAX_DURATION_WEEKS = 4
SUMMARIES_DIR = "runtime/shadow_summaries"


def is_trading_day(dt: datetime) -> bool:
    """Check if a date is a US equity trading day (weekday, not holiday)."""
    if dt.weekday() >= 5:
        return False
    return dt.strftime("%Y-%m-%d") not in US_MARKET_HOLIDAYS_2026


def next_trading_day(dt: datetime) -> datetime:
    """Find the next trading day after the given datetime."""
    candidate = dt + timedelta(days=1)
    while not is_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate.replace(hour=9, minute=30, second=0, microsecond=0)


def is_deferred_window(dt: datetime) -> bool:
    """Check if signal falls in a deferred window (weekend/holiday)."""
    return not is_trading_day(dt)


@dataclass
class PipelineResult:
    signal_id: str
    stages: list[dict]
    total_latency_ms: float
    outcome: str  # success | failure | stale | deferred
    deferred_until: Optional[str] = None


class Pipeline(Protocol):
    """Protocol for the pipeline to be orchestrated."""

    def run(self, signal_text: str, signal_id: str) -> PipelineResult: ...


class ShadowObservationRunner:
    """Orchestrates the full pipeline in shadow mode with observation period tracking."""

    def __init__(
        self,
        state_store: ObservationStateStore,
        metrics_collector: MetricsCollector,
        ledger: AuditLedger,
        pipeline: Optional[Pipeline] = None,
    ):
        self._state = state_store
        self._metrics = metrics_collector
        self._ledger = ledger
        self._pipeline = pipeline

    def process_signal(self, signal_text: str, signal_id: str) -> PipelineResult:
        """Process a single signal through the pipeline in shadow mode."""
        state = self._state.get_active()
        if state is None:
            raise RuntimeError("No active observation period. Start one first.")

        signal_time = datetime.now(UTC)

        # Check deferred window
        if is_deferred_window(signal_time):
            deferred_to = next_trading_day(signal_time)
            result = PipelineResult(
                signal_id=signal_id,
                stages=[],
                total_latency_ms=0.0,
                outcome="deferred",
                deferred_until=deferred_to.isoformat(),
            )
            self._metrics.record_stage(
                signal_id=signal_id,
                stage="detection",
                latency_ms=0.0,
                outcome="deferred",
            )
            self._state.increment_signals()
            return result

        # Run pipeline with timing
        start_ms = time.monotonic() * 1000

        if self._pipeline is not None:
            result = self._pipeline.run(signal_text, signal_id)
        else:
            # Without a real pipeline, record a no-op
            result = PipelineResult(
                signal_id=signal_id,
                stages=[],
                total_latency_ms=0.0,
                outcome="success",
            )

        end_ms = time.monotonic() * 1000
        total_latency = end_ms - start_ms
        result.total_latency_ms = total_latency

        # Record metrics for each stage
        for stage_data in result.stages:
            self._metrics.record_stage(
                signal_id=signal_id,
                stage=stage_data["stage"],
                latency_ms=stage_data["latency_ms"],
                outcome=stage_data.get("outcome", "success"),
                error_type=stage_data.get("error_type"),
            )

        # Classify stale
        if self._metrics.classify_stale(total_latency, signal_time.isoformat()):
            result.outcome = "stale"
            self._metrics.record_stage(
                signal_id=signal_id,
                stage="detection",
                latency_ms=total_latency,
                outcome="stale",
            )

        self._state.increment_signals()
        return result

    def check_status(self) -> dict:
        """Get current observation period status with extension check."""
        state = self._state.get_active()
        if state is None:
            return {"status": "no_active_observation"}

        started = datetime.fromisoformat(state["started_at"])
        now = datetime.now(UTC)
        elapsed_days = (now - started).days
        max_reached = self._state.is_max_duration_reached()
        should_extend = self._state.should_extend(min_signals=MIN_SIGNALS)

        return {
            **state,
            "elapsed_days": elapsed_days,
            "min_duration_met": elapsed_days >= MIN_DURATION_DAYS,
            "min_signals_met": state["signals_processed"] >= MIN_SIGNALS,
            "should_extend": should_extend,
            "max_duration_reached": max_reached,
        }

    def generate_summary(self) -> str:
        """Generate shadow run summary and write to file."""
        state = self._state.get_active()
        if state is None:
            # Try to get the most recently completed
            raise RuntimeError("No observation period to summarize.")

        report = self._metrics.generate_report(since=state["started_at"])
        status = self.check_status()

        lines = [
            f"# Shadow Run Summary — {datetime.now(UTC).strftime('%Y-%m-%d')}",
            "",
            f"**Observation ID:** {state['observation_id']}",
            f"**Started:** {state['started_at']}",
            f"**Signals Processed:** {state['signals_processed']}",
            f"**Elapsed Days:** {status.get('elapsed_days', 'N/A')}",
            "",
            "## Pipeline Metrics",
            "",
        ]

        for stage_name, stats in sorted(report.stages.items()):
            lines.append(f"### {stage_name}")
            lines.append(f"- Count: {stats.count}")
            lines.append(f"- p50: {stats.p50_ms:.1f}ms")
            lines.append(f"- p95: {stats.p95_ms:.1f}ms")
            lines.append(f"- Max: {stats.max_ms:.1f}ms")
            if stats.outcomes:
                lines.append(f"- Outcomes: {stats.outcomes}")
            lines.append("")

        lines.extend([
            "## Stale Signal Analysis",
            "",
            f"- Stale count: {report.stale_count}",
            f"- Stale rate: {report.stale_rate:.1%}",
            f"- Threshold exceeded: {'YES' if report.stale_rate_exceeded else 'NO'}",
            "",
        ])

        lines.extend([
            "## Go/No-Go Readiness Checklist",
            "",
            f"- [{'x' if status.get('min_signals_met') else ' '}] "
            f"Minimum signals (≥{MIN_SIGNALS})",
            f"- [{'x' if status.get('min_duration_met') else ' '}] "
            f"Minimum duration (≥{MIN_DURATION_DAYS} days)",
            f"- [{'x' if not report.stale_rate_exceeded else ' '}] Stale signal rate ≤5%",
            "- [ ] Kill switch drill completed",
            "- [ ] Alert channel tested",
            "- [ ] No unresolved ORDER_UNKNOWN",
            "- [ ] No duplicate order incidents",
            "- [ ] Reconcile state clean",
            "- [ ] Risk limits approved",
            "",
        ])

        content = "\n".join(lines)

        # Write to file
        summaries_path = Path(SUMMARIES_DIR)
        summaries_path.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.now(UTC).strftime('%Y-%m-%d')}-shadow-run-summary.md"
        filepath = summaries_path / filename
        filepath.write_text(content)

        return content
