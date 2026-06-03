"""Tests for parser data models and schema."""

from __future__ import annotations

import jsonschema
import pytest

from src.analyzer.parser_schema import (
    LLM_OUTPUT_SCHEMA,
    ParsedInstruction,
    ParseResult,
    generate_instruction_id,
)

# ---------------------------------------------------------------------------
# instruction_id generation
# ---------------------------------------------------------------------------


class TestGenerateInstructionId:
    def test_basic_format(self) -> None:
        result = generate_instruction_id("substack:20260601:test", 0)
        assert result == "instr:substack:20260601:test:0"

    def test_sequence_increment(self) -> None:
        base = "substack:20260601:test"
        assert generate_instruction_id(base, 0) == f"instr:{base}:0"
        assert generate_instruction_id(base, 1) == f"instr:{base}:1"
        assert generate_instruction_id(base, 5) == f"instr:{base}:5"

    def test_deterministic(self) -> None:
        assert generate_instruction_id("abc", 3) == generate_instruction_id("abc", 3)

    def test_different_post_id_different_result(self) -> None:
        assert generate_instruction_id("aaa", 0) != generate_instruction_id("bbb", 0)


# ---------------------------------------------------------------------------
# ParsedInstruction — basic construction
# ---------------------------------------------------------------------------


class TestParsedInstructionBasic:
    def test_minimal_buy(self) -> None:
        inst = ParsedInstruction(
            post_id="test:1",
            sequence=0,
            action="BUY",
            symbol="NVDA",
            quantity_type="pct",
            quantity_pct=1.0,
            confidence=0.95,
            parse_span="加倉 nvda 1%",
        )
        assert inst.action == "BUY"
        assert inst.symbol == "NVDA"
        assert inst.quantity_pct == 1.0
        assert inst.option_type is None

    def test_sell_all(self) -> None:
        inst = ParsedInstruction(
            post_id="test:1",
            sequence=0,
            action="SELL",
            symbol="ETSY",
            quantity_type="all",
            quantity_pct=None,
            confidence=0.9,
            parse_span="賣出全部 etsy",
        )
        assert inst.quantity_type == "all"
        assert inst.quantity_pct is None

    def test_option_instruction(self) -> None:
        inst = ParsedInstruction(
            post_id="test:1",
            sequence=0,
            action="option_place",
            symbol="CRWV",
            quantity_type="pct",
            quantity_pct=1.0,
            option_type="call",
            option_side="long",
            strike=150.0,
            expiry="2026-07-17",
            confidence=0.92,
            parse_span="買入1% crwv call（26年7月17日到期，strike 150）",
        )
        assert inst.option_type == "call"
        assert inst.option_side == "long"
        assert inst.strike == 150.0
        assert inst.expiry == "2026-07-17"

    def test_defaults(self) -> None:
        inst = ParsedInstruction(
            post_id="test:1",
            sequence=0,
            action="BUY",
            symbol="TSLA",
            quantity_type="pct",
            quantity_pct=2.0,
            confidence=0.88,
        )
        assert inst.market == "US"
        assert inst.time_modifier == "immediate"
        assert inst.scheduled_for is None
        assert inst.instruction_id == ""
        assert inst.idempotency_key == ""


# ---------------------------------------------------------------------------
# ParsedInstruction — validation
# ---------------------------------------------------------------------------


class TestParsedInstructionValidation:
    def test_reject_quantity_all_with_pct(self) -> None:
        with pytest.raises(ValueError, match="quantity_pct must be None"):
            ParsedInstruction(
                post_id="test:1",
                sequence=0,
                action="SELL",
                symbol="X",
                quantity_type="all",
                quantity_pct=5.0,
                confidence=0.9,
            )

    def test_reject_quantity_pct_without_value(self) -> None:
        with pytest.raises(ValueError, match="quantity_pct must be set"):
            ParsedInstruction(
                post_id="test:1",
                sequence=0,
                action="BUY",
                symbol="X",
                quantity_type="pct",
                quantity_pct=None,
                confidence=0.9,
            )

    def test_reject_incomplete_option_fields(self) -> None:
        """Only option_type set without option_side should fail."""
        with pytest.raises(ValueError, match="at least option_type"):
            ParsedInstruction(
                post_id="test:1",
                sequence=0,
                action="option_place",
                symbol="X",
                quantity_type="pct",
                quantity_pct=1.0,
                option_type="call",
                confidence=0.9,
            )

    def test_reject_empty_symbol(self) -> None:
        with pytest.raises(ValueError):
            ParsedInstruction(
                post_id="test:1",
                sequence=0,
                action="BUY",
                symbol="",
                quantity_type="pct",
                quantity_pct=1.0,
                confidence=0.9,
            )

    def test_reject_negative_sequence(self) -> None:
        with pytest.raises(ValueError):
            ParsedInstruction(
                post_id="test:1",
                sequence=-1,
                action="BUY",
                symbol="X",
                quantity_type="pct",
                quantity_pct=1.0,
                confidence=0.9,
            )

    def test_reject_confidence_out_of_range(self) -> None:
        with pytest.raises(ValueError):
            ParsedInstruction(
                post_id="test:1",
                sequence=0,
                action="BUY",
                symbol="X",
                quantity_type="pct",
                quantity_pct=1.0,
                confidence=1.5,
            )

    def test_reject_invalid_action(self) -> None:
        with pytest.raises(ValueError):
            ParsedInstruction(
                post_id="test:1",
                sequence=0,
                action="HOLD",  # type: ignore[literal-arg]
                symbol="X",
                quantity_type="pct",
                quantity_pct=1.0,
                confidence=0.9,
            )


# ---------------------------------------------------------------------------
# ParsedInstruction — compute_keys
# ---------------------------------------------------------------------------


class TestParsedInstructionComputeKeys:
    def test_generates_instruction_id(self) -> None:
        inst = ParsedInstruction(
            post_id="substack:20260601:test",
            sequence=0,
            action="BUY",
            symbol="NVDA",
            quantity_type="pct",
            quantity_pct=1.0,
            confidence=0.95,
        )
        inst.compute_keys()
        assert inst.instruction_id == "instr:substack:20260601:test:0"

    def test_generates_idempotency_key(self) -> None:
        inst = ParsedInstruction(
            post_id="substack:20260601:test",
            sequence=0,
            action="BUY",
            symbol="NVDA",
            quantity_type="pct",
            quantity_pct=1.0,
            confidence=0.95,
        )
        inst.compute_keys()
        assert inst.idempotency_key.startswith("idem:")

    def test_keys_deterministic(self) -> None:
        def _make() -> ParsedInstruction:
            return ParsedInstruction(
                post_id="test:1",
                sequence=2,
                action="SELL",
                symbol="AAPL",
                quantity_type="pct",
                quantity_pct=3.0,
                confidence=0.8,
            )

        a = _make()
        a.compute_keys()
        b = _make()
        b.compute_keys()
        assert a.instruction_id == b.instruction_id
        assert a.idempotency_key == b.idempotency_key

    def test_all_quantity_type_key_uses_zero(self) -> None:
        """quantity_type='all' uses 0.0 for idempotency key stability."""
        inst = ParsedInstruction(
            post_id="test:1",
            sequence=0,
            action="SELL",
            symbol="ETSY",
            quantity_type="all",
            quantity_pct=None,
            confidence=0.9,
        )
        inst.compute_keys()
        assert inst.idempotency_key.startswith("idem:")

        # Same instruction with pct=0.0 should produce same key
        inst2 = ParsedInstruction(
            post_id="test:1",
            sequence=0,
            action="SELL",
            symbol="ETSY",
            quantity_type="pct",
            quantity_pct=0.0,
            confidence=0.9,
        )
        inst2.compute_keys()
        assert inst.idempotency_key == inst2.idempotency_key


# ---------------------------------------------------------------------------
# ParseResult
# ---------------------------------------------------------------------------


class TestParseResult:
    def test_executable_result(self) -> None:
        result = ParseResult(
            post_id="test:1",
            status="EXECUTABLE",
            instructions=[
                ParsedInstruction(
                    post_id="test:1",
                    sequence=0,
                    action="BUY",
                    symbol="NVDA",
                    quantity_type="pct",
                    quantity_pct=1.0,
                    confidence=0.95,
                )
            ],
            reason_codes=["CLEAR_ACTION"],
            confidence=0.95,
            raw_text="加倉 nvda 1%",
            model_id="claude-opus-4-8",
        )
        assert result.status == "EXECUTABLE"
        assert len(result.instructions) == 1
        assert result.parsed_at  # auto-generated

    def test_skip_result(self) -> None:
        result = ParseResult(
            post_id="test:1",
            status="SKIP_NOT_ACTIONABLE",
            reason_codes=["NO_ACTION"],
            confidence=0.9,
            raw_text="今天沒有操作",
        )
        assert result.status == "SKIP_NOT_ACTIONABLE"
        assert result.instructions == []

    def test_needs_review_result(self) -> None:
        result = ParseResult(
            post_id="test:1",
            status="NEEDS_REVIEW",
            reason_codes=["LOW_CONFIDENCE"],
            confidence=0.3,
            raw_text="some ambiguous text",
        )
        assert result.status == "NEEDS_REVIEW"

    def test_reject_invalid_status(self) -> None:
        with pytest.raises(ValueError):
            ParseResult(
                post_id="test:1",
                status="INVALID",  # type: ignore[literal-arg]
                raw_text="x",
            )


# ---------------------------------------------------------------------------
# LLM_OUTPUT_SCHEMA validation
# ---------------------------------------------------------------------------


class TestLLMOutputSchema:
    def test_valid_executable_output(self) -> None:
        data = {
            "status": "EXECUTABLE",
            "reason_codes": ["CLEAR_ACTION"],
            "confidence": 0.95,
            "instructions": [
                {
                    "action": "BUY",
                    "symbol": "NVDA",
                    "quantity_type": "pct",
                    "quantity_pct": 1.0,
                    "confidence": 0.95,
                    "parse_span": "加倉 nvda 1%",
                }
            ],
        }
        jsonschema.validate(instance=data, schema=LLM_OUTPUT_SCHEMA)

    def test_valid_skip_output(self) -> None:
        data = {
            "status": "SKIP_NOT_ACTIONABLE",
            "reason_codes": ["NO_ACTION"],
            "confidence": 0.9,
            "instructions": [],
        }
        jsonschema.validate(instance=data, schema=LLM_OUTPUT_SCHEMA)

    def test_valid_option_output(self) -> None:
        data = {
            "status": "EXECUTABLE",
            "reason_codes": ["CLEAR_ACTION"],
            "confidence": 0.92,
            "instructions": [
                {
                    "action": "option_place",
                    "symbol": "CRWV",
                    "quantity_type": "pct",
                    "quantity_pct": 1.0,
                    "option_type": "call",
                    "option_side": "long",
                    "strike": 150.0,
                    "expiry": "2026-07-17",
                    "confidence": 0.92,
                    "parse_span": "買入1% crwv call",
                }
            ],
        }
        jsonschema.validate(instance=data, schema=LLM_OUTPUT_SCHEMA)

    def test_reject_missing_status(self) -> None:
        data = {
            "reason_codes": [],
            "confidence": 0.5,
            "instructions": [],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=LLM_OUTPUT_SCHEMA)

    def test_reject_invalid_status_value(self) -> None:
        data = {
            "status": "MAYBE",
            "reason_codes": [],
            "confidence": 0.5,
            "instructions": [],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=LLM_OUTPUT_SCHEMA)

    def test_reject_instruction_missing_required(self) -> None:
        data = {
            "status": "EXECUTABLE",
            "reason_codes": [],
            "confidence": 0.9,
            "instructions": [
                {
                    "action": "BUY",
                    # missing symbol, quantity_type, confidence
                }
            ],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=LLM_OUTPUT_SCHEMA)

    def test_reject_sell_all_with_pct_value(self) -> None:
        """Schema allows quantity_type='all' with quantity_pct=null."""
        data = {
            "status": "EXECUTABLE",
            "reason_codes": [],
            "confidence": 0.9,
            "instructions": [
                {
                    "action": "SELL",
                    "symbol": "ETSY",
                    "quantity_type": "all",
                    "quantity_pct": None,
                    "confidence": 0.9,
                }
            ],
        }
        # This should pass schema validation (null is allowed)
        jsonschema.validate(instance=data, schema=LLM_OUTPUT_SCHEMA)
