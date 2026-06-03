"""SQLite-backed durable work queue."""

import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Optional

from src.state.models import Job


class DuplicateKeyError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class WorkQueue:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS work_queue (
                    job_id          TEXT PRIMARY KEY,
                    job_type        TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE,
                    payload         TEXT NOT NULL,
                    status          TEXT NOT NULL DEFAULT 'pending',
                    attempt_count   INTEGER NOT NULL DEFAULT 0,
                    leased_by       TEXT,
                    lease_expires_at TEXT,
                    next_retry_at   TEXT,
                    last_error      TEXT,
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL
                )
                """
            )

    def enqueue(self, job_type: str, idempotency_key: str, payload: dict) -> str:
        job_id = str(uuid.uuid4())
        now = _now_iso()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO work_queue
                        (job_id, job_type, idempotency_key, payload, status,
                         attempt_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'pending', 0, ?, ?)
                    """,
                    (job_id, job_type, idempotency_key, json.dumps(payload), now, now),
                )
        except sqlite3.IntegrityError:
            raise DuplicateKeyError(
                f"Duplicate idempotency_key: {idempotency_key}"
            )
        return job_id

    def lease(self, worker_id: str, ttl_seconds: int = 300) -> Optional[Job]:
        if ttl_seconds < 0:
            raise ValueError(f"ttl_seconds must be non-negative, got {ttl_seconds}")
        now = datetime.now(UTC)
        now_iso = now.isoformat()
        expires_iso = (now + timedelta(seconds=ttl_seconds)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT * FROM work_queue
                WHERE (status = 'pending'
                       AND (next_retry_at IS NULL OR next_retry_at <= ?))
                   OR (status = 'leased'
                       AND lease_expires_at IS NOT NULL
                       AND lease_expires_at <= ?)
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (now_iso, now_iso),
            ).fetchone()

            if row is None:
                return None

            conn.execute(
                """
                UPDATE work_queue
                SET status = 'leased',
                    leased_by = ?,
                    lease_expires_at = ?,
                    updated_at = ?
                WHERE job_id = ?
                  AND (status = 'pending' OR status = 'leased')
                """,
                (worker_id, expires_iso, now_iso, row["job_id"]),
            )

            # Re-read to get post-update state
            row = conn.execute(
                "SELECT * FROM work_queue WHERE job_id = ?", (row["job_id"],)
            ).fetchone()

        return self._row_to_job(row)

    def ack(self, job_id: str) -> None:
        now = _now_iso()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE work_queue
                SET status = 'completed', updated_at = ?
                WHERE job_id = ?
                """,
                (now, job_id),
            )

    def retry_after(self, job_id: str, delay_seconds: int, reason: str) -> None:
        now = datetime.now(UTC)
        retry_at = (now + timedelta(seconds=delay_seconds)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE work_queue
                SET status = 'pending',
                    next_retry_at = ?,
                    last_error = ?,
                    attempt_count = attempt_count + 1,
                    leased_by = NULL,
                    lease_expires_at = NULL,
                    updated_at = ?
                WHERE job_id = ?
                  AND status NOT IN ('dead_lettered', 'completed')
                """,
                (retry_at, reason, now.isoformat(), job_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(
                    f"Cannot retry job {job_id}: job is in a terminal state"
                )

    def dead_letter(self, job_id: str, reason: str) -> None:
        now = _now_iso()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE work_queue
                SET status = 'dead_lettered',
                    last_error = ?,
                    leased_by = NULL,
                    lease_expires_at = NULL,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (reason, now, job_id),
            )

    def get(self, job_id: str) -> Optional[Job]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM work_queue WHERE job_id = ?", (job_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        return Job(
            job_id=row["job_id"],
            job_type=row["job_type"],
            idempotency_key=row["idempotency_key"],
            payload=json.loads(row["payload"]),
            status=row["status"],
            attempt_count=row["attempt_count"],
            leased_by=row["leased_by"],
            lease_expires_at=row["lease_expires_at"],
            next_retry_at=row["next_retry_at"],
            last_error=row["last_error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
