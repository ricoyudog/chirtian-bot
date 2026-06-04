"""Portfolio data models — snapshot, sizing decision, and reconciliation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Position & Snapshot
# ---------------------------------------------------------------------------


class Position(BaseModel):
    """A single equity position in the portfolio."""

    symbol: str = Field(min_length=1)
    quantity: int = Field(ge=0)
    avg_cost: float = Field(ge=0)
    market_value_usd: float = Field(ge=0)
    side: Literal["long", "short"] = "long"


class OpenOrder(BaseModel):
    """A pending/open broker order."""

    order_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    order_type: str = "MARKET"
    limit_price: float | None = None
    status: str = "pending"


class Quote(BaseModel):
    """A price quote for a single symbol."""

    symbol: str = Field(min_length=1)
    price: float = Field(gt=0)
    ask: float | None = None
    bid: float | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PortfolioSnapshot(BaseModel):
    """A point-in-time snapshot of account state."""

    account_id: str = Field(min_length=1)
    equity_usd: float = Field(ge=0)
    buying_power_usd: float = Field(ge=0)
    positions: list[Position] = Field(default_factory=list)
    open_orders: list[OpenOrder] = Field(default_factory=list)
    snapshot_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    source: Literal["fake", "webull"] = "fake"

    def get_position(self, symbol: str) -> Position | None:
        """Find a position by symbol (case-insensitive)."""
        symbol_upper = symbol.upper()
        for pos in self.positions:
            if pos.symbol.upper() == symbol_upper:
                return pos
        return None

    def has_open_order(self, symbol: str) -> bool:
        """Check if there is any open order for the given symbol."""
        symbol_upper = symbol.upper()
        return any(o.symbol.upper() == symbol_upper for o in self.open_orders)


# ---------------------------------------------------------------------------
# Sizing Decision
# ---------------------------------------------------------------------------

SizingStatus = Literal[
    "EXECUTABLE",
    "MODIFY_SIZE",
    "SKIP_TOO_SMALL",
    "SKIP_INSUFFICIENT_BUYING_POWER",
    "SKIP_LOT_SIZE",
    "SKIP_NO_POSITION",
    "SIZING_NEEDS_REVIEW",
    "SKIP_STALE_QUOTE",
]


class SizingDecision(BaseModel):
    """Output of the SizingEngine for a single instruction."""

    instruction_id: str
    symbol: str = Field(min_length=1)
    action: Literal["BUY", "SELL"]
    sizing_status: SizingStatus

    # -- portfolio context --
    basis: Literal["portfolio_equity"] = "portfolio_equity"
    portfolio_equity_usd: float
    available_buying_power_usd: float

    # -- sizing inputs --
    target_pct: float | None = None
    target_notional_usd: float | None = None  # Buy path
    capped_notional_usd: float | None = None  # Buy path, after clamps
    target_quantity: float | None = None  # Sell path (before floor)

    # -- pricing --
    estimated_price: float = Field(gt=0)

    # -- lot/quantity --
    lot_size: int = Field(default=1, ge=1)
    min_quantity: int = Field(default=1, ge=1)
    order_quantity: int = Field(ge=0)
    estimated_order_notional_usd: float = Field(ge=0)
    unfilled_residual_usd: float = Field(ge=0)

    # -- audit --
    reason_codes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


class ReconcileDifference(BaseModel):
    """A single field difference found during reconciliation."""

    field: str
    local_value: Any
    broker_value: Any
    tolerance: Any
    exceeded: bool


class ReconcileResult(BaseModel):
    """Output of the Reconciler comparing local vs broker state."""

    reconcile_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: Literal["ok", "mismatch"]
    local_snapshot_hash: str = ""
    broker_snapshot_hash: str = ""
    differences: list[ReconcileDifference] = Field(default_factory=list)
    action_taken: str = "none"
    requires_manual_clear: bool = False
