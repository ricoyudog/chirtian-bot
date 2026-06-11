"""Shadow metrics collector — records per-stage pipeline latency and outcomes."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from src.state.ledger import AuditLedger
from src.state.models import AuditEvent

STAGE_NAMES = frozenset({
    "detection", "parse", "llm", "ta", "sizing", "execution_gate", "broker",
})

OUTCOMES = frozenset({
    "success", "failure", "timeout", "stale", "deferred", "ta_skipped",
})

METRIC_PREFIX = "shadow_metric."

DEFAULT_STALE_WINDOW_MINUTES = 15.0
STALE_RATE_THRESHOLD = 0.05


@dataclass
class StageMetric:
    signal_id: str
    stage: str
    latency_ms: float
    outcome: str
    error_type: Optional[str] = None


@dataclass
class StageStats:
    stage: str
    count: int = 0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    max_ms: float = 0.0
    outcomes: dict[str, int] = field(default_factory=dict)


@dataclass
class MetricsReport:
    stages: dict[str, StageStats] = field(default_factory=dict)
    total_signals: int = 0
    stale_count: int = 0
    stale_rate: float = 0.0
    stale_rate_exceeded: bool = False


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    return sorted_values[int(f)] * (c - k) + sorted_values[int(c)] * (k - f)


def _is_market_open_at(ts: str) -> bool:
    """Check if US equity market is open (weekday, simplified check)."""
    from datetime import datetime
    dt = datetime.fromisoformat(ts)
    return dt.weekday() < 5  # Mon=0 .. Fri=4


class MetricsCollector:
    """Records shadow observation metrics to AuditLedger."""

    def __init__(self, ledger: AuditLedger, source: str = "shadow"):
        self._ledger = ledger
        self._source = source

    def record_stage(
        self,
        signal_id: str,
        stage: str,
        latency_ms: float,
        outcome: str,
        error_type: Optional[str] = None,
    ) -> None:
        if stage not in STAGE_NAMES:
            raise ValueError(f"Unknown stage: {stage}")
        if outcome not in OUTCOMES:
            raise ValueError(f"Unknown outcome: {outcome}")

        event = AuditEvent(
            event_type=f"{METRIC_PREFIX}{stage}",
            source=self._source,
            data={
                "signal_id": signal_id,
                "stage": stage,
                "latency_ms": latency_ms,
                "outcome": outcome,
                "error_type": error_type,
            },
            correlation_id=signal_id,
        )
        self._ledger.append(event)

    def classify_stale(
        self,
        total_latency_ms: float,
        signal_timestamp: str,
        stale_window_minutes: float = DEFAULT_STALE_WINDOW_MINUTES,
    ) -> bool:
        """Classify a signal as stale due to pipeline delay (not market closure)."""
        if _is_market_open_at(signal_timestamp):
            return total_latency_ms > stale_window_minutes * 60_000
        return False

    def generate_report(
        self,
        since: Optional[str] = None,
        stale_window_minutes: float = DEFAULT_STALE_WINDOW_MINUTES,
    ) -> MetricsReport:
        """Aggregate all shadow metrics into a report."""
        events = self._ledger.query(event_type=None, since=since)
        metric_events = [e for e in events if e.event_type.startswith(METRIC_PREFIX)]

        stage_latencies: dict[str, list[float]] = {}
        stage_outcomes: dict[str, dict[str, int]] = {}
        signal_stale_count = 0
        signal_ids = set()

        for event in metric_events:
            data = event.data
            stage = data["stage"]
            signal_ids.add(data["signal_id"])

            stage_latencies.setdefault(stage, []).append(data["latency_ms"])

            outcomes = stage_outcomes.setdefault(stage, {})
            outcome = data["outcome"]
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

            if outcome == "stale":
                signal_stale_count += 1

        total_signals = len(signal_ids)
        stale_rate = signal_stale_count / total_signals if total_signals > 0 else 0.0

        stages: dict[str, StageStats] = {}
        for stage in stage_latencies:
            latencies = sorted(stage_latencies[stage])
            stages[stage] = StageStats(
                stage=stage,
                count=len(latencies),
                p50_ms=_percentile(latencies, 50),
                p95_ms=_percentile(latencies, 95),
                max_ms=latencies[-1] if latencies else 0.0,
                outcomes=stage_outcomes.get(stage, {}),
            )

        return MetricsReport(
            stages=stages,
            total_signals=total_signals,
            stale_count=signal_stale_count,
            stale_rate=stale_rate,
            stale_rate_exceeded=stale_rate > STALE_RATE_THRESHOLD,
        )
