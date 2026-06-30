"""Integration tests for the FastAPI dashboard (Group 4.14).

Covers all 11 routes, kill-switch auth (valid + invalid), SSE stream,
health stale detection, and positions-empty-when-DB-missing.
"""

from __future__ import annotations

import inspect
import json
import sqlite3
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.dashboard import create_app

# ---------- Fixtures ----------

@pytest.fixture
def runtime_dir(tmp_path: Path) -> Path:
    rt = tmp_path / "runtime"
    rt.mkdir(parents=True, exist_ok=True)
    return rt


@pytest.fixture
def client(runtime_dir: Path) -> TestClient:
    app = create_app(runtime_dir)
    return TestClient(app)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _st(dur_ms: int | None, skipped: bool = False) -> dict:
    """Build a single stage_timing entry."""
    return {
        "started_at": _iso(datetime.now(UTC)),
        "duration_ms": dur_ms,
        "skipped": skipped,
    }


def _sample_run(run_id: str = "2026-07-05-001-a1b2c3d4", outcome: str = "success") -> dict:
    return {
        "run_id": run_id,
        "started_at": _iso(datetime.now(UTC)),
        "ended_at": _iso(datetime.now(UTC) + timedelta(seconds=45)),
        "mode": "uat_confirm",
        "environment": "uat",
        "signals_processed": 1,
        "instructions": [
            {
                "instruction_id": "post-abc",
                "symbol": "NVDA",
                "action": "BUY",
                "outcome": "PLACED",
                "stage_timings": {
                    "detect": _st(500),
                    "parse": _st(2100),
                    "llm": _st(None, skipped=True),
                    "ta": _st(10000),
                    "sizing": _st(300),
                    "exec": _st(800),
                    "broker": _st(1200),
                },
            }
        ],
        "errors": [],
        "outcome": outcome,
    }


# ---------- Task 4.3: GET /api/runs ----------

class TestListRuns:
    def test_empty_returns_list(self, client: TestClient) -> None:
        r = client.get("/api/runs")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_summary_fields(self, runtime_dir: Path, client: TestClient) -> None:
        _write_jsonl(runtime_dir / "runs.jsonl", [_sample_run()])
        r = client.get("/api/runs")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        item = data[0]
        assert set(item.keys()) == {
            "run_id", "started_at", "ended_at", "outcome",
            "signals_processed", "orders_placed",
        }
        assert item["run_id"] == "2026-07-05-001-a1b2c3d4"
        assert item["outcome"] == "success"
        assert item["signals_processed"] == 1
        assert item["orders_placed"] == 1

    def test_limit_param(self, runtime_dir: Path, client: TestClient) -> None:
        records = [
            _sample_run(run_id=f"2026-07-05-{i:03d}-abc{i}")
            for i in range(1, 6)
        ]
        _write_jsonl(runtime_dir / "runs.jsonl", records)
        r = client.get("/api/runs?limit=2")
        assert len(r.json()) == 2
        # Most-recent-first (file order reversed)
        assert r.json()[0]["run_id"] == "2026-07-05-005-abc5"

    def test_most_recent_first(self, runtime_dir: Path, client: TestClient) -> None:
        records = [
            _sample_run(run_id="2026-07-05-001-old"),
            _sample_run(run_id="2026-07-05-002-new"),
        ]
        _write_jsonl(runtime_dir / "runs.jsonl", records)
        r = client.get("/api/runs")
        assert r.json()[0]["run_id"] == "2026-07-05-002-new"


# ---------- Task 4.4: GET /api/runs/{run_id} ----------

class TestGetRun:
    def test_404_when_missing(self, client: TestClient) -> None:
        r = client.get("/api/runs/nope")
        assert r.status_code == 404

    def test_returns_full_run_with_audit_events(
        self, runtime_dir: Path, client: TestClient
    ) -> None:
        run = _sample_run()
        _write_jsonl(runtime_dir / "runs.jsonl", [run])
        # Audit events: one matching, one not
        _write_jsonl(runtime_dir / "audit_ledger.jsonl", [
            {"event_id": "e1", "correlation_id": run["run_id"], "event_type": "RUN_STARTED"},
            {"event_id": "e2", "correlation_id": "other-run", "event_type": "RUN_STARTED"},
        ])
        r = client.get(f"/api/runs/{run['run_id']}")
        assert r.status_code == 200
        data = r.json()
        assert data["run_id"] == run["run_id"]
        assert "instructions" in data
        assert data["instructions"][0]["stage_timings"]["ta"]["duration_ms"] == 10000
        assert "audit_events" in data
        assert len(data["audit_events"]) == 1
        assert data["audit_events"][0]["event_id"] == "e1"


# ---------- Task 4.5: GET /api/metrics ----------

class TestMetrics:
    def test_empty_when_no_runs(self, client: TestClient) -> None:
        r = client.get("/api/metrics")
        assert r.status_code == 200
        data = r.json()
        for stage in ("detect", "parse", "llm", "ta", "sizing", "exec", "broker"):
            assert data["stages"][stage] == {"p50": 0.0, "p95": 0.0, "max": 0.0, "count": 0}

    def test_aggregates_stage_timings(self, runtime_dir: Path, client: TestClient) -> None:
        _write_jsonl(runtime_dir / "runs.jsonl", [_sample_run()])
        r = client.get("/api/metrics")
        data = r.json()["stages"]
        # Skipped stages excluded from count
        assert data["llm"]["count"] == 0
        assert data["detect"]["count"] == 1
        assert data["detect"]["max"] == 500.0
        assert data["detect"]["p50"] == 500.0
        assert data["ta"]["max"] == 10000.0


# ---------- Task 4.6: GET /api/safety ----------

class TestSafety:
    def test_no_kill_switch(self, client: TestClient) -> None:
        r = client.get("/api/safety")
        assert r.status_code == 200
        data = r.json()
        assert data == {"kill_switch_active": False, "guard_status": "ok"}

    def test_kill_switch_active(
        self, runtime_dir: Path, client: TestClient
    ) -> None:
        (runtime_dir / "kill_switch.flag").touch()
        r = client.get("/api/safety")
        data = r.json()
        assert data["kill_switch_active"] is True
        assert data["guard_status"] == "stopped"


# ---------- Task 4.7: GET /api/events/tail (SSE) ----------

class TestSSE:
    def test_route_registered_as_sse(self, runtime_dir: Path) -> None:
        """The /api/events/tail route exists and returns a StreamingResponse."""
        import asyncio

        from fastapi.responses import StreamingResponse

        app = create_app(runtime_dir)
        ledger = runtime_dir / "audit_ledger.jsonl"
        ledger.touch()
        route = next(r for r in app.routes if getattr(r, "path", "") == "/api/events/tail")
        endpoint = getattr(route, "endpoint")
        response = asyncio.run(endpoint())
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "text/event-stream"

    def test_event_generator_emits_appended_lines(
        self, runtime_dir: Path
    ) -> None:
        import asyncio

        from src.dashboard.app import _sse_event_stream

        ledger = runtime_dir / "audit_ledger.jsonl"
        ledger.touch()
        event = {
            "event_id": "ev1",
            "event_type": "TEST_EVENT",
            "correlation_id": "r1",
        }

        async def scenario() -> list[bytes]:
            stop = asyncio.Event()
            agen = _sse_event_stream(ledger, stop)
            out: list[bytes] = []

            def append_after_delay() -> None:
                time.sleep(0.3)
                with open(ledger, "a") as f:
                    f.write(json.dumps(event) + "\n")

            threading.Thread(target=append_after_delay, daemon=True).start()
            try:
                first = await asyncio.wait_for(agen.__anext__(), timeout=3.0)
                out.append(first)
            finally:
                stop.set()
            return out

        chunks = asyncio.run(scenario())
        assert len(chunks) == 1
        decoded = chunks[0].decode()
        assert decoded.startswith("data: ")
        assert "TEST_EVENT" in decoded
        assert '"correlation_id": "r1"' in decoded


# ---------- Task 4.8: GET /api/health ----------

class TestHealth:
    def test_dashboard_always_ok(self, client: TestClient) -> None:
        r = client.get("/api/health")
        data = r.json()
        assert data["dashboard"] == "ok"
        assert "daemon" in data
        assert "bot" in data
        assert "safety" in data

    def test_daemon_ok_when_fresh(
        self, runtime_dir: Path, client: TestClient
    ) -> None:
        (runtime_dir / "daemon_heartbeat.json").write_text(json.dumps({
            "last_tick": _iso(datetime.now(UTC)),
            "pid": 123,
            "status": "ok",
        }))
        r = client.get("/api/health")
        daemon = r.json()["daemon"]
        assert daemon["status"] == "ok"
        assert daemon["last_tick"] is not None

    def test_daemon_stale_when_old(
        self, runtime_dir: Path, client: TestClient
    ) -> None:
        old = datetime.now(UTC) - timedelta(seconds=300)
        (runtime_dir / "daemon_heartbeat.json").write_text(json.dumps({
            "last_tick": _iso(old),
            "pid": 123,
            "status": "ok",
        }))
        r = client.get("/api/health")
        daemon = r.json()["daemon"]
        assert daemon["status"] == "stale"
        assert daemon["stale_seconds"] >= 290

    def test_bot_health(self, runtime_dir: Path, client: TestClient) -> None:
        (runtime_dir / "bot_heartbeat.json").write_text(json.dumps({
            "last_heartbeat": _iso(datetime.now(UTC)),
            "pid": 456,
            "status": "ok",
        }))
        r = client.get("/api/health")
        bot = r.json()["bot"]
        assert bot["status"] == "ok"


# ---------- Task 4.9: GET /api/posts ----------

class TestPosts:
    def test_empty_when_no_store(self, client: TestClient) -> None:
        r = client.get("/api/posts")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_posts(
        self, runtime_dir: Path, client: TestClient
    ) -> None:
        (runtime_dir / "processed_posts.json").write_text(json.dumps({
            "post-1": {"title": "First", "ts": _iso(datetime.now(UTC)), "parsed": True},
            "post-2": {"title": "Second", "ts": _iso(datetime.now(UTC) - timedelta(hours=1))},
        }))
        r = client.get("/api/posts")
        data = r.json()
        assert len(data) == 2
        ids = {p["post_id"] for p in data}
        assert ids == {"post-1", "post-2"}
        # Sorted most-recent-first
        assert data[0]["post_id"] == "post-1"


# ---------- Task 4.10: GET /api/positions ----------

class TestPositions:
    def test_empty_when_no_db(self, client: TestClient) -> None:
        r = client.get("/api/positions")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_latest_tick(
        self, runtime_dir: Path, client: TestClient
    ) -> None:
        db = runtime_dir / "positions.db"
        conn = sqlite3.connect(db)
        conn.execute("""
            CREATE TABLE position_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                tick_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                position_qty REAL NOT NULL,
                market_value REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                pnl_pct REAL NOT NULL
            )
        """)
        old_tick = "2026-07-05T10:00:00Z"
        new_tick = "2026-07-05T11:00:00Z"
        conn.executemany(
            "INSERT INTO position_snapshots (run_id, tick_at, symbol, position_qty, "
            "market_value, unrealized_pnl, pnl_pct) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("r1", old_tick, "OLD", 1.0, 10.0, 0.0, 0.0),
                ("r2", new_tick, "NVDA", 10.0, 1000.0, 50.0, 5.0),
                ("r2", new_tick, "AMD", 5.0, 500.0, -10.0, -2.0),
            ],
        )
        conn.commit()
        conn.close()

        r = client.get("/api/positions")
        data = r.json()
        assert len(data) == 2
        syms = {p["symbol"] for p in data}
        assert syms == {"NVDA", "AMD"}
        # OLD tick row excluded
        assert all(p["symbol"] != "OLD" for p in data)


# ---------- Task 4.11: POST /api/kill-switch ----------

class TestKillSwitch:
    def test_403_when_no_env(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DASHBOARD_KILL_SWITCH_SECRET", raising=False)
        r = client.post("/api/kill-switch", headers={"X-Kill-Switch-Secret": "anything"})
        assert r.status_code == 403

    def test_403_when_wrong_secret(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DASHBOARD_KILL_SWITCH_SECRET", "correct")
        r = client.post("/api/kill-switch", headers={"X-Kill-Switch-Secret": "wrong"})
        assert r.status_code == 403

    def test_403_when_missing_header(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DASHBOARD_KILL_SWITCH_SECRET", "correct")
        r = client.post("/api/kill-switch")
        assert r.status_code == 403

    def test_activates_with_valid_secret(
        self, runtime_dir: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DASHBOARD_KILL_SWITCH_SECRET", "correct")
        r = client.post("/api/kill-switch", headers={"X-Kill-Switch-Secret": "correct"})
        assert r.status_code == 200
        assert r.json() == {"status": "kill_switch_activated"}
        assert (runtime_dir / "kill_switch.flag").exists()
        # Now safety should reflect it
        safety = client.get("/api/safety").json()
        assert safety["kill_switch_active"] is True


# ---------- Task 4.12: GET / ----------

class TestRoot:
    def test_serves_html(self, client: TestClient) -> None:
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        assert "Christian Bot Dashboard" in r.text


# ---------- Task 4.13: bind 127.0.0.1 ----------

class TestBinding:
    def test_app_factory_accepts_runtime_dir(self, tmp_path: Path) -> None:
        rt = tmp_path / "rt"
        app = create_app(rt)
        assert app.title == "Christian Bot Dashboard"
        assert rt.exists()

    def test_main_uses_localhost(self) -> None:
        """Inspect that main() is configured for 127.0.0.1 — verified by source grep."""
        import src.dashboard.app as mod

        src = inspect.getsource(mod.main)
        assert 'host="127.0.0.1"' in src
        # Confirm 0.0.0.0 (as a host binding) is not used. Allow it inside string
        # literals/comments only by checking the uvicorn.run call line.
        assert "uvicorn.run(app, host=\"127.0.0.1\"" in src
