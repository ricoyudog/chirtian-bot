"""Parser data models and JSON schema for LLM output validation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from src.safety.idempotency import generate_idempotency_key

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def generate_instruction_id(post_id: str, sequence: int) -> str:
    """Generate a deterministic, human-readable instruction ID.

    Format: ``instr:{post_id}:{sequence}``
    """
    return f"instr:{post_id}:{sequence}"


# ---------------------------------------------------------------------------
# ParsedInstruction
# ---------------------------------------------------------------------------

ActionType = Literal[
    "BUY",
    "SELL",
    "SHORT",
    "COVER",
    "option_place",
    "option_cover",
]

QuantityType = Literal["pct", "all"]

TimeModifier = Literal["immediate", "open", "close", "scheduled"]

MarketType = Literal["US", "HK"]

OptionType = Literal["call", "put"]

OptionSide = Literal["long", "short"]


class ParsedInstruction(BaseModel):
    """A single parsed trading instruction extracted from a post."""

    # -- identifiers (set by parser, not LLM) ---
    instruction_id: str = ""
    idempotency_key: str = ""

    # -- core fields (from LLM output) ---
    post_id: str
    sequence: int = Field(ge=0)
    action: ActionType
    symbol: str = Field(min_length=1)
    market: MarketType = "US"

    # -- quantity ---
    quantity_type: QuantityType = "pct"
    quantity_pct: float | None = None

    # -- timing ---
    time_modifier: TimeModifier = "immediate"
    scheduled_for: str | None = None

    # -- option fields (null for equity instructions) ---
    option_type: OptionType | None = None
    option_side: OptionSide | None = None
    strike: float | None = None
    expiry: str | None = None  # ISO date "YYYY-MM-DD"

    # -- parse metadata ---
    confidence: float = Field(ge=0.0, le=1.0)
    parse_span: str = ""

    @model_validator(mode="after")
    def _validate_quantity(self) -> ParsedInstruction:
        """quantity_type='all' requires quantity_pct to be None."""
        if self.quantity_type == "all" and self.quantity_pct is not None:
            raise ValueError("quantity_pct must be None when quantity_type is 'all'")
        if self.quantity_type == "pct" and self.quantity_pct is None:
            raise ValueError("quantity_pct must be set when quantity_type is 'pct'")
        return self

    @model_validator(mode="after")
    def _validate_options(self) -> ParsedInstruction:
        """Option fields must be consistent: either all core fields set or all None."""
        option_fields = [self.option_type, self.option_side, self.strike, self.expiry]
        set_count = sum(1 for f in option_fields if f is not None)
        if set_count > 0 and set_count < 2:
            raise ValueError(
                "If any option field is set, at least option_type and option_side must be provided"
            )
        return self

    def compute_keys(self) -> ParsedInstruction:
        """Generate and set instruction_id and idempotency_key.

        Call this after constructing the instruction with post_id, sequence,
        action, symbol, and quantity_pct populated.
        """
        self.instruction_id = generate_instruction_id(self.post_id, self.sequence)
        # For quantity_type "all", use a sentinel for idempotency key stability
        qty = self.quantity_pct if self.quantity_pct is not None else 0.0
        self.idempotency_key = generate_idempotency_key(
            post_id=self.post_id,
            sequence=self.sequence,
            action=self.action,
            symbol=self.symbol,
            quantity_pct=qty,
        )
        return self


# ---------------------------------------------------------------------------
# ParseResult
# ---------------------------------------------------------------------------

ParseStatus = Literal["EXECUTABLE", "SKIP_NOT_ACTIONABLE", "NEEDS_REVIEW"]


class ParseResult(BaseModel):
    """Result of parsing a single post."""

    post_id: str
    status: ParseStatus
    instructions: list[ParsedInstruction] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    raw_text: str = ""
    model_id: str = ""
    parsed_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# ---------------------------------------------------------------------------
# LLM output JSON schema
# ---------------------------------------------------------------------------

LLM_OUTPUT_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["EXECUTABLE", "SKIP_NOT_ACTIONABLE", "NEEDS_REVIEW"],
        },
        "reason_codes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "instructions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "BUY",
                            "SELL",
                            "SHORT",
                            "COVER",
                            "option_place",
                            "option_cover",
                        ],
                    },
                    "symbol": {"type": "string", "minLength": 1},
                    "quantity_type": {
                        "type": "string",
                        "enum": ["pct", "all"],
                    },
                    "quantity_pct": {"type": ["number", "null"]},
                    "market": {
                        "type": "string",
                        "enum": ["US", "HK"],
                    },
                    "time_modifier": {
                        "type": "string",
                        "enum": ["immediate", "open", "close", "scheduled"],
                    },
                    "scheduled_for": {"type": ["string", "null"]},
                    "option_type": {
                        "type": ["string", "null"],
                        "enum": ["call", "put", None],
                    },
                    "option_side": {
                        "type": ["string", "null"],
                        "enum": ["long", "short", None],
                    },
                    "strike": {"type": ["number", "null"]},
                    "expiry": {"type": ["string", "null"]},
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "parse_span": {"type": "string"},
                },
                "required": [
                    "action",
                    "symbol",
                    "quantity_type",
                    "confidence",
                ],
            },
        },
    },
    "required": ["status", "reason_codes", "confidence", "instructions"],
}
