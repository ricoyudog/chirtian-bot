"""Layer 1: Gold set unit tests — mock LLM, deterministic, CI-safe.

These tests load each YAML case, mock the LLM with a matching response,
and verify parser output: status, instructions, IDs, reason codes.
No external dependencies (no claude CLI, no network).
"""

from __future__ import annotations

import pytest

from tests.gold_set.conftest import (
    _make_parser_with_mock,
    load_gold_cases,
)

# Load all cases once for parametrization
ALL_CASES = load_gold_cases()
CASE_IDS = [f"{c['case_id']}_{c['category']}" for c in ALL_CASES]


@pytest.mark.parametrize("case", ALL_CASES, ids=CASE_IDS)
class TestGoldSetUnit:
    """Parametrized gold set tests — one test per case."""

    def test_status_matches_expected(self, case: dict) -> None:
        """Parser must return the expected status classification."""
        parser, _ = _make_parser_with_mock(case)
        result = parser.parse(case["post_id"], case["raw_text"].strip())
        assert result.status == case["expected_status"], (
            f"Case {case['case_id']}: expected {case['expected_status']}, got {result.status}"
        )

    def test_instruction_count(self, case: dict) -> None:
        """Number of parsed instructions must match expected."""
        parser, _ = _make_parser_with_mock(case)
        result = parser.parse(case["post_id"], case["raw_text"].strip())
        expected_count = len(case.get("expected_instructions", []))
        assert len(result.instructions) == expected_count, (
            f"Case {case['case_id']}: expected {expected_count} instructions, "
            f"got {len(result.instructions)}"
        )

    def test_reason_codes_contain_expected(self, case: dict) -> None:
        """Result must contain all expected reason codes."""
        parser, _ = _make_parser_with_mock(case)
        result = parser.parse(case["post_id"], case["raw_text"].strip())
        expected_codes = set(case.get("expected_reason_codes", []))
        actual_codes = set(result.reason_codes)
        missing = expected_codes - actual_codes
        assert not missing, f"Case {case['case_id']}: missing reason codes {missing}"

    def test_instruction_id_format(self, case: dict) -> None:
        """Every instruction must have a valid instruction_id."""
        parser, _ = _make_parser_with_mock(case)
        result = parser.parse(case["post_id"], case["raw_text"].strip())
        for inst in result.instructions:
            expected_id = f"instr:{case['post_id']}:{inst.sequence}"
            assert inst.instruction_id == expected_id, (
                f"Case {case['case_id']}: expected ID {expected_id}, got {inst.instruction_id}"
            )

    def test_idempotency_key_present_and_stable(self, case: dict) -> None:
        """Every instruction must have a stable idempotency_key."""
        parser1, _ = _make_parser_with_mock(case)
        result1 = parser1.parse(case["post_id"], case["raw_text"].strip())

        parser2, _ = _make_parser_with_mock(case)
        result2 = parser2.parse(case["post_id"], case["raw_text"].strip())

        for inst1, inst2 in zip(result1.instructions, result2.instructions):
            assert inst1.idempotency_key.startswith("idem:"), (
                f"Case {case['case_id']}: key missing idem: prefix"
            )
            assert inst1.idempotency_key == inst2.idempotency_key, (
                f"Case {case['case_id']}: key not stable on replay"
            )

    def test_action_and_symbol_match(self, case: dict) -> None:
        """Action and symbol must match expected values."""
        parser, _ = _make_parser_with_mock(case)
        result = parser.parse(case["post_id"], case["raw_text"].strip())
        for inst, expected in zip(result.instructions, case.get("expected_instructions", [])):
            assert inst.action == expected["action"], f"Case {case['case_id']}: action mismatch"
            assert inst.symbol == expected["symbol"].upper(), (
                f"Case {case['case_id']}: symbol mismatch"
            )

    def test_quantity_type_matches(self, case: dict) -> None:
        """quantity_type must match expected (pct or all)."""
        parser, _ = _make_parser_with_mock(case)
        result = parser.parse(case["post_id"], case["raw_text"].strip())
        for inst, expected in zip(result.instructions, case.get("expected_instructions", [])):
            if "quantity_type" in expected:
                assert inst.quantity_type == expected["quantity_type"], (
                    f"Case {case['case_id']}: quantity_type mismatch"
                )

    def test_option_fields_match(self, case: dict) -> None:
        """Option-specific fields must match when present."""
        parser, _ = _make_parser_with_mock(case)
        result = parser.parse(case["post_id"], case["raw_text"].strip())
        for inst, expected in zip(result.instructions, case.get("expected_instructions", [])):
            for key in ("option_type", "option_side", "strike", "expiry"):
                if key in expected:
                    assert getattr(inst, key) == expected[key], (
                        f"Case {case['case_id']}: {key} mismatch"
                    )


class TestSchemaValidationError:
    """Verify parser handles mock schema errors correctly."""

    def test_invalid_schema_returns_needs_review(self) -> None:
        """When mock returns invalid data, parser should handle gracefully."""
        from unittest.mock import MagicMock

        from src.analyzer.llm_client import LLMError
        from src.analyzer.parser import InstructionParser

        mock_llm = MagicMock()
        mock_llm.complete_json.side_effect = LLMError("schema error")

        parser = InstructionParser(
            llm_client=mock_llm,
            reference_context="[Test]",
        )
        result = parser.parse("test:1", "some text")

        assert result.status == "NEEDS_REVIEW"
        assert "LLM_ERROR" in result.reason_codes


class TestNoExternalDependency:
    """Verify Layer 1 tests require no external processes."""

    def test_no_claude_cli_required(self) -> None:
        """All gold set unit tests use mocked LLM — no claude CLI needed."""

        cases = load_gold_cases()
        assert len(cases) >= 40, f"Expected >= 40 cases, got {len(cases)}"

        # Process one case end-to-end with mock
        case = cases[0]
        parser, _ = _make_parser_with_mock(case)
        result = parser.parse(case["post_id"], case["raw_text"].strip())
        assert result.status  # Should complete without any subprocess call
