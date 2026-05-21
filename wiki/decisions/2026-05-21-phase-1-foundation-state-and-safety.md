---
type: decision
created: 2026-05-21
updated: 2026-05-21
tags: [decision, auto-trading, phase-1, safety, state, audit]
status: proposed
---

# 第 1 階段 — 基礎、狀態與安全骨架

## 決策

第一個實作階段先建立「不會錯下單」的基礎，而不是先接 Webull 或先寫完整 daemon。

第 1 階段範圍：
- Python project scaffold / package layout
- config schema + startup validation
- runtime mode guard
- durable work queue interface
- append-only audit ledger（只追加稽核帳本） interface
- idempotency key helpers
- safety unit tests

## 原因

Auto-trading 最大風險不是功能做不出來，而是 state 不可靠、retry 錯誤、或 prod guard 漏掉。先完成 safety harness，可以讓後面 parser、sizing、executor 都掛在同一組不變式上。

## 核心契約

- `prod + auto_confirm` 永遠 hard fail。
- Mutating broker operation 預設必須 manual confirmation。
- 同一 `idempotency_key` 不可產生第二次 executable broker attempt。
- Runtime config 啟動時 validate；MVP 不支援 hot reload。
- Config hash 要寫入 audit，讓每筆 decision 可追溯當時設定。

## 狀態儲存方向

MVP 採用：
- SQLite：durable queue / leases / attempts / idempotency lookup
- JSONL：append-only audit ledger（只追加稽核帳本）
- JSON snapshot：只作可重建快取，不作 source of truth

## 拒絕方案

| 方案 | 拒絕原因 |
|---|---|
| 只用 `state.json.pending_orders` | 不足以安全支援 lease、retry、crash recovery、idempotency lookup |
| 先寫 Webull executor | broker side effect 風險太早出現，測試基礎不足 |
| Hot reload config | MVP 增加太多狀態分支；config 改動應 restart |

## 驗收標準

- Config validation tests 通過。
- State/queue 能 enqueue、lease、ack、retry_after、dead_letter。
- Audit ledger 能記錄 parser/sizing/execution/skip/reject events。
- Tests 覆蓋：
  - prod auto hard fail
  - duplicate idempotency key blocked
  - invalid environment/account/region blocked
  - config hash included in audit event

## 交接到第 2 階段

第 2 階段 parser/LLM output 只能寫入 queue/audit/state，不可直接 call broker。

## 相關文件

- [[wiki/architecture/auto-trading-state-machine]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/operations/auto-trading-runbook]]
