"""Poll daemon — 60s tick loop wrapping ``poll_once`` with operational safety.

Implements the M2 requirements from
``openspec/changes/production-deploy-scheduling-dashboard``:

* Reentrancy lock via ``fcntl.flock`` on ``runtime/daemon.lock`` (Linux
  primary; ``msvcrt`` fallback on Windows).
* Heartbeat written every tick — even on error ticks — to
  ``runtime/daemon_heartbeat.json``.
* Circuit breaker: 5 consecutive failures → ``runtime/kill_switch.flag`` +
  optional ``on_circuit_break`` callback (Telegram wiring is M3's job) +
  exit.
* Dead-man switch readiness: heartbeat is always written; the 120s age
  threshold is checked externally (Docker healthcheck / dashboard).
* Tick-abort: SIGTERM handler sets a ``threading.Event`` the tick loop
  polls; the daemon records an aborted run, releases the lock, and exits
  within 15s.
* Startup gate: refuses to run when ``runtime/kill_switch.flag`` exists
  (invokes ``RuntimeGuard.activate_stop``); runs ``PRAGMA
  integrity_check`` on the runtime SQLite DBs; purges ``runs-*.jsonl``
  older than 13 months.
* Positions snapshot: every tick pulls ``provider.get_snapshot(account_id)``
  and writes the rows to ``runtime/positions.db`` (best-effort, never
  crashes a tick on broker error).
* JSONL monthly rotation: ``runs-YYYY-MM.jsonl`` rotates on month boundary.

This module is intentionally dependency-light — only stdlib plus the
existing project modules. Telegram wiring is injected via ``on_circuit_break``.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sqlite3
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from src.analyzer.parser_crosscheck import CrossCheckParser
from src.config.settings import RuntimeConfig
from src.ingestion.poll import poll_once
from src.ingestion.seen_store import ProcessedPostStore
from src.ops.run_record import RunRecorder
from src.safety.runtime_guard import RuntimeGuard

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants (mirror design.md §3, §10)
# ---------------------------------------------------------------------------

DEFAULT_TICK_INTERVAL_SECONDS = 60
DEFAULT_CIRCUIT_BREAKER_THRESHOLD = 5
JSONL_RETENTION_DAYS = 395  # ~13 months
RUNTIME_DIR = Path("runtime")

# SQLite DBs to integrity-check at startup (best-effort — only if present).
STARTUP_INTEGRITY_DBS = ("shadow_state.db", "positions.db")

# Cross-platform file locking. Linux is the primary target; Windows gets a
# best-effort ``msvcrt`` fallback. The ImportError guard keeps the module
# importable on either platform. Both bindings are typed as ``Any`` so the
# runtime ``None``/imported-module values flow through Pyright without
# needing per-attribute ``# type: ignore`` annotations at every call site.
_fcntl: Any = None
_msvcrt: Any = None
_HAS_FCNTL = False
_HAS_MSVCRT = False

try:
    import fcntl as _fcntl_mod  # POSIX only

    _fcntl = _fcntl_mod
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover — Windows path
    try:
        import msvcrt as _msvcrt_mod  # Windows only

        _msvcrt = _msvcrt_mod
        _HAS_MSVCRT = True
    except ImportError:  # pragma: no cover — neither available
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """ISO-8601 UTC timestamp with timezone suffix."""
    return datetime.now(UTC).isoformat()


def _ensure_runtime_dir(runtime_dir: Path) -> None:
    runtime_dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# PollDaemon
# ---------------------------------------------------------------------------


class PollDaemon:
    """Long-running poller that ticks ``poll_once`` every 60 seconds.

    Construct via the constructor; call :meth:`run` to start the tick loop.
    The loop exits when SIGTERM is received (setting ``stop_event``), when
    the circuit breaker trips, or when :meth:`shutdown` is invoked.

    All operational artifacts live under ``runtime_dir`` (default ``runtime``):

    * ``daemon.lock`` — exclusive flock held for the daemon lifetime.
    * ``daemon_heartbeat.json`` — overwritten every tick.
    * ``kill_switch.flag`` — written when the circuit breaker trips.
    * ``runs-YYYY-MM.jsonl`` — monthly-rotated run records.
    * ``positions.db`` — per-tick broker positions snapshot.
    """

    def __init__(
        self,
        *,
        pipeline: Any,
        parser: CrossCheckParser,
        substack_client: Any,
        seen_store: ProcessedPostStore,
        account_id: str,
        config: RuntimeConfig,
        guard: RuntimeGuard,
        run_recorder: RunRecorder,
        provider: Any | None = None,
        tick_interval_seconds: int = DEFAULT_TICK_INTERVAL_SECONDS,
        circuit_breaker_threshold: int = DEFAULT_CIRCUIT_BREAKER_THRESHOLD,
        on_circuit_break: Callable[[], None] | None = None,
        runs_dir: str | Path = RUNTIME_DIR,
        deepseek_api_key: str = "",
        deepseek_base_url: str = "https://api.deepseek.com",
        publication_ids: list[str] | None = None,
        post_limit: int = 10,
    ) -> None:
        self.pipeline = pipeline
        self.parser = parser
        self.substack_client = substack_client
        self.seen_store = seen_store
        self.account_id = account_id
        self.config = config
        self.guard = guard
        self.run_recorder = run_recorder
        self.provider = provider
        self.tick_interval_seconds = tick_interval_seconds
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.on_circuit_break = on_circuit_break
        self.publication_ids = publication_ids
        self.post_limit = post_limit

        self.runtime_dir = Path(runs_dir)
        _ensure_runtime_dir(self.runtime_dir)

        # Filesystem paths — resolved once for clarity.
        self._lock_path = self.runtime_dir / "daemon.lock"
        self._heartbeat_path = self.runtime_dir / "daemon_heartbeat.json"
        self._kill_switch_path = self.runtime_dir / "kill_switch.flag"
        self._positions_db = self.runtime_dir / "positions.db"

        # Daemon state — guarded by ``_state_lock``.
        self._state_lock = threading.Lock()
        self._lock_fd: Any = None
        self._consecutive_failures = 0
        self._active_run_id: str | None = None
        self._sigterm_received = False

        # Shutdown coordination. ``stop_event`` is set by the SIGTERM handler
        # OR by :meth:`shutdown`; the tick loop polls it.
        self.stop_event = threading.Event()

        # Cache the previous SIGTERM handler so we can restore it on exit
        # (only set during :meth:`run`).
        self._prev_sigterm: Any = None

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main daemon loop.

        Performs startup gates (kill switch / flock / SQLite integrity /
        JSONL purge), registers the SIGTERM handler, then ticks every
        ``tick_interval_seconds`` until ``stop_event`` is set.
        """
        # 1. Kill-switch flag check — refuse to start if armed.
        if self._check_kill_switch():
            self.guard.activate_stop("kill_switch_flag_present")
            _logger.error("Refusing to start: kill_switch.flag present")
            raise SystemExit(
                "Refusing to start: runtime/kill_switch.flag exists. "
                "Remove it after diagnosing the issue."
            )

        # 2. Acquire exclusive lock — refuse dual-start.
        self._acquire_lock()

        try:
            # 3. SQLite integrity check.
            if not self._check_sqlite_integrity():
                raise SystemExit(
                    "Refusing to start: SQLite integrity check failed. "
                    "Inspect runtime/*.db before restarting."
                )

            # 4. JSONL purge (>13 months).
            self._purge_old_jsonl()

            # 5. Rotate if the active file's month is stale.
            self._rotate_jsonl_if_needed()

            # 6. Register SIGTERM handler.
            self._register_sigterm_handler()

            _logger.info(
                "PollDaemon starting (pid=%s, tick=%ss, breaker=%s)",
                os.getpid(),
                self.tick_interval_seconds,
                self.circuit_breaker_threshold,
            )

            # 7. Tick loop.
            while not self.stop_event.is_set():
                try:
                    self._tick()
                    self._consecutive_failures = 0
                except Exception:
                    self._on_tick_failure()
                    if self._consecutive_failures >= self.circuit_breaker_threshold:
                        self._trip_circuit_breaker()
                        break
                finally:
                    # Heartbeat always written, even on error ticks (task 2.6).
                    status = (
                        "error" if self._consecutive_failures > 0 else "ok"
                    )
                    self._write_heartbeat(status)

                # Wait the tick interval but remain responsive to SIGTERM.
                if self.stop_event.wait(self.tick_interval_seconds):
                    break
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Release the lock and restore signal handlers.

        Idempotent: safe to call from :meth:`run`'s ``finally`` block and
        again externally.
        """
        # Restore previous SIGTERM handler (if any).
        if self._prev_sigterm is not None:
            try:
                signal.signal(signal.SIGTERM, self._prev_sigterm)
            except (ValueError, OSError):  # pragma: no cover — non-main thread
                pass
            self._prev_sigterm = None

        # Finalize any in-flight run as aborted.
        with self._state_lock:
            run_id = self._active_run_id
            self._active_run_id = None
            sigterm = self._sigterm_received
        if run_id is not None:
            reason = "SIGTERM_ABORT" if sigterm else "SHUTDOWN"
            try:
                self.run_recorder.record_error(
                    stage="tick", message=f"Aborted ({reason})"
                )
                self.run_recorder.end_run(outcome="aborted", reason=reason)
            except Exception:  # pragma: no cover — best-effort cleanup
                _logger.exception("Failed to finalize aborted run on shutdown")

        # Release flock.
        self._release_lock()

    # ------------------------------------------------------------------
    # Single tick
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """Run one poll → pipeline → record → positions-snapshot → heartbeat."""
        run_id = self.run_recorder.start_run(
            mode=self.config.mode,
            environment=self.config.environment,
        )
        with self._state_lock:
            self._active_run_id = run_id

        try:
            outcomes = poll_once(
                client=self.substack_client,
                parser=self.parser,
                pipeline=self.pipeline,
                seen_store=self.seen_store,
                account_id=self.account_id,
                publication_ids=self.publication_ids,
                limit=self.post_limit,
            )

            for outcome in outcomes:
                instruction_id = getattr(
                    outcome, "instruction_id", f"{run_id}:unknown"
                )
                symbol = getattr(outcome, "symbol", "")
                action = getattr(outcome, "action", "")
                final = getattr(outcome, "outcome", "") or getattr(
                    outcome, "status", ""
                )
                self.run_recorder.record_instruction_outcome(
                    instruction_id=str(instruction_id),
                    symbol=str(symbol),
                    action=str(action),
                    outcome=str(final),
                )

            self.run_recorder.end_run(outcome="success")
        except BaseException as exc:  # noqa: BLE001 — re-raise after bookkeeping
            # Re-raise KeyboardInterrupt/SystemExit so the tick loop's except
            # clauses (or Python itself) handle them.
            try:
                self.run_recorder.record_error(
                    stage="tick", message=f"{type(exc).__name__}: {exc}"
                )
                self.run_recorder.end_run(outcome="error")
            except Exception:  # pragma: no cover — best-effort bookkeeping
                _logger.exception("Failed to record error outcome")
            raise
        finally:
            with self._state_lock:
                self._active_run_id = None

            # Positions snapshot is best-effort — never let it mask the tick's
            # real outcome. Always attempt, even after a poll failure.
            self._snapshot_positions(run_id)

    # ------------------------------------------------------------------
    # Startup gates
    # ------------------------------------------------------------------

    def _check_kill_switch(self) -> bool:
        """Return True if ``runtime/kill_switch.flag`` exists."""
        return self._kill_switch_path.exists()

    def _acquire_lock(self) -> Any:
        """Acquire an exclusive non-blocking lock on ``runtime/daemon.lock``.

        Uses ``fcntl.flock(LOCK_EX | LOCK_NB)`` on POSIX; falls back to
        ``msvcrt.locking`` on Windows. Exits with a clear message if held.
        """
        # Create the lock file if missing so flock/locking has something to
        # lock against. Opening in write mode is sufficient.
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o644)

        if _HAS_FCNTL:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
            except OSError as exc:
                os.close(fd)
                raise SystemExit(
                    f"Refusing to start: {self._lock_path} is already held "
                    f"by another daemon process ({exc})."
                ) from exc
        elif _HAS_MSVCRT:  # pragma: no cover — Windows path
            try:
                _msvcrt_locking_nb(fd)
            except OSError as exc:
                os.close(fd)
                raise SystemExit(
                    f"Refusing to start: {self._lock_path} is already held "
                    f"by another daemon process ({exc})."
                ) from exc
        else:  # pragma: no cover — no platform lock available
            _logger.warning(
                "Neither fcntl nor msvcrt available — daemon lock is a no-op"
            )

        self._lock_fd = fd
        return fd

    def _release_lock(self) -> None:
        """Release the flock and close the lock file descriptor."""
        fd = self._lock_fd
        if fd is None:
            return
        try:
            if _HAS_FCNTL:
                try:
                    _fcntl.flock(fd, _fcntl.LOCK_UN)
                except OSError:
                    pass
            elif _HAS_MSVCRT:  # pragma: no cover — Windows path
                try:
                    os.lseek(fd, 0, os.SEEK_SET)
                    _msvcrt_unlock(fd)
                except OSError:
                    pass
        finally:
            try:
                os.close(fd)
            except OSError:
                pass
            self._lock_fd = None

    def _check_sqlite_integrity(self) -> bool:
        """Run ``PRAGMA integrity_check`` on the runtime SQLite DBs.

        Returns True if every existing DB reports ``ok``. Missing DBs are
        skipped (the daemon will create ``positions.db`` itself; others are
        optional). Returns False on any non-``ok`` result or exception.
        """
        for name in STARTUP_INTEGRITY_DBS:
            db_path = self.runtime_dir / name
            if not db_path.exists():
                continue
            try:
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                try:
                    row = conn.execute("PRAGMA integrity_check").fetchone()
                finally:
                    conn.close()
                result = row[0] if row else ""
                if str(result).lower() != "ok":
                    _logger.error(
                        "SQLite integrity_check on %s returned: %s", name, result
                    )
                    return False
            except sqlite3.Error as exc:
                _logger.error("SQLite integrity_check on %s failed: %s", name, exc)
                return False
        return True

    def _purge_old_jsonl(self) -> None:
        """Delete ``runs-*.jsonl`` files older than 13 months (395 days)."""
        threshold = time.time() - JSONL_RETENTION_DAYS * 86400
        for path in self.runtime_dir.glob("runs-*.jsonl"):
            try:
                if path.stat().st_mtime < threshold:
                    path.unlink()
                    _logger.info("Purged old JSONL: %s", path)
            except OSError:
                _logger.exception("Failed to purge %s", path)

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    def _write_heartbeat(self, status: str) -> None:
        """Overwrite ``runtime/daemon_heartbeat.json`` with current state.

        Writes happen every tick (success or failure) — the file's mtime is
        the dead-man-switch signal checked externally.
        """
        payload = {
            "last_tick": _utc_now_iso(),
            "pid": os.getpid(),
            "status": status,
        }
        try:
            self._heartbeat_path.write_text(
                json.dumps(payload, ensure_ascii=False)
            )
        except OSError:
            _logger.exception("Failed to write heartbeat")

    # ------------------------------------------------------------------
    # Circuit breaker
    # ------------------------------------------------------------------

    def _on_tick_failure(self) -> None:
        """Increment failure counter; log + (optionally) record in run record."""
        with self._state_lock:
            self._consecutive_failures += 1
            count = self._consecutive_failures
        _logger.warning(
            "Tick failed (%d/%d consecutive)",
            count,
            self.circuit_breaker_threshold,
        )

    def _trip_circuit_breaker(self) -> None:
        """Engage the kill switch: write flag, fire callback, log, return."""
        _logger.critical(
            "Circuit breaker tripped after %d consecutive failures — "
            "writing kill_switch.flag",
            self._consecutive_failures,
        )
        try:
            self._kill_switch_path.touch()
        except OSError:
            _logger.exception("Failed to write kill_switch.flag")

        if self.on_circuit_break is not None:
            try:
                self.on_circuit_break()
            except Exception:  # noqa: BLE001 — alert must not mask breaker
                _logger.exception("on_circuit_break callback raised")

    # ------------------------------------------------------------------
    # SIGTERM / tick-abort
    # ------------------------------------------------------------------

    def _register_sigterm_handler(self) -> None:
        """Register the SIGTERM handler that sets ``stop_event``.

        Stored as the previous handler so :meth:`shutdown` can restore it.
        ``signal.signal`` only works from the main thread; the daemon is
        always run from the main thread.
        """
        self._prev_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def _handle_sigterm(self, signum: int, frame: Any) -> None:  # noqa: ARG002
        """SIGTERM handler: set ``stop_event`` so the tick loop wakes and exits.

        The tick loop's ``finally`` block finalizes the in-flight run as
        aborted (``SIGTERM_ABORT``), writes a final heartbeat, and releases
        the flock — all within the 15s shutdown budget.

        We intentionally do NOT propagate SIGTERM to the daemon's own process
        group here: that would re-enter this handler recursively. The TA
        subprocess kill is the orchestrator's responsibility (task 2.11 — the
        gateway's ``stop_event`` check). For orphan safety, Docker's
        ``stop_grace_period`` provides the SIGKILL backstop.
        """
        _logger.warning("SIGTERM received — initiating graceful shutdown")
        self.stop_event.set()
        self._sigterm_received = True

    # ------------------------------------------------------------------
    # Positions snapshot (task 2.14)
    # ------------------------------------------------------------------

    def _snapshot_positions(self, run_id: str) -> None:
        """Pull broker positions and append rows to ``runtime/positions.db``.

        Best-effort: never raises. Broker errors are logged and swallowed
        so they cannot mask the real tick outcome.
        """
        if self.provider is None:
            return
        try:
            snapshot = self.provider.get_snapshot(self.account_id)
        except Exception as exc:  # noqa: BLE001 — broker calls are best-effort
            _logger.warning("Positions snapshot skipped: %s", exc)
            return

        tick_at = _utc_now_iso()
        rows = [
            (
                run_id,
                tick_at,
                pos.symbol,
                float(pos.quantity),
                float(pos.market_value_usd),
                _unrealized_pnl(pos),
                _pnl_pct(pos),
            )
            for pos in snapshot.positions
        ]
        if not rows:
            return

        conn = sqlite3.connect(self._positions_db)
        try:
            conn.executescript(_POSITIONS_SCHEMA)
            conn.executemany(
                "INSERT INTO position_snapshots "
                "(run_id, tick_at, symbol, position_qty, market_value, "
                "unrealized_pnl, pnl_pct) VALUES (?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        except sqlite3.Error as exc:
            _logger.warning("Positions snapshot write failed: %s", exc)
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # JSONL rotation (task 2.15)
    # ------------------------------------------------------------------

    def _rotate_jsonl_if_needed(self) -> None:
        """Rotate ``runs.jsonl`` → ``runs-YYYY-MM.jsonl`` on month boundary.

        Strategy: if ``runs.jsonl`` exists and its mtime month differs from
        the current month, rename it to ``runs-{mtime_month}.jsonl`` so the
        next write starts a fresh file. We compare by ``strftime("%Y-%m")``
        of the mtime vs ``datetime.now(UTC)``.
        """
        active = self.runtime_dir / "runs.jsonl"
        if not active.exists() or active.stat().st_size == 0:
            return

        file_month = datetime.fromtimestamp(
            active.stat().st_mtime, tz=UTC
        ).strftime("%Y-%m")
        current_month = datetime.now(UTC).strftime("%Y-%m")
        if file_month == current_month:
            return

        target = self.runtime_dir / f"runs-{file_month}.jsonl"
        try:
            active.rename(target)
            _logger.info("Rotated runs.jsonl → %s", target.name)
        except OSError:
            _logger.exception("Failed to rotate runs.jsonl")


# ---------------------------------------------------------------------------
# Module-level constants + helpers
# ---------------------------------------------------------------------------


_POSITIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS position_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    tick_at TEXT NOT NULL,
    symbol TEXT NOT NULL,
    position_qty REAL NOT NULL,
    market_value REAL NOT NULL,
    unrealized_pnl REAL NOT NULL,
    pnl_pct REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshots_tick ON position_snapshots(tick_at);
"""


def _unrealized_pnl(pos: Any) -> float:
    """Best-effort unrealized P&L — falls back to 0 when cost basis is missing."""
    qty = float(getattr(pos, "quantity", 0) or 0)
    if qty == 0:
        return 0.0
    market = float(getattr(pos, "market_value_usd", 0) or 0)
    avg_cost = float(getattr(pos, "avg_cost", 0) or 0)
    return market - avg_cost * qty


def _pnl_pct(pos: Any) -> float:
    """Best-effort P&L percentage — 0 when cost basis is missing or zero."""
    avg_cost = float(getattr(pos, "avg_cost", 0) or 0)
    if avg_cost <= 0:
        return 0.0
    pnl = _unrealized_pnl(pos)
    cost_basis = avg_cost * float(getattr(pos, "quantity", 0) or 0)
    if cost_basis <= 0:
        return 0.0
    return (pnl / cost_basis) * 100.0


def _msvcrt_locking_nb(fd: int) -> None:
    """Acquire a non-blocking exclusive lock on *fd* via msvcrt.

    Locks the first byte; ``msvcrt.LK_NBLCK`` fails immediately if held.
    Raises ``OSError`` (errno=EDEADLK/EACCES) on contention.
    """
    _msvcrt.locking(fd, _msvcrt.LK_NBLCK, 1)  # pragma: no cover — Windows only


def _msvcrt_unlock(fd: int) -> None:
    """Release the msvcrt lock acquired by :func:`_msvcrt_locking_nb`."""
    _msvcrt.locking(fd, _msvcrt.LK_UNLCK, 1)  # pragma: no cover — Windows only
