"""Gold test set shared fixtures — loads YAML cases for parametrized testing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from src.analyzer.llm_client import LLMClient
from src.analyzer.parser import InstructionParser
from src.state.ledger import AuditLedger

CASES_DIR = Path(__file__).parent / "cases"


def load_gold_cases() -> list[dict]:
    """Load all YAML fixture files from cases/ directory.

    Returns:
        List of parsed case dicts sorted by case_id.
    """
    cases: list[dict] = []
    for path in sorted(CASES_DIR.glob("*.yaml")):
        with open(path) as f:
            case = yaml.safe_load(f)
            case["_file"] = path.name
            cases.append(case)
    return cases


def build_mock_llm_response(case: dict) -> dict:
    """Build a mock LLM response that matches the case's expected output.

    For EXECUTABLE cases: returns full instructions.
    For non-EXECUTABLE cases: returns empty instructions.
    """
    instructions = []
    for inst in case.get("expected_instructions", []):
        entry: dict = {
            "action": inst["action"],
            "symbol": inst["symbol"],
            "quantity_type": inst.get("quantity_type", "pct"),
            "quantity_pct": inst.get("quantity_pct"),
            "confidence": inst.get("confidence_min", 0.8),
            "parse_span": case.get("raw_text", "").strip(),
        }
        # Add optional fields
        for key in (
            "market",
            "time_modifier",
            "scheduled_for",
            "option_type",
            "option_side",
            "strike",
            "expiry",
        ):
            if key in inst and inst[key] is not None:
                entry[key] = inst[key]
        instructions.append(entry)

    return {
        "status": case["expected_status"],
        "reason_codes": case.get("expected_reason_codes", []),
        "confidence": 0.9,
        "instructions": instructions,
    }


@pytest.fixture
def gold_cases() -> list[dict]:
    """Load all gold set cases."""
    return load_gold_cases()


@pytest.fixture
def tmp_ledger(tmp_path: Path) -> AuditLedger:
    """Temporary audit ledger for testing."""
    return AuditLedger(tmp_path / "test_audit.jsonl")


def _make_parser_with_mock(
    case: dict,
    ledger: AuditLedger | None = None,
) -> tuple[InstructionParser, MagicMock]:
    """Create an InstructionParser with a mock LLM configured for the case."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete_json.return_value = build_mock_llm_response(case)
    parser = InstructionParser(
        llm_client=mock_llm,
        audit_ledger=ledger,
        reference_context="[Test reference context]",
    )
    return parser, mock_llm
