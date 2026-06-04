---
type: decision
created: 2026-05-21
updated: 2026-06-04
tags: [decision, auto-trading, phase-3, portfolio, sizing, reconcile]
status: decided
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
- [[wiki/research/stop-the-world-mechanism-analysis]]

---

## 設計決策（2026-06-04 explore 討論）

### D1: Phase 3 邊界

Phase 3 只做 sizing 和 reconcile，不碰 Webull API：

| Phase 3 做的 | Phase 4 才做的 |
|---|---|
| `AccountDataProvider` protocol 定義 | `WebullAccountProvider`（真實現） |
| `FakeAccountProvider`（測試用） | Webull API 調用 |
| `SizingEngine`（純計算） | Order placement |
| `Reconciler`（本地 vs fake broker） | Real broker reconcile |
| 所有 8 個測試場景 | Live UAT |

### D2: `quantity_pct` 對買/賣的含義

- **買入**: `target_notional = quantity_pct × portfolio_equity`
- **賣出**: `target_quantity = quantity_pct × position.quantity`（佔**當前持倉**比例，非 equity 比例）
- **ALL**: 直接看持倉量，無歧義

### D3: Sizing 買入路徑

```
target_notional = quantity_pct × equity
→ 依次 clamp: buying_power → concentration_cap → max_notional
→ capped_notional = min(all limits)
→ raw_quantity = capped_notional / estimated_price
→ floor(lot_size) or SKIP
```

### D4: Sizing 賣出路徑

```
target_quantity = quantity_pct × position.quantity
→ floor(lot_size) or SKIP
→ 如果 > position.quantity → clip to available
→ 如果 = 0 → SKIP_NO_POSITION
```

### D5: Clamping 策略 — 鏈式 clamp，記錄所有 reason codes

多個 limit 同時觸發時，記錄**所有**觸發的 reason code（不只是最緊的）。

舉例：target $3,000，buying_power 限制 $1,000，concentration 限制 $1,500：
- `capped_notional = min(3000, 1000, 1500) = 1000`
- `reason_codes = [CLAMPED_BUYING_POWER, CLAMPED_CONCENTRATION]`

理由：buying power 不足是暫時的，concentration cap 是結構性的，兩個資訊都有審計價值。

### D6: Reconcile Tolerance

| 對帳項 | Tolerance | 理由 |
|---|---|---|
| 持倉數量 | **±0（精確匹配）** | 只做整數股，差 1 股就是真 drift |
| Buying Power | **±$1 或 0.1%，取較大值** | 即時市值/利息/費用微波動 |
| Open Orders | **order_id 集合完全匹配** | 多一個 = 意外下單風險，少一個 = 可能已成交未記錄 |

### D7: Stop-the-World 機制 — Guard 層阻斷

**主機制**: 擴展 `RuntimeGuard`，加 reconcile status flag。

```
ReconcileState: OK | MISMATCH | UNKNOWN

RuntimeGuard.assert_reconcile_ok()
  → MISMATCH 或 UNKNOWN → raise ReconcileBlockedError
  → 在 sizing 和 execution 前調用
```

**不動 WorkQueue**。Reconcile 只阻斷 sizing/execution，不阻斷 parser。

**可選 refinement**: 後期給 WorkQueue 加 `pause()` 方法，阻止 worker 浪費週期。非 MVP 必須。

**參考**: [[wiki/research/stop-the-world-mechanism-analysis]]

### D8: Reconcile 觸發時機

1. **Daemon 啟動時** — 確認基線
2. **每次 sizing 前** — 確認即時狀態

不做定時 reconcile。

### D9: Reconcile 恢復路徑

**每次發生 MISMATCH 都必須人工介入。**

```
1. reconcile mismatch → status = MISMATCH → 阻斷所有 sizing/execution
2. 寫 incident 到 portfolio/ledger.jsonl + portfolio/reconciliations/<id>.json
3. 人工: 檢查 Webull 實際持倉 vs 本地 snapshot
4. 人工: 如需要，執行 rollback（runbook Section 7）
5. 人工: 觸發 reconcile → clean pass → 人工清除 MISMATCH flag
6. status = OK → sizing/execution 恢復
```

**後續正常 reconcile pass → 保持 OK，不需要每次人工確認。**
**下次 mismatch → 又要人工。**

這等效於：runbook "Resume only after explicit clean reconcile and owner approval"。

### D10: Reconcile 輸出模型

```json
{
  "reconcile_id": "recon_...",
  "timestamp": "2026-05-20T22:30:00+08:00",
  "status": "ok | mismatch",
  "local_snapshot_hash": "sha256:...",
  "broker_snapshot_hash": "sha256:...",
  "differences": [
    {
      "field": "position.AAPL.quantity",
      "local": 10,
      "broker": 11,
      "tolerance": 0,
      "exceeded": true
    }
  ],
  "action_taken": "blocked_all_execution",
  "requires_manual_clear": true
}
```

寫入兩處：
1. `portfolio/ledger.jsonl` — append-only 事件
2. `portfolio/reconciliations/<reconcile_id>.json` — 完整差異報告

### D11: 實作分組

| Group | 組件 | 依賴 |
|---|---|---|
| 1. Models | `PortfolioSnapshot`, `Position`, `SizingDecision`, `ReconcileResult` data models | None |
| 2. Config | `SizingConfig`（buying_power_buffer, slippage, fractional 等）+ config validation | Group 1 |
| 3. Provider Protocol | `AccountDataProvider` protocol + `FakeAccountProvider` | Group 1 |
| 4. Buying Power & Sizing | `BuyingPowerCalculator`, `SizingEngine`（D3/D4/D5 買入/賣出路徑） | Groups 1-3 |
| 5. Reconciler | `Reconciler`, `ReconcileGate`（D6 tolerance, D7 stop-the-world, D9 恢復） | Groups 1-3 |
| 6. Tests & Fixtures | Fake broker snapshots, 8 個必需測試場景, portfolio ledger tests | Groups 4-5 |
