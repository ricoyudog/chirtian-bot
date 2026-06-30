"""FastAPI dashboard application factory.

Read-only observation layer over local runtime files. Per design:
- Decision #7: positions from SQLite (daemon writes, dashboard reads)
- Decision #11: bind 127.0.0.1, CORS for localhost only, kill-switch secret

The dashboard NEVER calls the broker API. All data is local files.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

STAGE_NAMES = ("detect", "parse", "llm", "ta", "sizing", "exec", "broker")
_HEARTBEAT_STALE_SECS = 120


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield each line of a JSONL file, skipping blanks and parse errors."""
    if not path.exists():
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Index-based percentile on a pre-sorted list. pct in [0, 1]."""
    if not sorted_vals:
        return 0.0
    idx = int(len(sorted_vals) * pct)
    if idx >= len(sorted_vals):
        idx = len(sorted_vals) - 1
    return sorted_vals[idx]


def _heartbeat_age_seconds(hb: dict[str, Any] | None, key: str) -> float | None:
    """Return age in seconds since the heartbeat timestamp, or None."""
    if not hb:
        return None
    ts = hb.get(key)
    if not ts:
        return None
    try:
        from datetime import UTC, datetime

        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return (datetime.now(UTC) - dt).total_seconds()
    except (ValueError, TypeError):
        return None


def _positions_from_db(db_path: Path) -> list[dict[str, Any]]:
    """Read latest tick's position rows. Empty list if DB missing/corrupt."""
    if not db_path.exists():
        return []
    try:
        # ponytail: check_same_thread=False — read-only short-lived queries
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            cur = conn.execute(
                "SELECT symbol, position_qty, market_value, unrealized_pnl, pnl_pct "
                "FROM position_snapshots WHERE tick_at = "
                "(SELECT MAX(tick_at) FROM position_snapshots)"
            )
            rows = cur.fetchall()
        finally:
            conn.close()
    except sqlite3.Error:
        return []
    return [
        {
            "symbol": r[0],
            "position_qty": r[1],
            "market_value": r[2],
            "unrealized_pnl": r[3],
            "pnl_pct": r[4],
        }
        for r in rows
    ]


@contextmanager
def _tail_jsonl(path: Path) -> Iterator[tuple]:
    """Open a JSONL file for tailing. Yields (file_handle, inode_at_open)."""
    f = open(path) if path.exists() else open(path, "a+")  # ensure exists
    f.seek(0, 2)  # EOF
    inode = path.stat().st_ino if path.exists() else 0
    try:
        yield f, inode
    finally:
        f.close()


async def _sse_event_stream(
    ledger_path: Path, stop_event: asyncio.Event
) -> AsyncIterator[bytes]:
    """Tail audit_ledger.jsonl and yield SSE events as `data: {json}\\n\\n`."""
    if not ledger_path.exists():
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.touch()
    f = open(ledger_path)
    f.seek(0, 2)
    last_inode = ledger_path.stat().st_ino
    try:
        while not stop_event.is_set():
            line = f.readline()
            if line:
                payload = json.dumps(json.loads(line))
                yield f"data: {payload}\n\n".encode()
                continue
            try:
                cur_inode = ledger_path.stat().st_ino
            except OSError:
                cur_inode = last_inode
            if cur_inode != last_inode:
                f.close()
                f = open(ledger_path)
                f.seek(0, 2)
                last_inode = cur_inode
                continue
            await asyncio.sleep(1.0)
    finally:
        f.close()


def create_app(runtime_dir: str | Path = "runtime") -> FastAPI:
    """Build the FastAPI app bound to a runtime directory.

    Args:
        runtime_dir: directory containing runs.jsonl, audit_ledger.jsonl,
            positions.db, heartbeat files, kill_switch.flag.
    """
    rt = Path(runtime_dir)
    rt.mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title="Christian Bot Dashboard",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # Decision #11: CORS for localhost only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:8000",
            "http://127.0.0.1",
            "http://127.0.0.1:8000",
        ],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    # Per-request state for SSE teardown
    app.state.sse_stop_events = set()  # set[asyncio.Event]

    # -- File path helpers --
    def _runs_path() -> Path:
        return rt / "runs.jsonl"

    def _ledger_path() -> Path:
        return rt / "audit_ledger.jsonl"

    def _posts_path() -> Path:
        return rt / "processed_posts.json"

    def _positions_path() -> Path:
        return rt / "positions.db"

    def _kill_flag() -> Path:
        return rt / "kill_switch.flag"

    def _daemon_hb() -> Path:
        return rt / "daemon_heartbeat.json"

    def _bot_hb() -> Path:
        return rt / "bot_heartbeat.json"

    # ---------- Task 4.3: GET /api/runs ----------
    @app.get("/api/runs")
    def list_runs(limit: int = 20) -> list[dict[str, Any]]:
        """Paginated list of recent runs (summary fields only)."""
        records = list(_read_jsonl(_runs_path()))
        records.reverse()  # most recent first
        out: list[dict[str, Any]] = []
        for r in records[: max(0, limit)]:
            out.append({
                "run_id": r.get("run_id"),
                "started_at": r.get("started_at"),
                "ended_at": r.get("ended_at"),
                "outcome": r.get("outcome"),
                "signals_processed": r.get("signals_processed", 0),
                "orders_placed": len(r.get("instructions", [])),
            })
        return out

    # ---------- Task 4.4: GET /api/runs/{run_id} ----------
    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        """Single run detail cross-referenced with audit_ledger.jsonl."""
        target: dict[str, Any] | None = None
        for r in _read_jsonl(_runs_path()):
            if r.get("run_id") == run_id:
                target = r
                break
        if target is None:
            raise HTTPException(status_code=404, detail="run not found")
        audit_events = [
            e
            for e in _read_jsonl(_ledger_path())
            if e.get("correlation_id") == run_id
        ]
        target["audit_events"] = audit_events
        return target

    # ---------- Task 4.5: GET /api/metrics ----------
    @app.get("/api/metrics")
    def get_metrics() -> dict[str, Any]:
        """Per-stage p50/p95/max latency aggregated across all runs."""
        stage_durations: dict[str, list[float]] = {s: [] for s in STAGE_NAMES}
        for r in _read_jsonl(_runs_path()):
            for instr in r.get("instructions", []):
                timings = instr.get("stage_timings", {}) or {}
                for stage in STAGE_NAMES:
                    t = timings.get(stage) or {}
                    dur = t.get("duration_ms")
                    if dur is not None and not t.get("skipped"):
                        stage_durations[stage].append(float(dur))
        out: dict[str, Any] = {"stages": {}}
        for stage in STAGE_NAMES:
            vals = sorted(stage_durations[stage])
            out["stages"][stage] = {
                "p50": _percentile(vals, 0.5),
                "p95": _percentile(vals, 0.95),
                "max": vals[-1] if vals else 0.0,
                "count": len(vals),
            }
        return out

    # ---------- Task 4.6: GET /api/safety ----------
    @app.get("/api/safety")
    def get_safety() -> dict[str, Any]:
        """Kill switch flag existence + RuntimeGuard-derived status."""
        kill_active = _kill_flag().exists()
        guard_status = "stopped" if kill_active else "ok"
        return {
            "kill_switch_active": kill_active,
            "guard_status": guard_status,
        }

    # ---------- Task 4.7: GET /api/events/tail ----------
    @app.get("/api/events/tail")
    async def events_tail() -> StreamingResponse:
        """SSE stream tailing audit_ledger.jsonl. Polls every 1 second."""
        stop_event = asyncio.Event()
        app.state.sse_stop_events.add(stop_event)

        async def gen() -> AsyncIterator[bytes]:
            try:
                async for chunk in _sse_event_stream(_ledger_path(), stop_event):
                    yield chunk
            finally:
                app.state.sse_stop_events.discard(stop_event)

        return StreamingResponse(
            gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    # ---------- Task 4.8: GET /api/health ----------
    @app.get("/api/health")
    def get_health() -> dict[str, Any]:
        """Combined health: dashboard (always ok), daemon, bot, safety."""
        daemon_hb = _read_json(_daemon_hb())
        daemon_age = _heartbeat_age_seconds(daemon_hb, "last_tick")
        if daemon_age is None:
            daemon = {"status": "unknown"}
        elif daemon_age > _HEARTBEAT_STALE_SECS:
            daemon = {
                "status": "stale",
                "last_tick": daemon_hb.get("last_tick") if daemon_hb else None,
                "stale_seconds": round(daemon_age, 1),
            }
        else:
            daemon = {
                "status": "ok",
                "last_tick": daemon_hb.get("last_tick") if daemon_hb else None,
            }

        bot_hb = _read_json(_bot_hb())
        bot_age = _heartbeat_age_seconds(bot_hb, "last_heartbeat")
        if bot_age is None:
            bot = {"status": "unknown"}
        elif bot_age > _HEARTBEAT_STALE_SECS:
            bot = {
                "status": "stale",
                "last_heartbeat": bot_hb.get("last_heartbeat") if bot_hb else None,
                "stale_seconds": round(bot_age, 1),
            }
        else:
            bot = {
                "status": "ok",
                "last_heartbeat": bot_hb.get("last_heartbeat") if bot_hb else None,
            }

        kill_active = _kill_flag().exists()
        safety = {"status": "stopped" if kill_active else "ok"}

        return {
            "dashboard": "ok",
            "daemon": daemon,
            "bot": bot,
            "safety": safety,
        }

    # ---------- Task 4.9: GET /api/posts ----------
    @app.get("/api/posts")
    def list_posts(limit: int = 20) -> list[dict[str, Any]]:
        """Posts from processed_posts.json with linked run_id where available."""
        data = _read_json(_posts_path()) or {}
        # Map post_id → run_id from runs.jsonl instructions (best effort).
        pid_to_run: dict[str, str] = {}
        for r in _read_jsonl(_runs_path()):
            for instr in r.get("instructions", []):
                iid = instr.get("instruction_id", "")
                if iid:
                    pid_to_run[iid] = r.get("run_id", "")
        out: list[dict[str, Any]] = []
        for post_id, meta in data.items():
            out.append({
                "post_id": post_id,
                "title": meta.get("title"),
                "timestamp": meta.get("ts"),
                "parsed": meta.get("parsed", meta.get("processed", False)),
                "run_id": pid_to_run.get(post_id),
            })
        out.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        return out[: max(0, limit)]

    # ---------- Task 4.10: GET /api/positions ----------
    @app.get("/api/positions")
    def get_positions() -> list[dict[str, Any]]:
        """Latest tick's positions from positions.db. Empty if DB missing."""
        return _positions_from_db(_positions_path())

    # ---------- Task 4.11: POST /api/kill-switch ----------
    @app.post("/api/kill-switch")
    def activate_kill_switch(
        x_kill_switch_secret: str | None = Header(default=None, alias="X-Kill-Switch-Secret"),
    ) -> dict[str, Any]:
        """Write kill_switch.flag if header secret matches env var."""
        expected = os.environ.get("DASHBOARD_KILL_SWITCH_SECRET")
        if not expected or x_kill_switch_secret != expected:
            raise HTTPException(status_code=403, detail="invalid kill-switch secret")
        _kill_flag().parent.mkdir(parents=True, exist_ok=True)
        _kill_flag().touch()
        return {"status": "kill_switch_activated"}

    # ---------- Task 4.12: GET / ----------
    @app.get("/")
    def root() -> FileResponse:
        """Serve the dashboard SPA."""
        index = static_dir / "index.html"
        if not index.exists():
            raise HTTPException(status_code=404, detail="index.html missing")
        return FileResponse(index, media_type="text/html")

    # Static assets (JS/CSS) — index.html itself is served by GET /.
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        """Signal all SSE streams to terminate."""
        for ev in list(app.state.sse_stop_events):
            ev.set()

    return app


# For `python -m src.dashboard` or `uvicorn src.dashboard.app:app`
def main() -> None:
    """Run the dashboard bound to 127.0.0.1 (Decision #11)."""
    import uvicorn

    runtime_dir = os.environ.get("RUNTIME_DIR", "runtime")
    app = create_app(runtime_dir)
    # ponytail: host=127.0.0.1 enforced — never 0.0.0.0 (network isolation)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
