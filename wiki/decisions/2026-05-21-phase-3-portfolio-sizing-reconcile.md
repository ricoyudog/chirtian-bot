---
type: decision
created: 2026-05-21
updated: 2026-05-21
tags: [decision, auto-trading, phase-3, portfolio, sizing, reconcile]
status: proposed
---

# 第 3 階段 — Portfolio sizing 與對帳 gate

## 決策

在任何 executor/place-order 實作前，先完成 portfolio state、sizing、reconciliation gate。

Christian 的 `quantity_pct` 是目標風險/倉位，不是直接下單數量。Executor 只能接收已驗證的 `order_quantity`。

## 範圍

- Portfolio snapshot model
- Append-only portfolio/audit events
- Buying power calculation
- `quantity_pct -> order_quantity` sizing
- Lot size / min quantity / fractional support checks
- Concentration cap clipping
- Reconcile gate

## 硬性不變式

- 不超過可用購買力。
- 不超過 notional / quantity / concentration limits。
- 未開 fractional shares 時永遠向下取整。
- Webull/local mismatch 時 stop-the-world。
- 每個 sizing/skip/modify decision 都寫 ledger。

## 必要測試情境

- 1% 不足一股 → `SKIP_TOO_SMALL`
- buying power 不足 → clip or skip
- lot size 限制 → floor to lot or skip
- concentration cap → clip or `MODIFY_SIZE`
- sell more than position → sell available or skip
- open order conflict → review/pause
- stale quote → refresh/review
- reconcile mismatch → block all execution

## 驗收標準

- Sizing output 必須包含 target_notional、capped_notional、estimated_price、quantity、reason_codes。
- Reconcile mismatch 必須阻止所有新的 executable orders。
- Executor-facing object 只能包含具體 quantity，不可保留 unresolved percentage。
- Tests 必須可用 fake broker/account snapshots 執行，不依賴 Webull credentials。

## 相關文件

- [[wiki/architecture/auto-trading-pipeline-High-level]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/architecture/auto-trading-state-machine]]
