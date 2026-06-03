# Tasks: Phase 2 — Parser, LLM Client & Gold Test Set

## 1. LLM Client Adapter

- [x] 1.1 Create `src/analyzer/__init__.py`
- [x] 1.2 Implement `src/analyzer/llm_client.py` — `LLMClient` protocol with `complete_json(prompt, schema, timeout_seconds) -> dict`
- [x] 1.3 Implement `ClaudeCliClient` — subprocess wrapper calling `claude -p --bare --output-format json --tools "" --max-budget-usd 0.05`
- [x] 1.4 Implement error classes: `LLMTimeoutError`, `LLMOutputError`, `LLMSchemaError`, `LLMUnavailableError`
- [x] 1.5 Add JSON schema validation using `jsonschema` library
- [x] 1.6 Add `pydantic` + `jsonschema` to `pyproject.toml` dependencies
- [x] 1.7 Write `tests/test_llm_client.py` — cover: mock subprocess success, timeout, invalid JSON, schema mismatch, CLI not found, stderr capture, budget flag

**Estimated**: ~2 hours

---

## 2. Parser Data Models & Schema

- [x] 2.1 Implement `src/analyzer/parser_schema.py` — Pydantic models: `ParsedInstruction`, `ParseResult`
- [x] 2.2 Add `instruction_id` generation: `instr:{post_id}:{sequence}`
- [x] 2.3 Add `quantity_type` field: `Literal["pct", "all"]` with `quantity_pct: float | None`
- [x] 2.4 Add option fields: `option_type`, `option_side`, `strike`, `expiry` (all optional/nullable)
- [x] 2.5 Define JSON schema for LLM output — the schema passed to `complete_json` that the LLM must conform to
- [x] 2.6 Write `tests/test_parser_schema.py` — cover: model validation, instruction_id format, quantity_type constraints, option field combinations, invalid data rejection

**Estimated**: ~1.5 hours

---

## 3. Instruction Parser Core

- [x] 3.1 Implement `src/analyzer/context_loader.py` — load `wiki/research/christian-trading-language.md` as parser context
- [x] 3.2 Implement parser prompt template — system instruction + reference context + post text + output schema
- [x] 3.3 Implement `src/analyzer/parser.py` — `InstructionParser` class:
  - [x] 3.3.1 `parse(post_id, raw_text) -> ParseResult` — main entry point
  - [x] 3.3.2 Build prompt from template + context + post text
  - [x] 3.3.3 Call `LLMClient.complete_json()` with parser schema
  - [x] 3.3.4 Map LLM response to `ParseResult` with `ParsedInstruction[]`
  - [x] 3.3.5 Generate `instruction_id` and `idempotency_key` per instruction
  - [x] 3.3.6 Handle all LLM errors → `ParseResult(status="NEEDS_REVIEW")`
  - [x] 3.3.7 Write audit event to `AuditLedger` for every parse call
- [x] 3.4 Write `tests/test_parser.py` (mock-based) — cover:
  - [x] 3.4.1 Clear buy → EXECUTABLE with correct instruction fields
  - [x] 3.4.2 Clear sell → EXECUTABLE
  - [x] 3.4.3 Sell all → quantity_type "all"
  - [x] 3.4.4 No-op → SKIP_NOT_ACTIONABLE
  - [x] 3.4.5 Future intent → SKIP_NOT_ACTIONABLE + FUTURE_INTENT code
  - [x] 3.4.6 Conditional → SKIP_NOT_ACTIONABLE + CONDITIONAL code
  - [x] 3.4.7 Summary → SKIP_NOT_ACTIONABLE + HISTORICAL_SUMMARY code
  - [x] 3.4.8 Mixed summary + forward → SKIP_NOT_ACTIONABLE + multiple codes
  - [x] 3.4.9 Ambiguous → NEEDS_REVIEW
  - [x] 3.4.10 Multi-instruction → correct sequence order
  - [x] 3.4.11 Option long call → correct option fields
  - [x] 3.4.12 Option short call → correct option fields
  - [x] 3.4.13 Option long put → correct option fields
  - [x] 3.4.14 LLM timeout → NEEDS_REVIEW
  - [x] 3.4.15 LLM invalid JSON → NEEDS_REVIEW
  - [x] 3.4.16 Instruction ID and idempotency key stability on replay
  - [x] 3.4.17 Audit event written for success, skip, and error cases

**Estimated**: ~3 hours

---

## 4. Gold Test Set Fixtures

- [x] 4.1 Create `tests/gold_set/cases/` directory
- [x] 4.2 Write clear_buy cases (5–8 cases): simple buy, buy with time modifier, buy multiple stocks, buy leveraged ETF, buy with 解釋括號
- [x] 4.3 Write clear_sell cases (4–6 cases): simple sell, sell all, sell with percentage, cover short, cover short all
- [x] 4.4 Write no_op cases (3–5 cases): 今天沒有操作, market philosophy, operational post
- [x] 4.5 Write future_intent cases (3–5 cases): 準備下週, 計劃在, 等回調後, 等X再
- [x] 4.6 Write conditional cases (3–5 cases): 如果...會, 逢低加倉, 鑒於...如果...將
- [x] 4.7 Write summary cases (3–4 cases): weekly summary, monthly summary, strategy review
- [x] 4.8 Write mixed_summary_forward cases (3–5 cases): summary + plan, summary + conditional, 已完成 + 待執行
- [x] 4.9 Write low_confidence_ambiguous cases (3–5 cases): vague direction, unclear quantity, partial instruction
- [x] 4.10 Write multi_instruction cases (3–5 cases): inline multi, numbered list, 各N%, mixed buy+sell
- [x] 4.11 Write option_buy cases (3–4 cases): long call, long put, short put, buy with ticker format
- [x] 4.12 Write option_sell cases (2–3 cases): short call, sell call, short call with note
- [x] 4.13 Write option_cover cases (2–3 cases): cover call, cover put with ticker format

**Estimated**: ~2.5 hours

---

## 5. Test Harness

- [ ] 5.1 Implement `tests/gold_set/conftest.py` — YAML case loader: glob `cases/*.yaml`, parse, parametrize
- [ ] 5.2 Implement `tests/gold_set/test_unit.py` (Layer 1):
  - [ ] 5.2.1 Parametrized test: load case, mock LLM with expected-status-appropriate response, verify status, instructions, reason codes
  - [ ] 5.2.2 Instruction ID format verification
  - [ ] 5.2.3 Idempotency key determinism verification
  - [ ] 5.2.4 Schema validation error → NEEDS_REVIEW test
  - [ ] 5.2.5 Ensure no external dependency (no claude CLI, no network)
- [ ] 5.3 Implement `tests/gold_set/test_live.py` (Layer 2):
  - [ ] 5.3.1 Parametrized test: load case, call real ClaudeCliClient, verify with tolerances
  - [ ] 5.3.2 Status must match exactly
  - [ ] 5.3.3 Action + symbol must match exactly
  - [ ] 5.3.4 quantity_pct within ±0.1 tolerance
  - [ ] 5.3.5 Reason codes: expected subset must be present
  - [ ] 5.3.6 Confidence and parse_span recorded but not verified
  - [ ] 5.3.7 Mark with `@pytest.mark.live` skip marker (skip in CI by default)
- [ ] 5.4 Add `pytest` markers in `pyproject.toml`: `live` marker for Layer 2

**Estimated**: ~2 hours

---

## 6. Integration & Documentation

- [ ] 6.1 Run full Layer 1 test suite (`pytest tests/ -m "not live"`) and verify all pass
- [ ] 6.2 Run Layer 2 test suite (`pytest tests/gold_set/test_live.py -m live`) and record results
- [ ] 6.3 Update `wiki/architecture/auto-trading-pipeline-High-level.md` Module 2b — add explicit TA fallback policy: "Module 2b 如果 timeout / error / unavailable，結果必須是 NEEDS_REVIEW，不得產生 auto APPROVE。Parser result + basic risk 只能做 advisory reference，不能做 execution gate。"
- [ ] 6.4 Verify all Phase 1 tests still pass alongside new tests
- [ ] 6.5 Run `ruff check` and `ruff format` on all new files

**Estimated**: ~1 hour

---

## Summary

| Group | Name | Estimated | Dependencies |
|-------|------|-----------|--------------|
| 1 | LLM Client Adapter | ~2h | Phase 1 complete |
| 2 | Parser Data Models & Schema | ~1.5h | None |
| 3 | Instruction Parser Core | ~3h | Groups 1, 2 |
| 4 | Gold Test Set Fixtures | ~2.5h | Group 2 (for field reference) |
| 5 | Test Harness | ~2h | Groups 3, 4 |
| 6 | Integration & Documentation | ~1h | Groups 1–5 |

**Total estimated**: ~12 hours
