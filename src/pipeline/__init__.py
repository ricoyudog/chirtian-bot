"""Trading pipeline package — end-to-end orchestrator + wiring."""

from src.pipeline.orchestrator import (
    OUTCOME_BLOCKED,
    OUTCOME_NEEDS_REVIEW,
    OUTCOME_PLACED,
    OUTCOME_REJECTED,
    OUTCOME_SKIPPED,
    InstructionOutcome,
    TradingPipeline,
)

__all__ = [
    "TradingPipeline",
    "InstructionOutcome",
    "OUTCOME_PLACED",
    "OUTCOME_SKIPPED",
    "OUTCOME_NEEDS_REVIEW",
    "OUTCOME_REJECTED",
    "OUTCOME_BLOCKED",
]
