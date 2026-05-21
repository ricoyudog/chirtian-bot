# Proposal: Phase 1 — Foundation, State & Safety Skeleton

## What Changes

建立 auto-trading 系統的 Python 基礎骨架，讓後續 parser、sizing、executor 都掛在同一組安全不變式上。第 1 階段不接 broker、不接 LLM、不做 daemon — 只做「不會錯下單」的基礎。

具體交付：

1. **Python project scaffold** — `pyproject.toml`、package layout、dev tooling（pytest、ruff）
2. **Config schema + startup validation** — Pydantic models 驗證 runtime mode、environment、account、risk limits；啟動時 fail fast
3. **Runtime mode guard** — `prod + auto_confirm` hard fail；mutating operation 預設 manual confirmation
4. **Durable work queue interface** — SQLite-backed queue：enqueue、lease、ack、retry_after、dead_letter
5. **Append-only audit ledger interface** — JSONL 格式，記錄所有 pipeline events（parser/sizing/execution/skip/reject）
6. **Idempotency key helpers** — 穩定 key 生成、duplicate check、同一 key 最多一次 executable broker attempt
7. **Safety unit tests** — 覆蓋所有 core invariants

## Why

Auto-trading 最大風險不是功能做不出來，而是 state 不可靠、retry 錯誤、或 prod guard 漏掉。

從 [[wiki/architecture/auto-trading-state-machine]] 和 [[wiki/architecture/auto-trading-risk-gates]] 的分析，核心 hard invariants 是：
- 同一篇 post 重跑不會重複下單
- crash 後不漏 signal
- broker ack unknown 時不可直接 retry `place_order`
- 本地與 Webull 不一致時 stop-the-world
- `prod + auto_confirm` 永遠 hard fail

先完成 safety harness，可以讓後續每個模組（parser、sizing、executor）掛在同一組不變式上，而非各自實作錯誤處理。

## Scope

### In Scope
- Python package scaffold under `src/`
- Config models + validation
- Runtime mode guard
- Work queue interface (SQLite)
- Audit ledger interface (JSONL)
- Idempotency key generation + dedup check
- All safety unit tests
- 不需要 Webull credential 也能跑完整 test suite

### Out of Scope
- Webull / broker integration（第 4 階段）
- LLM / Claude CLI parser（第 2 階段）
- Portfolio sizing & reconcile（第 3 階段）
- Daemon main loop
- Notification / external alert channel
- Hot config reload

## Acceptance Criteria

- Config validation tests 通過：mode、account allowlist、environment、confirmation mode、risk limits
- `prod + auto_confirm` hard fail 有測試且通過
- Queue 能 enqueue、lease、ack、retry_after、dead_letter
- Audit ledger 能 append 事件、不可修改已有事件
- 同一 `idempotency_key` 第二次 enqueue 會被 blocked 或 deduplicated
- Config hash 寫入 audit event
- Tests 覆蓋：prod auto hard fail、duplicate idempotency key blocked、invalid environment/account/region blocked、config hash in audit
- 整個 test suite 不需要外部 credential 即可執行

## GitHub Issue

_To be filled after issue creation._

## References

- [[wiki/decisions/2026-05-21-phase-1-foundation-state-and-safety]]
- [[wiki/decisions/2026-05-21-auto-trading-completion-phases]]
- [[wiki/architecture/auto-trading-state-machine]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/architecture/auto-trading-pipeline-High-level]]
- [[wiki/operations/auto-trading-runbook]]
