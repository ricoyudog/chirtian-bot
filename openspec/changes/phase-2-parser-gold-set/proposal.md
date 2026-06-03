# Proposal: Phase 2 — Parser, LLM Client & Gold Test Set

## Why

Phase 1 建立了安全骨架（config validation、work queue、audit ledger、idempotency）。但系統還無法理解 Christian 的交易語言。Phase 2 的核心交付不是「能解析一篇文」，而是**「能穩定拒絕不該交易的文字」**。

Parser 必須在 gold test set 上證明：false-positive executable trade = P0 bug。所有無法確定判斷的結果都走 `NEEDS_REVIEW`，fail-closed。

## What Changes

1. **LLM Client adapter** — 封裝 Claude CLI (`claude -p --bare --output-format json`) 為 `LLMClient` protocol，提供 `complete_json(prompt, schema, timeout)` 介面。失敗全部 fail-closed。
2. **Instruction Parser** — 接收貼文文字 + `christian-trading-language.md` 作為 few-shot 上下文，輸出 `ParsedInstruction[]` 或 no-op。涵蓋 equity buy/sell 及 option buy/sell。
3. **Parser data models** — `ParsedInstruction`、`ParseResult` 等 Pydantic models，包含 `instruction_id`、`idempotency_key`、`quantity_type`、option fields。
4. **Gold test set** — 40–60 cases 覆蓋 12 種 case types（明確買入/賣出、no-op、未來預期、條件句、總結、混合回顧展望、低信心 ambiguous、多指令同帖、option 各類）。
5. **Two-layer test harness** — Layer 1 (mock LLM, 進 CI) + Layer 2 (live Claude CLI, nightly)。
6. **Pipeline doc fix** — 在 `auto-trading-pipeline-High-level.md` Module 2b 補明確 TA fallback policy：unavailable 不可 auto APPROVE。

## Capabilities

### New Capabilities

- `llm-client`: LLMClient protocol + ClaudeCliClient adapter — Claude CLI subprocess wrapper with schema validation, timeout, fail-closed error handling
- `instruction-parser`: Instruction parser module — takes post text → ParseResult with ParsedInstruction[], using LLM + christian-trading-language.md as context
- `parser-gold-set`: Gold test set fixtures + two-layer test harness — YAML cases, mock unit tests (CI), live integration tests (nightly)

### Modified Capabilities

_(None — Phase 2 is all new capabilities built on top of Phase 1 infrastructure.)_

## Impact

- **New code**: `src/analyzer/` module (llm_client.py, parser.py, parser_schema.py, context_loader.py)
- **New tests**: `tests/gold_set/` (cases/, test_unit.py, test_live.py)
- **Existing dependency**: Uses Phase 1's `IdempotencyGuard`, `WorkQueue`, `AuditLedger` — no modification needed
- **Wiki update**: `wiki/architecture/auto-trading-pipeline-High-level.md` Module 2b section
- **New dependency**: Requires `claude` CLI available in PATH for live tests; mock tests have no external dependency
- **Data model**: `instruction_id` generation pattern (`instr:{post_id}:{sequence}`) extends Phase 1 idempotency helpers conceptually but is a new module

## Acceptance Criteria

- Claude CLI adapter 能輸出 schema-validated JSON；timeout / unavailable → `NEEDS_REVIEW`
- Parser gold test set 覆蓋 12 種 case types，至少 40 cases
- Layer 1 mock tests 全部通過且 deterministic（CI 可跑）
- Layer 2 live tests 記錄 result，不要求 100% match（允許 tolerance）
- 低 confidence 或 schema invalid 一律 `NEEDS_REVIEW`，不得 auto approve
- False-positive executable trade = P0 bug
- Gold set replay 產生 stable `instruction_id` / `idempotency_key`
- Parser result 寫 audit event，包含 raw span、status、reason codes
- Pipeline doc TA fallback 語句已補上

## GitHub Issue

Parent issue: https://github.com/ricoyudog/chirtian-bot/issues/8

## References

- [[wiki/decisions/2026-05-21-phase-2-parser-gold-set]]
- [[wiki/decisions/2026-05-21-llm-claude-cli-first]]
- [[wiki/decisions/2026-05-21-auto-trading-completion-phases]]
- [[wiki/architecture/auto-trading-state-machine]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/architecture/auto-trading-pipeline-High-level]]
- [[wiki/research/christian-trading-language]]
- Phase 1 archive: `openspec/changes/archive/2026-06-03-phase-1-foundation-state-and-safety/`
