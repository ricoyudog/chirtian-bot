"""Executor data models — ExecutionIntent, ExecutionAttempt, and related types."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Execution status literals
# ---------------------------------------------------------------------------

ExecutionStatus = Literal[
    "ready",
    "previewed",
    "submitting",
    "acked",
    "unknown",
    "rejected",
    "filled",
    "cancelled",
    "human_review_pending",
    "expired_review",
]

AttemptOperation = Literal[
    "preview_order",
    "place_order",
    "get_order_status",
    "cancel_order",
]

AttemptStatus = Literal["success", "timeout", "error", "unknown"]


# ---------------------------------------------------------------------------
# ExecutionIntent
# ---------------------------------------------------------------------------


class ExecutionIntent(BaseModel):
    """Core data model for the executor stage.

    Bridges SizingDecision output to broker order flow.
    """

    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instruction_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: Literal["BUY", "SELL"]
    quantity: int = Field(ge=1)
    order_type: Literal["LIMIT"] = "LIMIT"
    limit_price: float = Field(gt=0)
    environment: str = Field(min_length=1)
    status: ExecutionStatus = "ready"


# ---------------------------------------------------------------------------
# ExecutionAttempt
# ---------------------------------------------------------------------------


class ExecutionAttempt(BaseModel):
    """Record of a single broker interaction attempt."""

    attempt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = Field(min_length=1)
    attempt_no: int = Field(ge=1)
    operation: AttemptOperation
    request_hash: str = Field(min_length=1)
    broker_order_id: str | None = None
    status: AttemptStatus
    response: dict = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def compute_idempotency_key(instruction_id: str, side: str, quantity: int) -> str:
    """Derive a deterministic idempotency key for an execution.

    sha256(instruction_id + side + str(quantity)) ensures uniqueness per
    instruction while incorporating the concrete order parameters.
    """
    raw = f"{instruction_id}:{side}:{quantity}"
    return hashlib.sha256(raw.encode()).hexdigest()
