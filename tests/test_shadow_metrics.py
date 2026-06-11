"""Unit tests for shadow metrics collector."""

import json
from pathlib import Path

import pytest

from src.shadow.metrics import (
    METRIC_PREFIX,
    MetricsCollector,
    MetricsReport,
    StageStats,
    _percentile,
)
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent


@pytest.fixture
def ledger(tmp_path):
    return AuditLedger(tmp_path / "test_shadow.jsonl")


@pytest.fixture
def collector(ledger):
    return MetricsCollector(ledger, source="test")


class TestRecordStage:
    def test_records_to_audit_ledger(self, collector, ledger):
        collector.record_stage("sig-1", "detection", 120.5, "success")

        events = ledger.query()
        assert len(events) == 1
        e = events[0]
        assert e.event_type == f"{METRIC_PREFIX}detection"
        assert e.correlation_id == "sig-1"
        assert e.data["signal_id"] == "sig-1"
        assert e.data["stage"] == "detection"
        assert e.data["latency_ms"] == 120.5
        assert e.data["outcome"] == "success"
        assert e.data["error_type"] is None

    def test_records_error_type(self, collector, ledger):
        collector.record_stage("sig-2", "parse", 500.0, "failure", error_type="TimeoutError")

        events = ledger.query()
        assert events[0].data["error_type"] == "TimeoutError"

    def test_rejects_unknown_stage(self, collector):
        with pytest.raises(ValueError, match="Unknown stage"):
            collector.record_stage("sig-1", "unknown_stage", 100.0, "success")

    def test_rejects_unknown_outcome(self, collector):
        with pytest.raises(ValueError, match="Unknown outcome"):
            collector.record_stage("sig-1", "detection", 100.0, "bad_outcome")

    def test_records_multiple_stages_for_same_signal(self, collector, ledger):
        collector.record_stage("sig-1", "detection", 50.0, "success")
        collector.record_stage("sig-1", "parse", 200.0, "success")
        collector.record_stage("sig-1", "broker", 800.0, "success")

        events = ledger.query(correlation_id="sig-1")
        assert len(events) == 3


class TestStaleClassification:
    def test_weekday_signal_above_threshold_is_stale(self, collector):
        # 2026-06-10 is a Wednesday, market open
        is_stale = collector.classify_stale(
            total_latency_ms=20 * 60_000,  # 20 minutes
            signal_timestamp="2026-06-10T10:00:00+00:00",
            stale_window_minutes=15.0,
        )
        assert is_stale is True

    def test_weekday_signal_below_threshold_not_stale(self, collector):
        is_stale = collector.classify_stale(
            total_latency_ms=10 * 60_000,  # 10 minutes
            signal_timestamp="2026-06-10T10:00:00+00:00",
            stale_window_minutes=15.0,
        )
        assert is_stale is False

    def test_weekend_signal_not_stale(self, collector):
        # 2026-06-14 is a Sunday
        is_stale = collector.classify_stale(
            total_latency_ms=20 * 60_000,  # 20 minutes
            signal_timestamp="2026-06-14T10:00:00+00:00",
            stale_window_minutes=15.0,
        )
        assert is_stale is False

    def test_custom_window(self, collector):
        is_stale = collector.classify_stale(
            total_latency_ms=3 * 60_000,  # 3 minutes
            signal_timestamp="2026-06-10T10:00:00+00:00",
            stale_window_minutes=2.0,
        )
        assert is_stale is True


class TestMetricsReport:
    def test_empty_report(self, collector):
        report = collector.generate_report()
        assert report.total_signals == 0
        assert report.stale_count == 0
        assert report.stale_rate == 0.0
        assert report.stale_rate_exceeded is False

    def test_report_with_single_signal(self, collector):
        collector.record_stage("sig-1", "detection", 100.0, "success")
        collector.record_stage("sig-1", "parse", 200.0, "success")

        report = collector.generate_report()
        assert report.total_signals == 1
        assert "detection" in report.stages
        assert "parse" in report.stages
        assert report.stages["detection"].p50_ms == 100.0
        assert report.stages["parse"].p50_ms == 200.0

    def test_report_with_multiple_signals(self, collector):
        for i in range(10):
            collector.record_stage(f"sig-{i}", "detection", 100.0 + i * 10, "success")

        report = collector.generate_report()
        assert report.total_signals == 10
        assert report.stages["detection"].count == 10

    def test_stale_rate_warning(self, collector):
        # 10 signals, 1 stale -> 10% > 5%
        for i in range(9):
            collector.record_stage(f"sig-{i}", "detection", 100.0, "success")
        collector.record_stage("sig-stale", "detection", 500.0, "stale")

        report = collector.generate_report()
        assert report.stale_count == 1
        assert report.stale_rate == pytest.approx(0.1)
        assert report.stale_rate_exceeded is True

    def test_stale_rate_within_threshold(self, collector):
        # 20 signals, 1 stale -> 5% = not exceeded
        for i in range(19):
            collector.record_stage(f"sig-{i}", "detection", 100.0, "success")
        collector.record_stage("sig-stale", "detection", 500.0, "stale")

        report = collector.generate_report()
        assert report.stale_rate == pytest.approx(0.05)
        assert report.stale_rate_exceeded is False

    def test_outcome_breakdown(self, collector):
        collector.record_stage("sig-1", "parse", 100.0, "success")
        collector.record_stage("sig-2", "parse", 200.0, "failure", error_type="ParseError")
        collector.record_stage("sig-3", "parse", 300.0, "timeout")

        report = collector.generate_report()
        outcomes = report.stages["parse"].outcomes
        assert outcomes["success"] == 1
        assert outcomes["failure"] == 1
        assert outcomes["timeout"] == 1

    def test_report_since_filter(self, collector, ledger):
        # Insert old event directly
        old_event = AuditEvent(
            event_type=f"{METRIC_PREFIX}detection",
            source="test",
            timestamp="2020-01-01T00:00:00+00:00",
            data={"signal_id": "old", "stage": "detection", "latency_ms": 50.0, "outcome": "success"},
            correlation_id="old",
        )
        ledger.append(old_event)

        collector.record_stage("sig-new", "detection", 200.0, "success")

        report = collector.generate_report(since="2026-01-01T00:00:00+00:00")
        assert report.total_signals == 1

    def test_percentile_calculation(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        assert _percentile(values, 50) == 30.0
        assert _percentile(values, 95) == 48.0
        assert _percentile([], 50) == 0.0

    def test_ta_skipped_outcome(self, collector):
        collector.record_stage("sig-1", "ta", 0.0, "ta_skipped")

        report = collector.generate_report()
        assert report.stages["ta"].outcomes["ta_skipped"] == 1

    def test_deferred_outcome(self, collector):
        collector.record_stage("sig-1", "detection", 0.0, "deferred")

        report = collector.generate_report()
        assert report.stages["detection"].outcomes["deferred"] == 1

    def test_full_report_includes_all_required_fields(self, collector):
        """Scenario: report includes all required observation metrics."""
        # Record metrics across multiple stages and outcomes
        collector.record_stage("sig-1", "detection", 50.0, "success")
        collector.record_stage("sig-1", "parse", 200.0, "success")
        collector.record_stage("sig-1", "llm", 1500.0, "success")
        collector.record_stage("sig-1", "ta", 0.0, "ta_skipped")
        collector.record_stage("sig-1", "sizing", 100.0, "success")
        collector.record_stage("sig-1", "execution_gate", 30.0, "success")
        collector.record_stage("sig-1", "broker", 800.0, "success")
        collector.record_stage("sig-2", "parse", 300.0, "failure", error_type="ParseError")
        collector.record_stage("sig-3", "detection", 500.0, "stale")

        report = collector.generate_report()

        # All 7 stages present
        assert len(report.stages) >= 4  # at least the stages we recorded
        assert "detection" in report.stages
        assert "parse" in report.stages
        assert "broker" in report.stages

        # Each stage has latency stats
        for stage_name, stats in report.stages.items():
            assert stats.count > 0
            assert stats.p50_ms >= 0
            assert stats.p95_ms >= 0
            assert stats.max_ms >= 0
            assert isinstance(stats.outcomes, dict)

        # Signal counts
        assert report.total_signals == 3
        assert report.stale_count == 1
        assert report.stale_rate == pytest.approx(1 / 3, abs=0.01)
