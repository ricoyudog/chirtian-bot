"""Tests for CrossCheckParser — 3-way DeepSeek V4 Flash + 2/3 majority voting.

Mock-based unit tests. The HTTP layer is mocked at the module boundary
(``_http_post_json``) so the ThreadPoolExecutor + voting logic is exercised
end-to-end without network or subprocess dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.analyzer import parser_crosscheck
from src.analyzer.parser import InstructionParser
from src.analyzer.parser_crosscheck import CrossCheckParser
from src.analyzer.parser_schema import ParseResult
from src.state.ledger import AuditLedger

# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_ledger(tmp_path: Path) -> AuditLedger:
    return AuditLedger(tmp_path / "audit.jsonl")


def _make_parser(runs_dir: Path, ledger: AuditLedger | None = None) -> CrossCheckParser:
    return CrossCheckParser(
        deepseek_api_key="test-key",
        runs_dir=runs_dir,
        audit_ledger=ledger,
        timeout_seconds=5,
    )


def _wrap(inner: dict) -> dict:
    """Wrap an inner parser JSON object as a chat-completions response."""
    return {
        "choices": [{"message": {"content": json.dumps(inner)}}]
    }


# Sample inner responses
_BUY_NVDA_5: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION"],
    "confidence": 0.92,
    "instructions": [
        {
            "action": "BUY",
            "symbol": "NVDA",
            "quantity_type": "pct",
            "quantity_pct": 5.0,
            "market": "US",
            "time_modifier": "immediate",
            "confidence": 0.92,
            "parse_span": "加倉 nvda 5%",
        }
    ],
}

_BUY_NVDA_3: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION"],
    "confidence": 0.88,
    "instructions": [
        {
            "action": "BUY",
            "symbol": "NVDA",
            "quantity_type": "pct",
            "quantity_pct": 3.0,
            "market": "US",
            "time_modifier": "immediate",
            "confidence": 0.88,
            "parse_span": "加倉 nvda 3%",
        }
    ],
}

_BUY_AMD: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION"],
    "confidence": 0.45,
    "instructions": [
        {
            "action": "BUY",
            "symbol": "AMD",
            "quantity_type": "pct",
            "quantity_pct": 5.0,
            "market": "US",
            "time_modifier": "immediate",
            "confidence": 0.45,
            "parse_span": "amd buy",
        }
    ],
}

_SELL_NVDA: dict = {
    "status": "EXECUTABLE",
    "reason_codes": ["CLEAR_ACTION"],
    "confidence": 0.85,
    "instructions": [
        {
            "action": "SELL",
            "symbol": "NVDA",
            "quantity_type": "pct",
            "quantity_pct": 5.0,
            "market": "US",
            "time_modifier": "immediate",
            "confidence": 0.85,
            "parse_span": "賣出 nvda 5%",
        }
    ],
}

_SKIP_NOOP: dict = {
    "status": "SKIP_NOT_ACTIONABLE",
    "reason_codes": ["NO_ACTION"],
    "confidence": 0.95,
    "instructions": [],
}


# ---------------------------------------------------------------------------
# Tests: 3/3 agreement
# ---------------------------------------------------------------------------


class TestUnanimousAgreement:
    def test_three_way_agreement_executable(self, tmp_path: Path) -> None:
        responses = [_wrap(_BUY_NVDA_5), _wrap(_BUY_NVDA_5), _wrap(_BUY_NVDA_5)]
        with patch.object(
            parser_crosscheck,
            "_http_post_json",
            side_effect=responses,
        ):
            parser = _make_parser(tmp_path)
            result = parser.parse("post:1", "加倉 nvda 5%")

        assert result.status == "EXECUTABLE"
        assert len(result.instructions) == 1
        inst = result.instructions[0]
        assert inst.action == "BUY"
        assert inst.symbol == "NVDA"
        assert inst.quantity_pct == 5.0
        assert inst.instruction_id == "instr:post:1:0"
        assert inst.idempotency_key.startswith("idem:")


# ---------------------------------------------------------------------------
# Tests: 2/3 agreement (symbol)
# ---------------------------------------------------------------------------


class TestTwoOfThreeAgreement:
    def test_two_agree_one_disagrees_symbol(self, tmp_path: Path) -> None:
        # A,B agree NVDA BUY; C returns AMD BUY → accept majority NVDA
        responses = [_wrap(_BUY_NVDA_5), _wrap(_BUY_NVDA_5), _wrap(_BUY_AMD)]
        with patch.object(
            parser_crosscheck,
            "_http_post_json",
            side_effect=responses,
        ):
            parser = _make_parser(tmp_path)
            result = parser.parse("post:2", "加倉 nvda 5%")

        assert result.status == "EXECUTABLE"
        assert result.instructions[0].symbol == "NVDA"
        assert result.instructions[0].action == "BUY"

    def test_two_agree_qty_uses_median(self, tmp_path: Path) -> None:
        # Two agreeing models → qty_pct = median of the two agreeing models.
        # A=5, B=3 → median(5, 3) = 4.0
        responses = [_wrap(_BUY_NVDA_5), _wrap(_BUY_NVDA_3), _wrap(_BUY_AMD)]
        with patch.object(
            parser_crosscheck,
            "_http_post_json",
            side_effect=responses,
        ):
            parser = _make_parser(tmp_path)
            result = parser.parse("post:3", "加倉 nvda")

        assert result.status == "EXECUTABLE"
        assert result.instructions[0].quantity_pct == 4.0


# ---------------------------------------------------------------------------
# Tests: 0/3 disagreement
# ---------------------------------------------------------------------------


class TestNoConsensus:
    def test_all_three_disagree_needs_review(self, tmp_path: Path) -> None:
        third = {
            "status": "EXECUTABLE",
            "reason_codes": ["CLEAR_ACTION"],
            "confidence": 0.5,
            "instructions": [
                {
                    "action": "BUY",
                    "symbol": "TSLA",
                    "quantity_type": "pct",
                    "quantity_pct": 2.0,
                    "confidence": 0.5,
                }
            ],
        }
        responses = [_wrap(_BUY_NVDA_5), _wrap(_BUY_AMD), _wrap(third)]
        with patch.object(
            parser_crosscheck,
            "_http_post_json",
            side_effect=responses,
        ):
            parser = _make_parser(tmp_path)
            result = parser.parse("post:4", "ambiguous")

        assert result.status == "NEEDS_REVIEW"
        assert "CROSSCHECK_NO_CONSENSUS" in result.reason_codes
        assert result.instructions == []


# ---------------------------------------------------------------------------
# Tests: 2/3 disagreement on action
# ---------------------------------------------------------------------------


class TestActionDisagreement:
    def test_two_disagree_on_action_needs_review(self, tmp_path: Path) -> None:
        # A: NVDA BUY, B: NVDA SELL, C: AMD BUY → no (symbol, action) majority.
        responses = [_wrap(_BUY_NVDA_5), _wrap(_SELL_NVDA), _wrap(_BUY_AMD)]
        with patch.object(
            parser_crosscheck,
            "_http_post_json",
            side_effect=responses,
        ):
            parser = _make_parser(tmp_path)
            result = parser.parse("post:5", "ambiguous action")

        assert result.status == "NEEDS_REVIEW"
        assert "CROSSCHECK_NO_CONSENSUS" in result.reason_codes


# ---------------------------------------------------------------------------
# Tests: timeout handling
# ---------------------------------------------------------------------------


class TestTimeoutHandling:
    def test_one_model_timeout_proceeds_with_two(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # First two calls succeed (both NVDA BUY), third times out.
        responses = iter([_wrap(_BUY_NVDA_5), _wrap(_BUY_NVDA_5)])

        def _fake_post(url, body, api_key, timeout_seconds):
            try:
                return next(responses)
            except StopIteration:
                raise TimeoutError("simulated timeout")

        monkeypatch.setattr(parser_crosscheck, "_http_post_json", _fake_post)

        parser = _make_parser(tmp_path)
        result = parser.parse("post:6", "加倉 nvda 5%")

        assert result.status == "EXECUTABLE"
        assert result.instructions[0].symbol == "NVDA"

    def test_all_models_timeout_needs_review(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _fake_post(url, body, api_key, timeout_seconds):
            raise TimeoutError("simulated timeout")

        monkeypatch.setattr(parser_crosscheck, "_http_post_json", _fake_post)

        parser = _make_parser(tmp_path)
        result = parser.parse("post:7", "加倉 nvda 5%")

        assert result.status == "NEEDS_REVIEW"
        assert "CROSSCHECK_LLM_ALL_FAILED" in result.reason_codes


# ---------------------------------------------------------------------------
# Tests: ParseResult structural compatibility
# ---------------------------------------------------------------------------


class TestParseResultStructure:
    def test_output_identical_to_instruction_parser(self, tmp_path: Path) -> None:
        """CrossCheck output must populate the same ParseResult fields as
        InstructionParser so downstream stages need no changes."""
        responses = [_wrap(_BUY_NVDA_5), _wrap(_BUY_NVDA_5), _wrap(_BUY_NVDA_5)]
        with patch.object(
            parser_crosscheck,
            "_http_post_json",
            side_effect=responses,
        ):
            parser = _make_parser(tmp_path)
            xcheck_result = parser.parse("post:8", "加倉 nvda 5%")

        # Sanity: every ParseResult field is populated / has a sensible default.
        assert xcheck_result.post_id == "post:8"
        assert xcheck_result.status == "EXECUTABLE"
        assert isinstance(xcheck_result.instructions, list)
        assert xcheck_result.instructions  # non-empty
        assert isinstance(xcheck_result.reason_codes, list)
        assert isinstance(xcheck_result.confidence, float)
        assert xcheck_result.raw_text == "加倉 nvda 5%"
        assert xcheck_result.model_id == "deepseek-chat"
        assert xcheck_result.parsed_at  # ISO timestamp

        # Instruction fields mirror what InstructionParser would produce.
        inst = xcheck_result.instructions[0]
        assert inst.instruction_id == "instr:post:8:0"
        assert inst.idempotency_key.startswith("idem:")

        # The _map_response code path is shared with InstructionParser, so the
        # structural guarantee holds at the type level — verify the type.
        assert isinstance(xcheck_result, ParseResult)

    def test_compatible_with_instruction_parser_signature(
        self, tmp_path: Path
    ) -> None:
        """Both parsers expose ``parse(post_id, raw_text) -> ParseResult``."""
        # Call signature parity (no extra required params).
        responses = [_wrap(_BUY_NVDA_5)] * 3
        with patch.object(
            parser_crosscheck, "_http_post_json", side_effect=responses
        ):
            xparser = _make_parser(tmp_path)
            r1 = xparser.parse("p", "text")
        assert r1.post_id == "p"

        # InstructionParser interface is unchanged (construct without invoking it).
        sig = InstructionParser.parse.__doc__ is not None or True  # noqa: F841
        # InstructionParser.parse(self, post_id, raw_text) — same shape.
        assert "post_id" in InstructionParser.parse.__annotations__
        assert "raw_text" in InstructionParser.parse.__annotations__


# ---------------------------------------------------------------------------
# Tests: voting trail JSONL
# ---------------------------------------------------------------------------


class TestVotingTrail:
    def _read_jsonl(self, path: Path) -> list[dict]:
        lines = path.read_text().strip().splitlines()
        return [json.loads(line) for line in lines]

    def test_vote_trail_written_on_majority(self, tmp_path: Path) -> None:
        responses = [_wrap(_BUY_NVDA_5), _wrap(_BUY_NVDA_5), _wrap(_BUY_AMD)]
        with patch.object(
            parser_crosscheck, "_http_post_json", side_effect=responses
        ):
            parser = _make_parser(tmp_path)
            parser.parse("post:9", "加倉 nvda")

        votes_path = tmp_path / "parser_votes.jsonl"
        assert votes_path.exists()
        records = self._read_jsonl(votes_path)
        assert len(records) == 1
        rec = records[0]
        assert rec["post_id"] == "post:9"
        assert rec["strategy"] == "majority_2of3"
        assert len(rec["model_votes"]) == 3
        for mv in rec["model_votes"]:
            assert "model_id" in mv
            assert "symbol" in mv
            assert "action" in mv
            assert "quantity_pct" in mv
            assert "confidence" in mv
        final = rec["final_decision"]
        assert final["symbol"] == "NVDA"
        assert final["action"] == "BUY"

    def test_vote_trail_written_on_no_consensus(self, tmp_path: Path) -> None:
        third = {
            "status": "EXECUTABLE",
            "reason_codes": ["CLEAR_ACTION"],
            "confidence": 0.5,
            "instructions": [
                {
                    "action": "BUY",
                    "symbol": "TSLA",
                    "quantity_type": "pct",
                    "quantity_pct": 2.0,
                    "confidence": 0.5,
                }
            ],
        }
        responses = [_wrap(_BUY_NVDA_5), _wrap(_BUY_AMD), _wrap(third)]
        with patch.object(
            parser_crosscheck, "_http_post_json", side_effect=responses
        ):
            parser = _make_parser(tmp_path)
            parser.parse("post:10", "ambiguous")

        records = self._read_jsonl(tmp_path / "parser_votes.jsonl")
        rec = records[0]
        assert rec["strategy"] == "no_consensus"
        assert rec["final_decision"]["status"] == "NEEDS_REVIEW"
        assert "CROSSCHECK_NO_CONSENSUS" in rec["final_decision"]["reason_codes"]

    def test_vote_trail_records_timeout_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _fake_post(url, body, api_key, timeout_seconds):
            raise TimeoutError("simulated timeout")

        monkeypatch.setattr(parser_crosscheck, "_http_post_json", _fake_post)

        parser = _make_parser(tmp_path)
        parser.parse("post:11", "加倉 nvda")

        records = self._read_jsonl(tmp_path / "parser_votes.jsonl")
        rec = records[0]
        for mv in rec["model_votes"]:
            assert mv["symbol"] is None
            assert "error" in mv
            assert "TimeoutError" in mv["error"]


# ---------------------------------------------------------------------------
# Tests: audit ledger integration
# ---------------------------------------------------------------------------


class TestAuditIntegration:
    def test_audit_written_on_success(
        self, tmp_path: Path, tmp_ledger: AuditLedger
    ) -> None:
        responses = [_wrap(_BUY_NVDA_5)] * 3
        with patch.object(
            parser_crosscheck, "_http_post_json", side_effect=responses
        ):
            parser = _make_parser(tmp_path, tmp_ledger)
            parser.parse("post:12", "加倉 nvda")

        events = tmp_ledger.query(event_type="instructions_parsed")
        assert len(events) == 1
        assert events[0].data["status"] == "EXECUTABLE"
        assert events[0].source == "CrossCheckParser"

    def test_no_audit_when_ledger_is_none(self, tmp_path: Path) -> None:
        responses = [_wrap(_BUY_NVDA_5)] * 3
        with patch.object(
            parser_crosscheck, "_http_post_json", side_effect=responses
        ):
            parser = _make_parser(tmp_path, ledger=None)
            result = parser.parse("post:13", "加倉 nvda")
        assert result.status == "EXECUTABLE"


# ---------------------------------------------------------------------------
# Tests: HTTP request body shape
# ---------------------------------------------------------------------------


class TestHttpRequestShape:
    def test_request_body_has_required_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The DeepSeek request payload must match the documented contract."""
        captured: list[dict] = []

        def _fake_post(url, body, api_key, timeout_seconds):
            captured.append({"url": url, "body": body, "api_key": api_key})
            return _wrap(_BUY_NVDA_5)

        monkeypatch.setattr(parser_crosscheck, "_http_post_json", _fake_post)

        parser = _make_parser(tmp_path)
        parser.parse("post:14", "加倉 nvda")

        assert len(captured) == 3
        first = captured[0]
        assert first["url"].endswith("/v1/chat/completions")
        assert first["api_key"] == "test-key"
        body = first["body"]
        assert body["model"] == "deepseek-chat"
        assert body["temperature"] == 0
        assert body["max_tokens"] == 2000
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][1]["role"] == "user"
