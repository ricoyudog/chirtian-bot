"""SQLite-backed observation state store."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Optional

from src.config.settings import RuntimeConfig


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ObservationStateStore:
    """Persist observation period state across restarts."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS observation_state (
                    observation_id   TEXT PRIMARY KEY,
                    started_at       TEXT NOT NULL,
                    ended_at         TEXT,
                    status           TEXT NOT NULL DEFAULT 'active',
                    signals_processed INTEGER NOT NULL DEFAULT 0,
                    config_snapshot  TEXT NOT NULL DEFAULT '{}'
                )
                """
            )

    def start(self, config: Optional[RuntimeConfig] = None) -> str:
        """Start a new observation period. Returns observation_id."""
        observation_id = str(uuid.uuid4())
        now = _now_iso()
        config_snapshot = "{}"
        if config is not None:
            config_snapshot = json.dumps(config.model_dump())

        with sqlite3.connect(self.db_path) as conn:
            # Ensure only one active observation at a time
            active = conn.execute(
                "SELECT observation_id FROM observation_state WHERE status = 'active'"
            ).fetchone()
            if active:
                raise RuntimeError(
                    f"Observation {active[0]} is already active. Stop it first."
                )

            conn.execute(
                """
                INSERT INTO observation_state
                    (observation_id, started_at, status, signals_processed, config_snapshot)
                VALUES (?, ?, 'active', 0, ?)
                """,
                (observation_id, now, config_snapshot),
            )
        return observation_id

    def stop(self, observation_id: Optional[str] = None) -> dict:
        """Stop an observation period. Returns the final state."""
        now = _now_iso()
        with sqlite3.connect(self.db_path) as conn:
            if observation_id is None:
                row = conn.execute(
                    "SELECT observation_id FROM observation_state WHERE status = 'active'"
                ).fetchone()
                if row is None:
                    raise RuntimeError("No active observation to stop.")
                observation_id = row[0]

            state = self.get(observation_id)
            if state is None:
                raise RuntimeError(f"Observation {observation_id} not found.")
            if state["status"] != "active":
                raise RuntimeError(f"Observation {observation_id} is not active.")

            new_status = "completed"
            if self._is_insufficient_signals(state):
                new_status = "insufficient_signals"

            conn.execute(
                """
                UPDATE observation_state
                SET ended_at = ?, status = ?
                WHERE observation_id = ?
                """,
                (now, new_status, observation_id),
            )

        return self.get(observation_id)

    def increment_signals(self, observation_id: Optional[str] = None) -> int:
        """Increment processed signal count. Returns new count."""
        with sqlite3.connect(self.db_path) as conn:
            if observation_id is None:
                row = conn.execute(
                    "SELECT observation_id FROM observation_state WHERE status = 'active'"
                ).fetchone()
                if row is None:
                    raise RuntimeError("No active observation.")
                observation_id = row[0]

            conn.execute(
                """
                UPDATE observation_state
                SET signals_processed = signals_processed + 1
                WHERE observation_id = ?
                """,
                (observation_id,),
            )

        state = self.get(observation_id)
        return state["signals_processed"]

    def get(self, observation_id: str) -> Optional[dict]:
        """Get observation state by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM observation_state WHERE observation_id = ?",
                (observation_id,),
            ).fetchone()

        if row is None:
            return None
        return {
            "observation_id": row["observation_id"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "status": row["status"],
            "signals_processed": row["signals_processed"],
            "config_snapshot": json.loads(row["config_snapshot"]),
        }

    def get_active(self) -> Optional[dict]:
        """Get the currently active observation, if any."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM observation_state WHERE status = 'active'"
            ).fetchone()

        if row is None:
            return None
        return {
            "observation_id": row["observation_id"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "status": row["status"],
            "signals_processed": row["signals_processed"],
            "config_snapshot": json.loads(row["config_snapshot"]),
        }

    def should_extend(self, min_signals: int = 10) -> bool:
        """Check if observation period needs extension (1 week passed, insufficient signals)."""
        state = self.get_active()
        if state is None:
            return False

        started = datetime.fromisoformat(state["started_at"])
        now = datetime.now(UTC)
        one_week = timedelta(weeks=1)
        four_weeks = timedelta(weeks=4)

        if now - started < one_week:
            return False  # Not even 1 week yet

        if now - started >= four_weeks:
            return False  # Max duration reached

        return state["signals_processed"] < min_signals

    def is_max_duration_reached(self) -> bool:
        """Check if 4-week maximum has been reached."""
        state = self.get_active()
        if state is None:
            return False

        started = datetime.fromisoformat(state["started_at"])
        now = datetime.now(UTC)
        return (now - started) >= timedelta(weeks=4)

    def _is_insufficient_signals(self, state: dict, min_signals: int = 10) -> bool:
        started = datetime.fromisoformat(state["started_at"])
        now = datetime.now(UTC)
        one_week_passed = (now - started) >= timedelta(weeks=1)
        return one_week_passed and state["signals_processed"] < min_signals
