"""Tests for RunRecorder: run_id, stage_timings, errors, abort, success path."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.ops.run_record import RunRecorder

RUN_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{3}-[0-9a-f]{8}$")


def _read_runs(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class TestRunId:
    def test_run_id_format_matches_spec(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        run_id = rec.start_run(mode="uat_confirm", environment="uat")
        assert RUN_ID_RE.match(run_id), f"bad run_id format: {run_id}"

    def test_seq_increments_within_recorder(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        r1 = rec.start_run(mode="uat_confirm", environment="uat")
        rec.end_run(outcome="success")
        r2 = rec.start_run(mode="uat_confirm", environment="uat")
        rec.end_run(outcome="success")
        seq1 = r1.split("-")[3]
        seq2 = r2.split("-")[3]
        assert int(seq2) == int(seq1) + 1

    def test_run_id_uniqueness_across_many_runs(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        ids = set()
        for _ in range(20):
            rid = rec.start_run(mode="uat", environment="uat")
            rec.end_run(outcome="success")
            ids.add(rid)
        assert len(ids) == 20

    def test_uuid_segment_is_hex8(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        run_id = rec.start_run(mode="uat", environment="uat")
        uuid_part = run_id.split("-")[4]
        assert len(uuid_part) == 8
        int(uuid_part, 16)  # parses as hex


class TestStageTimings:
    def test_record_stage_timing_attaches_started_at_and_duration(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        rec.start_run(mode="uat", environment="uat")
        rec.record_stage_timing("detect", duration_ms=500)
        rec.record_stage_timing("parse", duration_ms=2100)
        rec.record_stage_timing("llm", skipped=True)
        rec.record_instruction_outcome("ins-1", "NVDA", "BUY", "PLACED")
        rec.end_run(outcome="success")

        runs = _read_runs(tmp_path / "runs.jsonl")
        timings = runs[0]["instructions"][0]["stage_timings"]
        assert timings["detect"]["duration_ms"] == 500
        assert timings["parse"]["duration_ms"] == 2100
        assert timings["detect"]["started_at"] is not None
        assert timings["llm"]["skipped"] is True
        assert timings["llm"]["duration_ms"] is None

    def test_started_at_is_iso8601(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        rec.start_run(mode="uat", environment="uat")
        rec.record_stage_timing("detect", duration_ms=10)
        rec.record_instruction_outcome("ins-1", "NVDA", "BUY", "PLACED")
        rec.end_run(outcome="success")

        runs = _read_runs(tmp_path / "runs.jsonl")
        started = runs[0]["instructions"][0]["stage_timings"]["detect"]["started_at"]
        # parsable ISO-8601 with tz
        from datetime import datetime
        datetime.fromisoformat(started)

    def test_explicit_stage_timings_override_accumulated(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        rec.start_run(mode="uat", environment="uat")
        rec.record_stage_timing("detect", duration_ms=5)
        explicit = {
            "ta": {
                "started_at": "2026-07-05T14:30:00+00:00",
                "duration_ms": 1000,
                "skipped": False,
            }
        }
        rec.record_instruction_outcome("ins-1", "NVDA", "BUY", "PLACED", stage_timings=explicit)
        rec.end_run(outcome="success")

        runs = _read_runs(tmp_path / "runs.jsonl")
        timings = runs[0]["instructions"][0]["stage_timings"]
        assert timings == explicit


class TestRunLifecycle:
    def test_start_and_end_writes_jsonl_with_required_fields(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        run_id = rec.start_run(mode="uat_confirm", environment="uat")
        rec.end_run(outcome="success")

        runs = _read_runs(tmp_path / "runs.jsonl")
        assert len(runs) == 1
        r = runs[0]
        for field in (
            "run_id", "started_at", "ended_at", "mode", "environment",
            "signals_processed", "instructions", "errors", "outcome",
        ):
            assert field in r, f"missing field: {field}"
        assert r["run_id"] == run_id
        assert r["mode"] == "uat_confirm"
        assert r["environment"] == "uat"
        assert r["outcome"] == "success"
        assert r["errors"] == []
        assert r["instructions"] == []
        assert r["signals_processed"] == 0

    def test_end_run_with_reason_sets_reason_field(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        rec.start_run(mode="uat", environment="uat")
        rec.end_run(outcome="aborted", reason="SIGTERM_ABORT")
        runs = _read_runs(tmp_path / "runs.jsonl")
        assert runs[0]["outcome"] == "aborted"
        assert runs[0]["reason"] == "SIGTERM_ABORT"

    def test_signals_processed_tracks_instruction_count(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        rec.start_run(mode="uat", environment="uat")
        rec.record_instruction_outcome("ins-1", "NVDA", "BUY", "PLACED")
        rec.record_instruction_outcome("ins-2", "AMD", "SELL", "PLACED")
        rec.end_run(outcome="success")
        runs = _read_runs(tmp_path / "runs.jsonl")
        assert runs[0]["signals_processed"] == 2
        assert len(runs[0]["instructions"]) == 2


class TestErrorRecording:
    def test_record_error_appends_to_errors_array(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        rec.start_run(mode="uat", environment="uat")
        rec.record_error(stage="broker", message="connection refused")
        rec.end_run(outcome="error")

        runs = _read_runs(tmp_path / "runs.jsonl")
        assert runs[0]["outcome"] == "error"
        assert runs[0]["errors"] == [{"stage": "broker", "message": "connection refused"}]

    def test_multiple_errors_preserved_in_order(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        rec.start_run(mode="uat", environment="uat")
        rec.record_error(stage="parse", message="e1")
        rec.record_error(stage="ta", message="e2")
        rec.end_run(outcome="error")
        runs = _read_runs(tmp_path / "runs.jsonl")
        assert [e["message"] for e in runs[0]["errors"]] == ["e1", "e2"]


class TestAbortPath:
    def test_sigterm_abort_records_aborted_with_reason(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        run_id = rec.start_run(mode="uat", environment="uat")
        rec.record_error(stage="ta", message="SIGTERM received")
        rec.end_run(outcome="aborted", reason="SIGTERM_ABORT")
        runs = _read_runs(tmp_path / "runs.jsonl")
        r = runs[0]
        assert r["run_id"] == run_id
        assert r["outcome"] == "aborted"
        assert r["reason"] == "SIGTERM_ABORT"


class TestSuccessfulRunWithInstructions:
    def test_full_instruction_flow_written(self, tmp_path):
        rec = RunRecorder(runs_dir=tmp_path)
        rec.start_run(mode="uat_confirm", environment="uat")
        rec.record_stage_timing("detect", duration_ms=500)
        rec.record_stage_timing("parse", duration_ms=2100)
        rec.record_stage_timing("llm", skipped=True)
        rec.record_stage_timing("ta", duration_ms=1080000)
        rec.record_stage_timing("sizing", duration_ms=300)
        rec.record_stage_timing("exec", duration_ms=800)
        rec.record_stage_timing("broker", duration_ms=1200)
        rec.record_instruction_outcome(
            instruction_id="ins-1",
            symbol="NVDA",
            action="BUY",
            outcome="PLACED",
        )
        rec.end_run(outcome="success")

        runs = _read_runs(tmp_path / "runs.jsonl")
        r = runs[0]
        assert r["outcome"] == "success"
        assert r["signals_processed"] == 1
        ins = r["instructions"][0]
        assert ins["instruction_id"] == "ins-1"
        assert ins["symbol"] == "NVDA"
        assert ins["action"] == "BUY"
        assert ins["outcome"] == "PLACED"
        st = ins["stage_timings"]
        assert st["detect"]["duration_ms"] == 500
        assert st["ta"]["duration_ms"] == 1080000
        assert st["llm"]["skipped"] is True
        for stage in ("detect", "parse", "ta", "sizing", "exec", "broker"):
            assert st[stage]["started_at"] is not None


class TestThreadSafety:
    def test_concurrent_end_run_appends_each_exactly_once(self, tmp_path):
        # Lock must serialize JSONL appends from concurrent recorders without losing lines.
        import threading

        recorders = [RunRecorder(runs_dir=tmp_path) for _ in range(10)]
        for rec in recorders:
            rec.start_run(mode="uat", environment="uat")

        def worker(rec: RunRecorder):
            rec.end_run(outcome="success")

        threads = [threading.Thread(target=worker, args=(r,)) for r in recorders]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        runs = _read_runs(tmp_path / "runs.jsonl")
        assert len(runs) == 10


class TestInitCreatesDir:
    def test_init_creates_runs_dir(self, tmp_path):
        nested = tmp_path / "deep" / "nested" / "runtime"
        assert not nested.exists()
        rec = RunRecorder(runs_dir=nested)
        assert nested.exists()
        assert rec.runs_path == nested / "runs.jsonl"
