"""Instruction parser — converts post text to structured ParseResult via LLM."""

from __future__ import annotations

import os
from typing import Any

from src.analyzer.context_loader import load_reference_context
from src.analyzer.llm_client import (
    LLMClient,
    LLMError,
)
from src.analyzer.parser_schema import (
    LLM_OUTPUT_SCHEMA,
    ParsedInstruction,
    ParseResult,
)
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a trading instruction parser for Chinese-language trading posts from Christian.

Your job is to analyze the post text and determine if it contains executable trading \
instructions. You MUST follow the reference material for pattern recognition.

## Output Rules

1. Output valid JSON conforming to the schema provided.
2. Status must be one of:
   - "EXECUTABLE": The post contains clear, actionable trading instructions that have \
already been decided (not future intent, not conditional).
   - "SKIP_NOT_ACTIONABLE": The post contains no executable instructions. This includes: \
no-op posts, future intent (準備/打算/下週/計劃), conditional sentences (如果/逢低/跌穿才), \
historical summaries, market philosophy, and strategy reviews.
   - "NEEDS_REVIEW": You are unsure whether the post contains an executable instruction.
3. For "EXECUTABLE" posts, extract each instruction as a separate object in the \
"instructions" array. Use left-to-right textual order for sequence.
4. For option instructions, fill option_type, option_side, strike, and expiry fields.
5. "賣出全部"/"cover short 全部" → quantity_type: "all", quantity_pct: null.
6. Bracketed percentages like "賣出全部 smci（4.3%）" are informational annotations, \
NOT instruction quantities → still quantity_type: "all".
7. Posts with titles containing 總結/小結/回顧 are summaries → SKIP_NOT_ACTIONABLE.
8. Already-completed actions marked with 已/了 are past tense → SKIP_NOT_ACTIONABLE \
with reason code "PAST_ACTION".

## Action Values
- BUY: 買入, 加倉, 開始買入, 加倉做多, 開始做多
- SELL: 賣出, 賣出全部, 調倉賣出
- SHORT: 做空, short, 加倉short
- COVER: cover short, 平倉
- option_place: option buy/sell (new position)
- option_cover: closing an option position

## Reason Codes
Use these codes in reason_codes:
- CLEAR_ACTION: Clear, unambiguous trading instruction
- NO_ACTION: No trading instruction found
- FUTURE_INTENT: 計劃/準備/打算/下週/等回調後/等X再
- CONDITIONAL: 如果/逢低/逢高/跌穿才/突破才
- HISTORICAL_SUMMARY: Post is a review of past actions
- PAST_ACTION: Action already completed (已/了 markers)
- LOW_CONFIDENCE: Cannot determine intent reliably
- MULTI_INSTRUCTION: Multiple instructions in one post
"""


def _build_prompt(reference_context: str, post_text: str) -> str:
    """Build the full parser prompt (system rules + reference + post)."""
    return f"""\
{_SYSTEM_PROMPT}

---

## Output Format

Respond with ONLY a raw JSON object (no markdown fences, no prose) matching:
- status: one of "EXECUTABLE", "SKIP_NOT_ACTIONABLE", "NEEDS_REVIEW"
- reason_codes: array of reason-code strings
- confidence: number 0.0-1.0
- instructions: array, each with exactly: action (BUY|SELL|SHORT|COVER),
  symbol (string), quantity_type ("pct"|"all"), quantity_pct (number or null),
  market ("US"|"HK"), time_modifier, confidence, parse_span

Example for "賣出tsla（-1%）":
{{"status":"EXECUTABLE","reason_codes":["CLEAR_ACTION"],"confidence":0.95,
 "instructions":[{{"action":"SELL","symbol":"TSLA","quantity_type":"pct",
  "quantity_pct":1.0,"market":"US","time_modifier":"immediate","confidence":0.95,
  "parse_span":"賣出tsla（-1%）"}}]}}

---

## Reference Material

{reference_context}

---

## Post to Parse

{post_text}

---

Analyze the above post and output the JSON object."""


# ---------------------------------------------------------------------------
# InstructionParser
# ---------------------------------------------------------------------------


class InstructionParser:
    """Parse trading posts into structured instructions using LLM."""

    def __init__(
        self,
        *,
        llm_client: LLMClient,
        audit_ledger: AuditLedger | None = None,
        reference_context: str | None = None,
    ) -> None:
        self._llm = llm_client
        self._ledger = audit_ledger
        self._reference_context = reference_context

    def parse(self, post_id: str, raw_text: str) -> ParseResult:
        """Parse a post's text into a structured ParseResult.

        This is the main entry point. It:
        1. Builds the prompt with reference context + post text
        2. Calls the LLM client
        3. Maps the response to ParseResult with ParsedInstructions
        4. Generates instruction_id and idempotency_key per instruction
        5. Writes audit event
        6. Handles all LLM errors → NEEDS_REVIEW

        Args:
            post_id: Unique identifier for the post.
            raw_text: The full text content of the post.

        Returns:
            ParseResult with status, instructions, and metadata.
        """
        # Load reference context if not provided
        ref_context = self._reference_context
        if ref_context is None:
            try:
                ref_context = load_reference_context()
            except FileNotFoundError:
                ref_context = "[Reference context unavailable]"

        # Build prompt
        prompt = _build_prompt(ref_context, raw_text)

        # Call LLM
        llm_response: dict[str, Any] | None = None
        error_reason: str | None = None

        try:
            # The reference-context prompt is large; 180s is too tight under
            # load. Override via LLM_PARSER_TIMEOUT_SECONDS (default unchanged).
            parser_timeout = int(os.environ.get("LLM_PARSER_TIMEOUT_SECONDS", "180"))
            llm_response = self._llm.complete_json(
                prompt=prompt,
                schema=LLM_OUTPUT_SCHEMA,
                timeout_seconds=parser_timeout,
            )
        except LLMError as exc:
            error_reason = f"{type(exc).__name__}: {exc}"

        # Build ParseResult
        if error_reason is not None:
            result = ParseResult(
                post_id=post_id,
                status="NEEDS_REVIEW",
                reason_codes=["LLM_ERROR"],
                raw_text=raw_text,
                model_id="unavailable",
            )
        else:
            result = self._map_response(post_id, raw_text, llm_response)

        # Write audit event
        self._write_audit(result, error_reason)

        return result

    def _map_response(
        self,
        post_id: str,
        raw_text: str,
        response: dict[str, Any],
    ) -> ParseResult:
        """Map LLM JSON response to ParseResult with ParsedInstructions."""
        instructions: list[ParsedInstruction] = []

        for seq, raw_inst in enumerate(response.get("instructions", [])):
            try:
                inst = ParsedInstruction(
                    post_id=post_id,
                    sequence=seq,
                    action=raw_inst["action"],
                    symbol=raw_inst["symbol"],
                    quantity_type=raw_inst.get("quantity_type", "pct"),
                    quantity_pct=raw_inst.get("quantity_pct"),
                    market=raw_inst.get("market", "US"),
                    time_modifier=raw_inst.get("time_modifier", "immediate"),
                    scheduled_for=raw_inst.get("scheduled_for"),
                    option_type=raw_inst.get("option_type"),
                    option_side=raw_inst.get("option_side"),
                    strike=raw_inst.get("strike"),
                    expiry=raw_inst.get("expiry"),
                    confidence=raw_inst.get("confidence", 0.5),
                    parse_span=raw_inst.get("parse_span", ""),
                )
                inst.compute_keys()
                instructions.append(inst)
            except Exception:
                # If a single instruction fails validation, skip it
                # The overall result may still be valid
                continue

        # If status is EXECUTABLE but no valid instructions, downgrade
        status = response.get("status", "NEEDS_REVIEW")
        if status == "EXECUTABLE" and not instructions:
            status = "NEEDS_REVIEW"

        return ParseResult(
            post_id=post_id,
            status=status,
            instructions=instructions,
            reason_codes=response.get("reason_codes", []),
            confidence=response.get("confidence", 0.0),
            raw_text=raw_text,
            model_id=response.get("model_id", "unknown"),
        )

    def _write_audit(
        self,
        result: ParseResult,
        error_reason: str | None,
    ) -> None:
        """Write audit event for this parse."""
        if self._ledger is None:
            return

        event_type = (
            "instructions_parsed"
            if result.status == "EXECUTABLE"
            else "parse_error" if error_reason else "parse_completed"
        )

        event = AuditEvent(
            event_type=event_type,
            source="InstructionParser",
            data={
                "post_id": result.post_id,
                "status": result.status,
                "reason_codes": result.reason_codes,
                "confidence": result.confidence,
                "instruction_count": len(result.instructions),
                "error": error_reason,
            },
            correlation_id=result.post_id,
        )
        self._ledger.append(event)
