"""CrossCheckParser — 3 × DeepSeek V4 Flash parallel + 2/3 majority voting.

Output ``ParseResult`` is structurally identical to ``InstructionParser`` so
downstream stages need no changes. Voting trail appended to
``runtime/parser_votes.jsonl`` per design.md Data Model.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from src.analyzer.parser import _build_prompt
from src.analyzer.parser_schema import (
    LLM_OUTPUT_SCHEMA,
    ParsedInstruction,
    ParseResult,
)
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODEL_ID = "deepseek-chat"  # DeepSeek V4 Flash
_NUM_MODELS = 3
_WORKERS = 3
_SYSTEM_PREFIX = (
    "You are a trading instruction parser. Output ONLY raw JSON "
    "(no fences, no prose) conforming to this JSON schema:\n"
)

# ---------------------------------------------------------------------------
# Module-level HTTP + JSON helpers (testable in isolation)
# ---------------------------------------------------------------------------


def _build_system_message() -> str:
    """System message embedding the LLM output JSON schema."""
    return _SYSTEM_PREFIX + json.dumps(LLM_OUTPUT_SCHEMA)


def _build_request_body(prompt: str) -> dict[str, Any]:
    """Build the DeepSeek chat-completions request payload."""
    return {
        "model": _MODEL_ID,
        "messages": [
            {"role": "system", "content": _build_system_message()},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 2000,
    }


def _http_post_json(
    url: str,
    body: dict[str, Any],
    api_key: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """POST JSON to *url* and return parsed JSON response.

    Raises:
        TimeoutError: when the underlying socket times out.
        RuntimeError: on non-200 status, URL error, or invalid JSON body.
    """
    payload = json.dumps(body).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout_seconds) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {exc.reason}") from exc
    except urllib_error.URLError as exc:
        # socket.timeout surfaces here as URLError whose .reason is TimeoutError.
        if isinstance(exc.reason, TimeoutError):
            raise
        raise RuntimeError(f"DeepSeek URL error: {exc.reason}") from exc

    if status != 200:
        raise RuntimeError(f"DeepSeek HTTP {status}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DeepSeek returned non-JSON body: {exc}") from exc


def _extract_content_message(data: dict[str, Any]) -> str:
    """Extract the assistant message content from a chat-completions response."""
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("DeepSeek response missing 'choices'")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError("DeepSeek response missing 'message.content'")
    return content


def _parse_inner_json(content: str) -> dict[str, Any]:
    """Parse the model's content string as JSON, tolerant of ```json fences.

    Mirrors the strip-fence + first-``{`` raw_decode pattern used by the
    Claude CLI client (``llm_client._loads_maybe_fenced``).
    """
    s = content.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    start = s.find("{")
    if start == -1:
        return json.loads(s)
    obj, _ = json.JSONDecoder().raw_decode(s[start:])
    return obj


def _primary_instruction(vote: dict[str, Any]) -> dict[str, Any] | None:
    """Return the first instruction dict, or None if no instructions."""
    instructions = vote.get("instructions") or []
    return instructions[0] if instructions else None


def _vote_key(vote: dict[str, Any]) -> tuple[str, str] | None:
    """Return the (symbol, action) key for a successful model response.

    Returns None when the model returned no primary instruction (SKIP/REVIEW).
    """
    inst = _primary_instruction(vote)
    if not inst:
        return None
    sym, act = inst.get("symbol"), inst.get("action")
    if not sym or not act:
        return None
    return (str(sym), str(act))


def _new_run_id() -> str:
    """Generate a run_id matching the design.md scheme."""
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    short = uuid.uuid4().hex[:8]
    return f"{date}-xcheck-{short}"


# ---------------------------------------------------------------------------
# CrossCheckParser
# ---------------------------------------------------------------------------


class CrossCheckParser:
    """Three-way DeepSeek V4 Flash parser with 2/3 majority voting.

    Mirrors ``InstructionParser.parse(post_id, raw_text) -> ParseResult`` so
    downstream stages (orchestrator, TA fusion, sizing) require no changes.
    """

    def __init__(
        self,
        *,
        deepseek_api_key: str,
        deepseek_base_url: str = "https://api.deepseek.com",
        timeout_seconds: int = 120,
        audit_ledger: AuditLedger | None = None,
        runs_dir: str | Path = "runtime",
    ) -> None:
        self._api_key = deepseek_api_key
        self._endpoint = f"{deepseek_base_url.rstrip('/')}/v1/chat/completions"
        self._timeout = timeout_seconds
        self._ledger = audit_ledger
        self._votes_path = Path(runs_dir) / "parser_votes.jsonl"

    # -- public ----------------------------------------------------------

    def parse(self, post_id: str, raw_text: str) -> ParseResult:
        """Parse a post via 3 parallel DeepSeek calls + 2/3 majority vote."""
        run_id = _new_run_id()
        prompt = _build_prompt(self._reference_context(), raw_text)
        body = _build_request_body(prompt)

        votes = self._run_models(body)
        result, trail, strategy = self._vote(post_id, raw_text, votes)

        self._write_vote_trail(run_id, post_id, trail, result, strategy)
        self._write_audit(result)
        return result

    # -- parallel model calls -------------------------------------------

    def _run_models(self, body: dict[str, Any]) -> list[dict[str, Any] | Exception]:
        """Invoke all 3 models concurrently.

        Each slot is either a parsed response dict or an Exception
        (timeout / HTTP error / invalid JSON).
        """
        results: list[dict[str, Any] | Exception] = [
            RuntimeError("unset")
        ] * _NUM_MODELS

        def _call(idx: int) -> tuple[int, dict[str, Any] | Exception]:
            try:
                outer = _http_post_json(
                    self._endpoint, body, self._api_key, self._timeout
                )
                inner = _parse_inner_json(_extract_content_message(outer))
                inner.setdefault("model_id", f"{_MODEL_ID}-{idx + 1}")
                return idx, inner
            except Exception as exc:  # noqa: BLE001 — capture for voting
                return idx, exc

        with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
            futures = {pool.submit(_call, i): i for i in range(_NUM_MODELS)}
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    # Bound the wait by the per-call HTTP timeout + buffer.
                    idx, outcome = fut.result(timeout=self._timeout + 5)
                except Exception as exc:  # noqa: BLE001
                    outcome = exc
                results[idx] = outcome

        return results

    # -- voting ---------------------------------------------------------

    def _vote(
        self,
        post_id: str,
        raw_text: str,
        votes: list[dict[str, Any] | Exception],
    ) -> tuple[ParseResult, list[dict[str, Any]], str]:
        """Apply 2/3 majority voting. Returns (result, trail, strategy)."""
        trail = self._build_trail(votes)
        ok_votes = [v for v in votes if isinstance(v, dict)]

        # All models failed → NEEDS_REVIEW (no consensus possible).
        if not ok_votes:
            return (
                self._needs_review(post_id, raw_text, ["CROSSCHECK_LLM_ALL_FAILED"]),
                trail,
                "no_consensus",
            )

        keys = [_vote_key(v) for v in ok_votes]
        counts: Counter[tuple[str, str] | None] = Counter(keys)
        winner_key, winner_count = counts.most_common(1)[0]
        n_ok = len(ok_votes)

        # 2/3 majority threshold (or n/n when reduced to 2 by a timeout).
        threshold = 2 if n_ok >= 3 else n_ok

        if winner_count >= threshold and winner_count >= 2:
            if winner_key is None:
                # Majority agrees the post is not actionable.
                return (
                    ParseResult(
                        post_id=post_id,
                        status="SKIP_NOT_ACTIONABLE",
                        reason_codes=["CROSSCHECK_SKIP_MAJORITY"],
                        raw_text=raw_text,
                        model_id=_MODEL_ID,
                    ),
                    trail,
                    "majority_2of3",
                )
            accepting = [
                v for v, k in zip(ok_votes, keys, strict=True) if k == winner_key
            ]
            return (
                self._accept_majority(post_id, raw_text, accepting),
                trail,
                "majority_2of3",
            )

        # No 2/3 majority → NEEDS_REVIEW.
        return (
            self._needs_review(post_id, raw_text, ["CROSSCHECK_NO_CONSENSUS"]),
            trail,
            "no_consensus",
        )

    def _accept_majority(
        self,
        post_id: str,
        raw_text: str,
        accepting: list[dict[str, Any]],
    ) -> ParseResult:
        """Build the accepted ParseResult from the agreeing models.

        Uses the first agreeing model's full instruction payload (option
        fields, parse_span, time_modifier pass through) and overrides
        quantity_pct with the median across the agreeing models (design.md).
        Reuses ``InstructionParser._map_response`` so output structure is
        byte-identical to the single-parser path.
        """
        canonical = dict(accepting[0])
        canonical["status"] = "EXECUTABLE"
        canonical["reason_codes"] = canonical.get("reason_codes") or [
            "CROSSCHECK_MAJORITY"
        ]

        qtys_clean: list[float] = []
        for v in accepting:
            inst = _primary_instruction(v)
            if inst is not None and inst.get("quantity_pct") is not None:
                qtys_clean.append(float(inst["quantity_pct"]))

        instructions = canonical.get("instructions") or []
        if instructions and qtys_clean:
            new_inst = dict(instructions[0])
            new_inst["quantity_pct"] = float(median(qtys_clean))
            canonical["instructions"] = [new_inst]

        result = self._map_response(post_id, raw_text, canonical)
        result.model_id = _MODEL_ID
        return result

    def _map_response(
        self,
        post_id: str,
        raw_text: str,
        response: dict[str, Any],
    ) -> ParseResult:
        """Map LLM JSON response to ParseResult with ParsedInstructions.

        Replicates ``InstructionParser._map_response`` so output is
        byte-identical to the single-parser path.
        """
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

    def _needs_review(
        self, post_id: str, raw_text: str, reason_codes: list[str]
    ) -> ParseResult:
        return ParseResult(
            post_id=post_id,
            status="NEEDS_REVIEW",
            reason_codes=reason_codes,
            raw_text=raw_text,
            model_id=_MODEL_ID,
        )

    # -- vote trail + audit ---------------------------------------------

    def _build_trail(
        self, votes: list[dict[str, Any] | Exception]
    ) -> list[dict[str, Any]]:
        trail: list[dict[str, Any]] = []
        for idx, v in enumerate(votes):
            model_id = f"{_MODEL_ID}-{idx + 1}"
            if isinstance(v, Exception):
                trail.append(
                    {
                        "model_id": model_id,
                        "symbol": None,
                        "action": None,
                        "quantity_pct": None,
                        "confidence": 0.0,
                        "error": f"{type(v).__name__}: {v}",
                    }
                )
                continue
            inst = _primary_instruction(v)
            trail.append(
                {
                    "model_id": v.get("model_id", model_id),
                    "symbol": inst.get("symbol") if inst else None,
                    "action": inst.get("action") if inst else None,
                    "quantity_pct": inst.get("quantity_pct") if inst else None,
                    "confidence": float(v.get("confidence", 0.0)),
                }
            )
        return trail

    def _write_vote_trail(
        self,
        run_id: str,
        post_id: str,
        model_votes: list[dict[str, Any]],
        result: ParseResult,
        strategy: str,
    ) -> None:
        self._votes_path.parent.mkdir(parents=True, exist_ok=True)
        first_inst = result.instructions[0] if result.instructions else None
        if first_inst is not None:
            final_decision: dict[str, Any] = {
                "symbol": first_inst.symbol,
                "action": first_inst.action,
                "quantity_pct": first_inst.quantity_pct,
            }
        else:
            final_decision = {
                "status": result.status,
                "reason_codes": result.reason_codes,
            }
        record = {
            "run_id": run_id,
            "post_id": post_id,
            "model_votes": model_votes,
            "final_decision": final_decision,
            "strategy": strategy,
            "written_at": datetime.now(UTC).isoformat(),
        }
        with open(self._votes_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def _write_audit(self, result: ParseResult) -> None:
        if self._ledger is None:
            return
        event_type = (
            "instructions_parsed"
            if result.status == "EXECUTABLE"
            else "parse_completed"
        )
        self._ledger.append(
            AuditEvent(
                event_type=event_type,
                source="CrossCheckParser",
                data={
                    "post_id": result.post_id,
                    "status": result.status,
                    "reason_codes": result.reason_codes,
                    "confidence": result.confidence,
                    "instruction_count": len(result.instructions),
                    "model_id": _MODEL_ID,
                },
                correlation_id=result.post_id,
            )
        )

    # -- misc -----------------------------------------------------------

    def _reference_context(self) -> str:
        """Load reference context lazily; degrade gracefully if missing."""
        try:
            from src.analyzer.context_loader import load_reference_context

            return load_reference_context()
        except Exception:  # noqa: BLE001 — context is optional
            return "[Reference context unavailable]"


class _NullLLMClient:
    """Stub LLMClient for reusing ``InstructionParser._map_response``.

    Never invoked — only ``_map_response`` is called on the constructed
    instance, so ``complete_json`` is unreachable in practice.
    """

    def complete_json(
        self, *, prompt: str, schema: dict, timeout_seconds: int
    ) -> dict:  # pragma: no cover — unreachable
        raise RuntimeError("NullLLMClient.complete_json must not be called")
