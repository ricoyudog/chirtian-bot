"""Tests for the append-only JSONL audit ledger."""

from src.state.ledger import AuditLedger
from src.state.models import AuditEvent


def _make_event(**overrides) -> AuditEvent:
    defaults = dict(
        event_type="test_event",
        config_hash="sha256:abc123",
        source="test",
        data={"key": "value"},
    )
    defaults.update(overrides)
    return AuditEvent(**defaults)


class TestAppendAndRead:
    def test_append_single_event_and_read_back(self, tmp_ledger):
        ledger = AuditLedger(tmp_ledger)
        event = _make_event(event_type="config_loaded")
        ledger.append(event)

        results = ledger.query()
        assert len(results) == 1
        assert results[0].event_id == event.event_id
        assert results[0].event_type == "config_loaded"
        assert results[0].config_hash == "sha256:abc123"


class TestQueryByType:
    def test_filter_by_event_type(self, tmp_ledger):
        ledger = AuditLedger(tmp_ledger)
        ledger.append(_make_event(event_type="job_enqueued"))
        ledger.append(_make_event(event_type="job_completed"))
        ledger.append(_make_event(event_type="job_enqueued"))

        results = ledger.query(event_type="job_enqueued")
        assert len(results) == 2
        assert all(r.event_type == "job_enqueued" for r in results)


class TestQueryByCorrelationId:
    def test_filter_by_correlation_id(self, tmp_ledger):
        ledger = AuditLedger(tmp_ledger)
        ledger.append(_make_event(correlation_id="corr-1"))
        ledger.append(_make_event(correlation_id="corr-2"))
        ledger.append(_make_event(correlation_id="corr-1"))

        results = ledger.query(correlation_id="corr-1")
        assert len(results) == 2
        assert all(r.correlation_id == "corr-1" for r in results)


class TestQueryBySince:
    def test_filter_by_since_timestamp(self, tmp_ledger):
        ledger = AuditLedger(tmp_ledger)
        ledger.append(_make_event(timestamp="2026-01-01T00:00:00+00:00"))
        ledger.append(_make_event(timestamp="2026-06-01T00:00:00+00:00"))
        ledger.append(_make_event(timestamp="2026-12-01T00:00:00+00:00"))

        results = ledger.query(since="2026-03-01T00:00:00+00:00")
        assert len(results) == 2


class TestVerifyIntegrity:
    def test_valid_ledger_passes(self, tmp_ledger):
        ledger = AuditLedger(tmp_ledger)
        ledger.append(_make_event())
        ledger.append(_make_event())
        assert ledger.verify_integrity() is True

    def test_detects_malformed_lines(self, tmp_ledger):
        ledger = AuditLedger(tmp_ledger)
        ledger.append(_make_event())
        # Corrupt the ledger
        with open(tmp_ledger, "a") as f:
            f.write("NOT VALID JSON{{{}}}\n")
        assert ledger.verify_integrity() is False


class TestConfigHashInEvents:
    def test_config_hash_present_in_every_event(self, tmp_ledger):
        ledger = AuditLedger(tmp_ledger)
        for i in range(3):
            ledger.append(_make_event(config_hash=f"sha256:hash{i}"))

        results = ledger.query()
        assert len(results) == 3
        for r in results:
            assert r.config_hash.startswith("sha256:")
