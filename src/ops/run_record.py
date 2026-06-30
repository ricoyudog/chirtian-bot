"""Structured run-record for pipeline executions (writes runtime/runs.jsonl)."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class RunRecorder:
    """Records structured pipeline runs as append-only JSONL.

    run_id format: {YYYY-MM-DD}-{seq:03d}-{uuid[:8]}.
    Per-instruction stage_timings: {stage: {started_at, duration_ms, skipped}}.
    Thread-safe via a single lock around mutable state + write.
    """

    def __init__(self, runs_dir: str | Path = "runtime"):
        self.runs_dir = Path(runs_dir)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.runs_path = self.runs_dir / "runs.jsonl"
        self._lock = threading.Lock()
        self._current: dict[str, Any] | None = None
        self._current_stage_timings: dict[str, dict[str, Any]] = {}
        self._seq_counter = 0

    def start_run(self, mode: str, environment: str) -> str:
        """Begin a new run, return its run_id."""
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        with self._lock:
            self._seq_counter += 1
            short_uuid = uuid.uuid4().hex[:8]
            run_id = f"{date_str}-{self._seq_counter:03d}-{short_uuid}"
            self._current = {
                "run_id": run_id,
                "started_at": _utc_now_iso(),
                "ended_at": None,
                "mode": mode,
                "environment": environment,
                "signals_processed": 0,
                "instructions": [],
                "errors": [],
                "outcome": None,
            }
            self._current_stage_timings = {}
            return run_id

    def record_stage_timing(
        self,
        stage_name: str,
        duration_ms: int | None = None,
        skipped: bool = False,
    ) -> None:
        """Record timing for a stage of the current instruction."""
        with self._lock:
            self._current_stage_timings[stage_name] = {
                "started_at": _utc_now_iso(),
                "duration_ms": duration_ms,
                "skipped": skipped,
            }

    def record_instruction_outcome(
        self,
        instruction_id: str,
        symbol: str,
        action: str,
        outcome: str,
        stage_timings: dict[str, Any] | None = None,
    ) -> None:
        """Finalize and append an instruction's outcome to the current run."""
        with self._lock:
            if self._current is None:
                raise RuntimeError("record_instruction_outcome called with no active run")
            if stage_timings is not None:
                timings = stage_timings
            else:
                timings = dict(self._current_stage_timings)
            self._current["instructions"].append({
                "instruction_id": instruction_id,
                "symbol": symbol,
                "action": action,
                "outcome": outcome,
                "stage_timings": timings,
            })
            self._current["signals_processed"] = len(self._current["instructions"])
            self._current_stage_timings = {}

    def record_error(self, stage: str, message: str) -> None:
        """Append an error summary to the current run."""
        with self._lock:
            if self._current is None:
                raise RuntimeError("record_error called with no active run")
            self._current["errors"].append({"stage": stage, "message": message})

    def end_run(self, outcome: str, reason: str | None = None) -> None:
        """Finalize the current run with outcome (and optional reason) and write to JSONL."""
        with self._lock:
            if self._current is None:
                raise RuntimeError("end_run called with no active run")
            self._current["ended_at"] = _utc_now_iso()
            self._current["outcome"] = outcome
            if reason is not None:
                self._current["reason"] = reason
            self._write_run()
            self._current = None
            self._current_stage_timings = {}

    def _write_run(self) -> None:
        """Append the current run record as one JSONL line. Caller holds _lock."""
        if self._current is None:
            return
        line = json.dumps(self._current)
        with open(self.runs_path, "a") as f:
            f.write(line + "\n")
