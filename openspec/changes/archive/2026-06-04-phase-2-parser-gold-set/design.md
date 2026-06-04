# Design: Phase 2 — Parser, LLM Client & Gold Test Set

## Context

Phase 1 built the safety skeleton: config validation, SQLite work queue, JSONL audit ledger, idempotency key helpers, and runtime guards. The system can enqueue jobs, track state, and refuse unsafe operations — but it has no understanding of Christian's trading language.

Phase 2 adds the parser layer: an LLM-backed instruction parser that converts post text into structured `ParsedInstruction[]` objects, validated against a gold test set of 40–60 cases. The parser's primary deliverable is not "can parse a post" but "can reliably reject text that should not be traded."

The reference material for Christian's language patterns is in `wiki/research/christian-trading-language.md`, covering ~1297 posts with 18 long entry patterns, 9 short patterns, 14 cover/close patterns, and 8 option patterns.

---

## Goals / Non-Goals

**Goals:**

- LLMClient adapter wrapping Claude CLI with fail-closed error handling
- Instruction parser that produces schema-validated structured output
- Gold test set covering 12 case types, minimum 40 cases
- Two-layer test harness (mock unit + live integration)
- Stable `instruction_id` and `idempotency_key` on replay
- Every parse decision written to audit ledger
- Pipeline doc TA fallback clarification

**Non-Goals:**

- Portfolio sizing (Phase 3)
- Broker/Webull integration (Phase 4)
- Live polling / daemon main loop
- Hot config reload
- TradingAgents integration (later phase)
- Option execution (parser extracts, executor skips)
- Notification / external alert channel

---

## Unknowns & Investigation

### U1: LLM output non-determinism vs gold set stability

**Unknown**: LLM output varies between runs. Gold set acceptance criteria require "stable instruction_id / idempotency_key" on replay.

**Investigation**: Analyzed the dependency chain. `instruction_id` is computed from `post_id + sequence` (deterministic, no LLM involved). `idempotency_key` is computed from `post_id + sequence + action + symbol + quantity_pct` (also deterministic after LLM extraction). The LLM determines the *values* (action, symbol, qty), but once extracted, key generation is deterministic.

**Conclusion**: Keys are stable *given the same LLM output*. The two-layer test strategy handles this: Layer 1 mocks LLM (100% deterministic), Layer 2 tests real LLM with tolerance. Gold set stability means "same mock input → same keys", not "same real LLM call → same keys".

### U2: Confidence threshold value

**Unknown**: Risk gates say "low confidence → NEEDS_REVIEW" but don't define a number.

**Investigation**: LLM confidence values are not calibrated. A hard threshold (e.g., 0.8) would be arbitrary and fragile across model updates. Classification-based routing (EXECUTABLE / SKIP_NOT_ACTIONABLE / NEEDS_REVIEW) is more robust because the LLM makes the judgment call contextually rather than via a numeric boundary.

**Conclusion**: Use classification routing. LLM outputs a `status` field directly. Confidence is recorded in audit but not used for routing. Resolved as Q6 in pre-propose exploration.

### U3: "Sell all" with bracketed percentage

**Unknown**: "賣出全部 smci（4.3%）" — is 4.3% an instruction quantity or historical annotation?

**Investigation**: In Christian's writing, bracketed percentages in "賣出全部" posts consistently indicate the current position size being sold, not a new instruction quantity. The action is "sell all of this stock."

**Conclusion**: `quantity_type: "all"`, `quantity_pct: null`. The bracketed percentage is informational context from the original post. Resolved as Q3.

---

## Decisions

### D1: Claude CLI as LLM entry point

Following [[wiki/decisions/2026-05-21-llm-claude-cli-first]], use `claude -p --bare --output-format json --tools "" --max-budget-usd 0.05` via subprocess. Wrap behind `LLMClient` protocol for testability.

**Alternative considered**: Anthropic Python SDK directly — rejected per decision document; CLI is simpler for MVP, no API key management needed, and Claude Code already has auth.

### D2: instruction_id format

`instruction_id = "instr:{post_id}:{sequence}"`

Deterministic, human-readable, debuggable. Decoupled from `idempotency_key` which serves dedup, not tracing.

**Alternative considered**: Hash-based ID (`instr:{sha256[:12]}`) — rejected because it's essentially the same as `idempotency_key` with a different prefix, offering no additional value.

### D3: quantity_type field for "all" positions

Add `quantity_type: Literal["pct", "all"]` to ParsedInstruction. When `"all"`, `quantity_pct` is `null`.

**Alternative considered**: Sentinel value (`quantity_pct: -1.0` or `0`) — rejected because it overloads the field semantics and makes schema validation ambiguous.

### D4: Options parsed but not executed

Parser recognizes and structures option instructions with `option_type`, `option_side`, `strike`, `expiry` fields. These produce `EXECUTABLE` ParseResults but are filtered out before executor in later phases.

**Alternative considered**: Mark as `SKIP_NOT_ACTIONABLE` — rejected because options ARE real trading instructions. Skipping them loses audit visibility. Better to parse and filter downstream.

### D5: Classification routing over confidence threshold

LLM outputs `status` directly. Confidence is audit-only. Avoids arbitrary numeric boundaries and model sensitivity.

**Alternative considered**: Hard threshold at 0.8 — rejected due to LLM confidence miscalibration and model-update fragility.

### D6: Two-layer test architecture

Layer 1: Mock LLMClient, test parser logic (CI, deterministic). Layer 2: Real Claude CLI, test with tolerances (nightly, drift detection).

**Alternative considered**: Single layer with flaky test annotations — rejected because it conflates parser logic bugs with model behavior changes.

### D7: Multi-instruction sequence = left-to-right textual order

0-indexed sequence based on appearance order in the original text. This matches Christian's writing pattern and makes sequence numbers predictable.

### D8: Parser prompt template

The parser prompt SHALL include:
1. System instruction defining the parser's role and output schema
2. `christian-trading-language.md` as reference context
3. The post text to parse
4. Output schema specification (JSON)

The prompt template is deterministic (same template every call). Only the post text varies.

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| LLM output non-determinism causes gold set flakiness | Two-layer test strategy; Layer 1 is fully mocked and deterministic |
| Claude CLI unavailable in CI/CD | Layer 1 has no external deps; Layer 2 is manual/nightly only |
| False-positive executable trade | Gold set explicitly tests rejection cases; false-positive = P0 |
| Model update changes parser behavior | Layer 2 drift detection; gold set versioned alongside code |
| Chinese text parsing accuracy | `christian-trading-language.md` provides extensive few-shot examples; gold set covers edge cases |
| Prompt template drift across developers | Template is a single versioned file; any change requires gold set re-validation |
| Option parsing adds scope | Limited to 8 known patterns from research doc; gold set covers each |
| Mixed summary + forward-looking hardest pattern | Dedicated case type; fail-closed to NEEDS_REVIEW if uncertain |

---

## Data Model

### ParseResult

```python
class ParseResult(BaseModel):
    post_id: str
    status: Literal["EXECUTABLE", "SKIP_NOT_ACTIONABLE", "NEEDS_REVIEW"]
    instructions: list[ParsedInstruction]
    reason_codes: list[str]      # e.g., ["CLEAR_ACTION", "FUTURE_INTENT"]
    confidence: float            # Audit-only, not used for routing
    raw_text: str
    model_id: str                # Which LLM model produced this
    parsed_at: datetime
```

### ParsedInstruction

```python
class ParsedInstruction(BaseModel):
    instruction_id: str          # "instr:{post_id}:{sequence}"
    idempotency_key: str         # From Phase 1 generate_idempotency_key()
    post_id: str
    sequence: int                # 0-indexed, left-to-right
    action: Literal["BUY", "SELL", "SHORT", "COVER", "option_place", "option_cover"]
    symbol: str                  # Uppercase ticker
    market: Literal["US", "HK"] = "US"
    quantity_type: Literal["pct", "all"]
    quantity_pct: float | None   # null when quantity_type == "all"
    time_modifier: Literal["immediate", "open", "close", "scheduled"] = "immediate"
    scheduled_for: str | None = None
    # Option fields (null for equity instructions)
    option_type: Literal["call", "put"] | None = None
    option_side: Literal["long", "short"] | None = None
    strike: float | None = None
    expiry: str | None = None    # ISO date format "YYYY-MM-DD"
    # Parse metadata
    confidence: float
    parse_span: str              # The original text span that produced this instruction
```

### Gold Set Case Fixture

```yaml
case_id: "001"
category: "clear_buy"           # One of 12 case types
post_id: "substack:20260601:test-buy"
raw_text: |
  今天加倉 nvda 1%
expected_status: "EXECUTABLE"
expected_instructions:
  - sequence: 0
    action: "BUY"
    symbol: "NVDA"
    quantity_pct: 1.0
    quantity_type: "pct"
    confidence_min: 0.8
    time_modifier: "immediate"
expected_reason_codes: ["CLEAR_ACTION"]
```

---

## API Contracts

Not applicable — no API surface changes in this change. The parser is an internal module invoked via Python function calls. No HTTP endpoints, no CLI commands exposed to users.

---

## Migration Plan

No migration needed — this is a new module. Phase 1 infrastructure (WorkQueue, AuditLedger, IdempotencyGuard) is consumed as-is without modification.

---

## Open Questions

_None remaining — all resolved during pre-propose exploration (Q1–Q9)._
