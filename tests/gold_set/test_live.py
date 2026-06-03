"""Layer 2: Gold set integration tests — live Claude CLI with tolerances.

These tests call the real Claude CLI and verify parser output with
defined tolerances. They are NOT run in CI.

Run manually:
    pytest tests/gold_set/test_live.py -m live -v

Or via nightly run.
"""

from __future__ import annotations

import pytest

from src.analyzer.llm_client import ClaudeCliClient
from src.analyzer.parser import InstructionParser
from tests.gold_set.conftest import load_gold_cases

# Skip all tests in this module unless --live flag is given
pytestmark = pytest.mark.live

ALL_CASES = load_gold_cases()
CASE_IDS = [f"{c['case_id']}_{c['category']}" for c in ALL_CASES]

# Quantity tolerance: ±0.1%
QTY_TOLERANCE = 0.1


@pytest.fixture
def live_parser() -> InstructionParser:
    """Parser with real Claude CLI client."""
    client = ClaudeCliClient()
    return InstructionParser(
        llm_client=client,
        reference_context=None,  # Will load from file
    )


@pytest.mark.parametrize("case", ALL_CASES, ids=CASE_IDS)
class TestGoldSetLive:
    """Live gold set tests — real Claude CLI with tolerances."""

    def test_status_must_match_exactly(self, case: dict, live_parser: InstructionParser) -> None:
        """Status classification must match exactly."""
        result = live_parser.parse(case["post_id"], case["raw_text"].strip())
        assert result.status == case["expected_status"], (
            f"Case {case['case_id']} ({case['category']}): "
            f"expected {case['expected_status']}, got {result.status}"
        )
        # Record for review
        print(
            f"\n  Case {case['case_id']}: status={result.status} confidence={result.confidence:.2f}"
        )

    def test_action_and_symbol_must_match(self, case: dict, live_parser: InstructionParser) -> None:
        """Action and symbol must match exactly for EXECUTABLE cases."""
        if case["expected_status"] != "EXECUTABLE":
            pytest.skip("Non-EXECUTABLE case")

        result = live_parser.parse(case["post_id"], case["raw_text"].strip())

        expected = case.get("expected_instructions", [])
        if not expected:
            pytest.skip("No expected instructions")

        assert len(result.instructions) == len(expected), (
            f"Case {case['case_id']}: expected {len(expected)} instructions, "
            f"got {len(result.instructions)}"
        )

        for inst, exp in zip(result.instructions, expected):
            assert inst.action == exp["action"], (
                f"Case {case['case_id']}: action mismatch, "
                f"expected {exp['action']}, got {inst.action}"
            )
            assert inst.symbol.upper() == exp["symbol"].upper(), (
                f"Case {case['case_id']}: symbol mismatch, "
                f"expected {exp['symbol']}, got {inst.symbol}"
            )

    def test_quantity_within_tolerance(self, case: dict, live_parser: InstructionParser) -> None:
        """quantity_pct must be within ±0.1 of expected."""
        if case["expected_status"] != "EXECUTABLE":
            pytest.skip("Non-EXECUTABLE case")

        result = live_parser.parse(case["post_id"], case["raw_text"].strip())
        expected = case.get("expected_instructions", [])

        for inst, exp in zip(result.instructions, expected):
            if exp.get("quantity_pct") is not None and inst.quantity_pct is not None:
                diff = abs(inst.quantity_pct - exp["quantity_pct"])
                assert diff <= QTY_TOLERANCE, (
                    f"Case {case['case_id']}: quantity_pct {inst.quantity_pct} "
                    f"not within ±{QTY_TOLERANCE} of {exp['quantity_pct']}"
                )

    def test_reason_codes_subset(self, case: dict, live_parser: InstructionParser) -> None:
        """Result must contain all expected reason codes (superset allowed)."""
        result = live_parser.parse(case["post_id"], case["raw_text"].strip())
        expected_codes = set(case.get("expected_reason_codes", []))
        actual_codes = set(result.reason_codes)
        missing = expected_codes - actual_codes
        assert not missing, f"Case {case['case_id']}: missing reason codes {missing}"

    def test_confidence_recorded_not_verified(
        self, case: dict, live_parser: InstructionParser
    ) -> None:
        """Confidence should be recorded (0-1) but not verified against expected."""
        result = live_parser.parse(case["post_id"], case["raw_text"].strip())
        assert 0.0 <= result.confidence <= 1.0, (
            f"Case {case['case_id']}: confidence {result.confidence} out of range"
        )
        # Record for human review
        print(
            f"\n  Case {case['case_id']}: confidence={result.confidence:.2f} status={result.status}"
        )

    def test_parse_span_recorded_not_verified(
        self, case: dict, live_parser: InstructionParser
    ) -> None:
        """Parse spans should be recorded but not verified."""
        result = live_parser.parse(case["post_id"], case["raw_text"].strip())
        for inst in result.instructions:
            assert inst.parse_span, f"Case {case['case_id']}: parse_span is empty"
            # Record for human review
            print(f"\n  Case {case['case_id']}: span='{inst.parse_span[:50]}...'")
