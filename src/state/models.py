"""Data models for the state layer."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Job:
    job_id: str
    job_type: str
    idempotency_key: str
    payload: dict[str, Any]
    status: str = "pending"
    attempt_count: int = 0
    leased_by: Optional[str] = None
    lease_expires_at: Optional[str] = None
    next_retry_at: Optional[str] = None
    last_error: Optional[str] = None
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)


@dataclass
class AuditEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=_utc_now_iso)
    event_type: str = ""
    config_hash: str = ""
    source: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
