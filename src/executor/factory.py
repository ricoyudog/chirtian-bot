"""Factory functions for building executor data models from upstream outputs."""

from __future__ import annotations

from src.config.settings import RuntimeConfig
from src.executor.models import ExecutionIntent, compute_idempotency_key
from src.portfolio.models import SizingDecision


def build_execution_intent(
    sizing: SizingDecision,
    config: RuntimeConfig,
) -> ExecutionIntent | None:
    """Build an ExecutionIntent from a SizingDecision, or return None if not executable.

    Only SizingDecisions with sizing_status == "EXECUTABLE" and order_quantity >= 1
    produce an ExecutionIntent. All other statuses are skipped.
    """
    if sizing.sizing_status != "EXECUTABLE":
        return None

    if sizing.order_quantity < 1:
        return None

    side = sizing.action  # BUY or SELL — matches Literal directly
    quantity = sizing.order_quantity
    idempotency_key = compute_idempotency_key(
        instruction_id=sizing.instruction_id,
        side=side,
        quantity=quantity,
    )

    return ExecutionIntent(
        instruction_id=sizing.instruction_id,
        idempotency_key=idempotency_key,
        symbol=sizing.symbol,
        side=side,
        quantity=quantity,
        order_type="LIMIT",
        limit_price=sizing.estimated_price,
        environment=config.environment,
        status="ready",
    )
