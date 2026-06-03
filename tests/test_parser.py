"""Tests for InstructionParser — mock-based unit tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.analyzer.llm_client import LLMError, LLMTimeoutError
from src.analyzer.parser import InstructionParser
from src.state.ledger import AuditLedger

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_ledger(tmp_path: Path) -> AuditLedger:
    return AuditLedger(tmp_path / "audit.jsonl")


@pytest.fixture
def mock_llm() -> MagicMock:
    client = MagicMock()
    client.complete_json.return_value = _EXECUTABLE_RESPONSE
    return client


def _make_parser(
    mock_llm: MagicMock,
    ledger: AuditLedger | None = None,
) -> InstructionParser:
    return InstructionParser(
        llm_client=mock_llm,
        audit_ledger=ledger,
        reference_context="[Test reference context]",
    )


# ---------------------------------------------------------------------------
# Sample LLM responses
# ---------------------------------------------------------------------------

_EXECUTABLE_RESPONSE: dict = {
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
            "parse_span": "今天加倉 nvda 1%",
        }
    ],
}

_SELL_ALL_RESPONSE: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION"],
    "confidence": 0.92,
    "instructions": [
        {
            "action": "SELL",
            "symbol": "ETSY",
            "quantity_type": "all",
            "quantity_pct": None,
            "confidence": 0.92,
            "parse_span": "賣出全部 etsy",
        }
    ],
}

_CLEAR_SELL_RESPONSE: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION"],
    "confidence": 0.9,
    "instructions": [
        {
            "action": "SELL",
            "symbol": "TSLA",
            "quantity_type": "pct",
            "quantity_pct": 1.0,
            "confidence": 0.9,
            "parse_span": "賣出tsla（-1%）",
        }
    ],
}

_NOOP_RESPONSE: dict = {
    "status": "SKIP_NOT_ACTIONABLE",
    "reason_codes": ["NO_ACTION"],
    "confidence": 0.95,
    "instructions": [],
}

_FUTURE_RESPONSE: dict = {
    "status": "SKIP_NOT_ACTIONABLE",
    "reason_codes": ["FUTURE_INTENT"],
    "confidence": 0.9,
    "instructions": [],
}

_CONDITIONAL_RESPONSE: dict = {
    "status": "SKIP_NOT_ACTIONABLE",
    "reason_codes": ["CONDITIONAL"],
    "confidence": 0.88,
    "instructions": [],
}

_SUMMARY_RESPONSE: dict = {
    "status": "SKIP_NOT_ACTIONABLE",
    "reason_codes": ["HISTORICAL_SUMMARY"],
    "confidence": 0.92,
    "instructions": [],
}

_MIXED_RESPONSE: dict = {
    "status": "SKIP_NOT_ACTIONABLE",
    "reason_codes": ["HISTORICAL_SUMMARY", "FUTURE_INTENT", "CONDITIONAL"],
    "confidence": 0.85,
    "instructions": [],
}

_AMBIGUOUS_RESPONSE: dict = {
    "status": "NEEDS_REVIEW",
    "reason_codes": ["LOW_CONFIDENCE"],
    "confidence": 0.4,
    "instructions": [],
}

_MULTI_RESPONSE: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION", "MULTI_INSTRUCTION"],
    "confidence": 0.93,
    "instructions": [
        {
            "action": "BUY",
            "symbol": "AAOI",
            "quantity_type": "pct",
            "quantity_pct": 1.0,
            "confidence": 0.93,
            "parse_span": "加倉aaoi 1%",
        },
        {
            "action": "BUY",
            "symbol": "U",
            "quantity_type": "pct",
            "quantity_pct": 2.0,
            "confidence": 0.93,
            "parse_span": "加倉u 2%",
        },
        {
            "action": "BUY",
            "symbol": "SOFI",
            "quantity_type": "pct",
            "quantity_pct": 2.0,
            "confidence": 0.93,
            "parse_span": "加倉sofi 2%",
        },
    ],
}

_OPTION_LONG_CALL: dict = {
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
            "parse_span": "買入1% crwv call（26年7月17日到期，strike 150）",
        }
    ],
}

_OPTION_SHORT_CALL: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION"],
    "confidence": 0.9,
    "instructions": [
        {
            "action": "option_place",
            "symbol": "TSLA",
            "quantity_type": "pct",
            "quantity_pct": 2.0,
            "option_type": "call",
            "option_side": "short",
            "strike": 380.0,
            "expiry": "2026-07-18",
            "confidence": 0.9,
            "parse_span": "開始short 特斯拉 call，strike 380",
        }
    ],
}

_OPTION_LONG_PUT: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION"],
    "confidence": 0.88,
    "instructions": [
        {
            "action": "option_place",
            "symbol": "EWY",
            "quantity_type": "pct",
            "quantity_pct": 0.3,
            "option_type": "put",
            "option_side": "long",
            "strike": 120.0,
            "expiry": "2026-04-17",
            "confidence": 0.88,
            "parse_span": "買入0.3%的EWY 260417 120P",
        }
    ],
}


# ---------------------------------------------------------------------------
# Tests: Clear buy
# ---------------------------------------------------------------------------


class TestClearBuy:
    def test_executable_with_correct_fields(self, mock_llm: MagicMock) -> None:
        parser = _make_parser(mock_llm)
        result = parser.parse("substack:20260601:test", "今天加倉 nvda 1%")

        assert result.status == "EXECUTABLE"
        assert len(result.instructions) == 1
        inst = result.instructions[0]
        assert inst.action == "BUY"
        assert inst.symbol == "NVDA"
        assert inst.quantity_pct == 1.0
        assert inst.quantity_type == "pct"
        assert inst.confidence == 0.95

    def test_instruction_id_generated(self, mock_llm: MagicMock) -> None:
        parser = _make_parser(mock_llm)
        result = parser.parse("substack:20260601:test", "加倉 nvda 1%")

        inst = result.instructions[0]
        assert inst.instruction_id == "instr:substack:20260601:test:0"

    def test_idempotency_key_generated(self, mock_llm: MagicMock) -> None:
        parser = _make_parser(mock_llm)
        result = parser.parse("substack:20260601:test", "加倉 nvda 1%")

        inst = result.instructions[0]
        assert inst.idempotency_key.startswith("idem:")


# ---------------------------------------------------------------------------
# Tests: Clear sell
# ---------------------------------------------------------------------------


class TestClearSell:
    def test_executable_sell(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _CLEAR_SELL_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "賣出tsla（-1%）")

        assert result.status == "EXECUTABLE"
        assert result.instructions[0].action == "SELL"


# ---------------------------------------------------------------------------
# Tests: Sell all
# ---------------------------------------------------------------------------


class TestSellAll:
    def test_quantity_type_all(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _SELL_ALL_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "賣出全部 etsy")

        inst = result.instructions[0]
        assert inst.quantity_type == "all"
        assert inst.quantity_pct is None


# ---------------------------------------------------------------------------
# Tests: No-op
# ---------------------------------------------------------------------------


class TestNoOp:
    def test_skip_not_actionable(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _NOOP_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "今天沒有操作")

        assert result.status == "SKIP_NOT_ACTIONABLE"
        assert result.instructions == []
        assert "NO_ACTION" in result.reason_codes


# ---------------------------------------------------------------------------
# Tests: Future intent
# ---------------------------------------------------------------------------


class TestFutureIntent:
    def test_skip_with_future_intent_code(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _FUTURE_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "準備下週找機會做空泡泡瑪特")

        assert result.status == "SKIP_NOT_ACTIONABLE"
        assert "FUTURE_INTENT" in result.reason_codes


# ---------------------------------------------------------------------------
# Tests: Conditional
# ---------------------------------------------------------------------------


class TestConditional:
    def test_skip_with_conditional_code(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _CONDITIONAL_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "如果明天還保持弱勢，會考慮削減nvdl")

        assert result.status == "SKIP_NOT_ACTIONABLE"
        assert "CONDITIONAL" in result.reason_codes


# ---------------------------------------------------------------------------
# Tests: Summary
# ---------------------------------------------------------------------------


class TestSummary:
    def test_skip_with_summary_code(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _SUMMARY_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "3月-8月總結")

        assert result.status == "SKIP_NOT_ACTIONABLE"
        assert "HISTORICAL_SUMMARY" in result.reason_codes


# ---------------------------------------------------------------------------
# Tests: Mixed summary + forward
# ---------------------------------------------------------------------------


class TestMixedSummaryForward:
    def test_skip_with_multiple_codes(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _MIXED_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "本週操作...下週計劃...如果突破...")

        assert result.status == "SKIP_NOT_ACTIONABLE"
        assert "HISTORICAL_SUMMARY" in result.reason_codes
        assert "FUTURE_INTENT" in result.reason_codes
        assert "CONDITIONAL" in result.reason_codes


# ---------------------------------------------------------------------------
# Tests: Ambiguous / low confidence
# ---------------------------------------------------------------------------


class TestAmbiguous:
    def test_needs_review(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _AMBIGUOUS_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "some vague text")

        assert result.status == "NEEDS_REVIEW"
        assert "LOW_CONFIDENCE" in result.reason_codes


# ---------------------------------------------------------------------------
# Tests: Multi-instruction
# ---------------------------------------------------------------------------


class TestMultiInstruction:
    def test_correct_sequence_order(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _MULTI_RESPONSE
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "加倉aaoi 1%，加倉u 2%，加倉sofi 2%")

        assert result.status == "EXECUTABLE"
        assert len(result.instructions) == 3

        symbols = [inst.symbol for inst in result.instructions]
        assert symbols == ["AAOI", "U", "SOFI"]

        sequences = [inst.sequence for inst in result.instructions]
        assert sequences == [0, 1, 2]

        ids = [inst.instruction_id for inst in result.instructions]
        assert ids[0] != ids[1] != ids[2]


# ---------------------------------------------------------------------------
# Tests: Options
# ---------------------------------------------------------------------------


class TestOptionLongCall:
    def test_correct_option_fields(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _OPTION_LONG_CALL
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "買入1% crwv call（...）")

        inst = result.instructions[0]
        assert inst.action == "option_place"
        assert inst.option_type == "call"
        assert inst.option_side == "long"
        assert inst.strike == 150.0
        assert inst.expiry == "2026-07-17"


class TestOptionShortCall:
    def test_correct_option_fields(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _OPTION_SHORT_CALL
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "開始short 特斯拉 call")

        inst = result.instructions[0]
        assert inst.option_type == "call"
        assert inst.option_side == "short"
        assert inst.strike == 380.0


class TestOptionLongPut:
    def test_correct_option_fields(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.return_value = _OPTION_LONG_PUT
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "買入0.3%的EWY 260417 120P")

        inst = result.instructions[0]
        assert inst.option_type == "put"
        assert inst.option_side == "long"
        assert inst.strike == 120.0
        assert inst.expiry == "2026-04-17"


# ---------------------------------------------------------------------------
# Tests: Error handling
# ---------------------------------------------------------------------------


class TestLLMError:
    def test_timeout_returns_needs_review(self, mock_llm: MagicMock) -> None:
        mock_llm.complete_json.side_effect = LLMTimeoutError(timeout=60.0, elapsed=61.0)
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "加倉 nvda 1%")

        assert result.status == "NEEDS_REVIEW"
        assert "LLM_ERROR" in result.reason_codes
        assert result.instructions == []

    def test_generic_llm_error_returns_needs_review(
        self, mock_llm: MagicMock
    ) -> None:
        mock_llm.complete_json.side_effect = LLMError("something broke")
        parser = _make_parser(mock_llm)
        result = parser.parse("test:1", "加倉 nvda 1%")

        assert result.status == "NEEDS_REVIEW"
        assert result.instructions == []


# ---------------------------------------------------------------------------
# Tests: ID stability
# ---------------------------------------------------------------------------


class TestIdStability:
    def test_same_input_same_keys(self, mock_llm: MagicMock) -> None:
        parser = _make_parser(mock_llm)

        result1 = parser.parse("test:1", "加倉 nvda 1%")
        result2 = parser.parse("test:1", "加倉 nvda 1%")

        assert result1.instructions[0].instruction_id == result2.instructions[0].instruction_id
        assert result1.instructions[0].idempotency_key == result2.instructions[0].idempotency_key


# ---------------------------------------------------------------------------
# Tests: Audit events
# ---------------------------------------------------------------------------


class TestAuditEvents:
    def test_audit_on_success(self, mock_llm: MagicMock, tmp_ledger: AuditLedger) -> None:
        parser = _make_parser(mock_llm, tmp_ledger)
        parser.parse("test:1", "加倉 nvda 1%")

        events = tmp_ledger.query(event_type="instructions_parsed")
        assert len(events) == 1
        assert events[0].data["status"] == "EXECUTABLE"
        assert events[0].data["instruction_count"] == 1

    def test_audit_on_skip(self, mock_llm: MagicMock, tmp_ledger: AuditLedger) -> None:
        mock_llm.complete_json.return_value = _NOOP_RESPONSE
        parser = _make_parser(mock_llm, tmp_ledger)
        parser.parse("test:1", "今天沒有操作")

        events = tmp_ledger.query(event_type="parse_completed")
        assert len(events) == 1
        assert events[0].data["status"] == "SKIP_NOT_ACTIONABLE"

    def test_audit_on_error(self, mock_llm: MagicMock, tmp_ledger: AuditLedger) -> None:
        mock_llm.complete_json.side_effect = LLMTimeoutError(timeout=60.0, elapsed=61.0)
        parser = _make_parser(mock_llm, tmp_ledger)
        parser.parse("test:1", "加倉 nvda 1%")

        events = tmp_ledger.query(event_type="parse_error")
        assert len(events) == 1
        assert events[0].data["status"] == "NEEDS_REVIEW"
        assert events[0].data["error"] is not None

    def test_no_audit_when_ledger_is_none(self, mock_llm: MagicMock) -> None:
        """Parser should work without a ledger (no audit written)."""
        parser = _make_parser(mock_llm, ledger=None)
        result = parser.parse("test:1", "加倉 nvda 1%")
        assert result.status == "EXECUTABLE"
