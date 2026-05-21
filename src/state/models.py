"""Data models for the state layer."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional


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
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
