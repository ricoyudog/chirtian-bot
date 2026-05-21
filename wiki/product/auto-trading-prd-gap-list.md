---
type: wiki
created: 2026-05-20
updated: 2026-05-20
tags: [product, trading, prd, auto-trading]
status: draft
---

# Auto Trading PRD Gap List

> 從 [[wiki/architecture/auto-trading-pipeline-High-level|auto-trading-pipeline]] 拆出的產品需求缺口。核心產品定位：收到 Christian 明確指示後，當天完成 double-confirmed execution decision；TradingAgents 是確認閘門，不是主策略來源。

## 1. Product Goal

### Primary Goal
當 Christian 發出明確交易指示時，系統能：
1. 在同日偵測並保存帖文。
2. 解析出可交易指令。
3. 用 TradingAgents 做 double confirmation。
4. 套用硬風控與 sizing。
5. 在 UAT/MVP 階段要求人工確認後下單。
6. 對每個決策留下可審計紀錄。

### Non-goals for MVP
- 不做全自動 prod 下單。
- 不支援 options / short / HK。
- 不做多帳戶。
- 不做完整 UI dashboard。
- 不把 Christian 策略 alpha 驗證作為 MVP blocker。

---

## 2. Missing Product Requirements

### Success Criteria
需要明確定義不同層次的成功：

| Layer | Success Metric |
|---|---|
| Detection | 新帖同日偵測，無重複/無漏處理 |
| Parser | 明確操作抽取正確，低信心進 review |
| TA confirmation | TA green/yellow/red/unavailable 明確可追蹤 |
| Execution | UAT preview/place 成功，無重複單 |
| Safety | reconcile mismatch / stale signal / timeout 會停單 |
| Audit | 任一 order 可回溯到 post + instruction + decision |

### Personas / Roles
MVP 可先定義為單一 operator：
- `Operator`: 你本人，負責確認 order、處理 review、切換模式。
- `Risk Owner`: 同一人也可以，但文件要明確標出風控參數 owner。
- `Ops Owner`: 負責看 alert、停機、恢復。

### Human-in-the-loop Policy
需要補：
- 哪些狀態必須人工確認？
- 確認 timeout 多久？
- timeout 是 cancel、queue、還是 escalate？
- 使用者可修改哪些欄位？quantity、limit price、skip reason？
- override 是否必須寫 audit？答案應為 yes。

---

## 3. User Journeys

### Happy Path
```text
New Christian post
→ parser extracts BUY NVDA 1%
→ TA green
→ portfolio reconciled
→ sizing executable
→ user confirms
→ Webull UAT preview/place
→ audit complete
```

### No-op Path
```text
New Christian post
→ parser finds no concrete trade
→ mark NO_OP
→ audit: checked, no action
```

### TA Not Green Path
```text
Christian BUY
→ TA yellow/red/unavailable
→ NEEDS_REVIEW or REJECT
→ no auto order
```

### Stale Signal Path
```text
Post detected late
→ signal age exceeds configured window
→ SKIP_STALE_SIGNAL
→ audit reason
```

### Reconcile Fail Path
```text
Before order, Webull positions != local snapshot
→ RECONCILE_FAILED
→ stop all auto orders
→ user resolves / resyncs
→ resume only after explicit clean reconcile
```

### Broker Unknown Path
```text
place_order timeout
→ ORDER_UNKNOWN
→ query broker order status
→ reconcile
→ never blindly retry place_order
```

---

## 4. Metrics / Dashboard Needs

MVP can be file/log based, but metrics should be defined now.

### Pipeline Health
- poll success rate
- detection latency
- parse latency
- TA latency
- queue depth
- same-day completion rate

### Decision Quality
- parser confidence distribution
- NEEDS_REVIEW rate
- TA green/yellow/red/unavailable rate
- stale signal rate

### Execution Quality
- preview success rate
- place success rate
- order unknown count
- duplicate prevented count
- fill / cancel / reject count

### Safety
- reconcile mismatch count
- kill switch triggers
- prod guard blocked count
- manual override count

### Trading Observation
- signal age at execution
- expected vs actual order price
- slippage
- cost estimate
- post-trade PnL observation

---

## 5. PRD Sections to Add

- Product Goal & Non-goals
- Personas & Ownership
- Human Review Policy
- Alert & Notification Policy
- Error Message Catalog
- Audit Query Requirements
- Config Management Policy
- MVP Scope
- Later Scope
- Go/No-Go Checklist

---

## 6. MVP vs Later

### MVP
- UAT only
- US equities only
- buy/sell only
- single account
- single worker
- manual confirmation required
- TradingAgents double confirmation required for auto path
- append-only ledger/audit

### Later
- prod mode
- options
- shorting
- HK market
- fractional shares
- multi-account
- full dashboard
- strategy performance attribution
