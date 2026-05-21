---
type: wiki
created: 2026-05-20
updated: 2026-05-20
tags: [architecture, trading, risk, gates, auto-trading]
status: draft
---

# Auto Trading Risk Gates

> 從 [[wiki/architecture/auto-trading-pipeline-High-level|auto-trading-pipeline]] 拆出的風控與上線 gate。核心目標不是證明 Christian 策略本身，而是：收到 Christian 指示後，當天能在安全條件下下單；TradingAgents 作為 double confirmation，綠燈才 go。

## 0. Scope Clarification

### 目標
- Christian 發出明確交易指示後，系統能在同日內完成解析、風控、double confirmation、sizing、下單或跳過。
- TradingAgents 不是策略發明者，而是 **second-opinion gate**：
  - Christian 指示明確；
  - TradingAgents 方向同意或不反對；
  - 所有硬風控通過；
  - 才允許進入下單流程。

### 非 P0 目標
- 不把「證明 Christian 策略有 alpha」當作第一階段 blocker。
- 不要求 MVP 先完成完整投資績效歸因。
- 不要求 TradingAgents 證明比 Christian 原策略更好。

### 仍需保留的投資風險觀察
即使不把策略 edge 當 blocker，也仍要記錄：
- 成本後 PnL
- 滑點
- signal age
- Christian 指示與實際成交偏差
- TradingAgents 擋下/放行後的後續表現

---

## 1. Hard No-Trade Gates

以下任一條件成立，系統必須 `NO_TRADE` 或 `NEEDS_REVIEW`，不得自動下單。

| Gate | 觸發條件 | 行為 |
|---|---|---|
| Parser confidence | 解析低信心、方向/數量/標的不確定 | `NEEDS_REVIEW` |
| TradingAgents unavailable | TA timeout、API error、資料源 degraded | `NEEDS_REVIEW`，不得 fail-open |
| TA red light | TA 明確反對 Christian 方向 | `NEEDS_REVIEW` 或 `REJECT` |
| Stale signal | 指示已超過同日可接受時間窗 | `SKIP_STALE_SIGNAL` |
| Reconcile mismatch | 本地 snapshot 與 Webull 不一致 | stop-the-world |
| Broker ambiguity | place order timeout / ack unknown | 查單與對帳，不可重送 |
| Duplicate risk | 同 post/instruction/order idempotency key 已處理 | skip duplicate |
| Open order conflict | 同 account + symbol 有未完成衝突單 | pause / review |
| Quote stale | 報價超時或缺 bid/ask | refresh or review |
| Liquidity fail | spread / lot size / min notional 不合格 | skip or review |
| Buying power fail | 可用買力不足最小交易單位 | skip |
| Concentration fail | 超出單一持倉/組合限制 | clip or reject |
| Environment fail | 非 UAT、account mismatch、region mismatch | hard fail |
| Prod unsafe | prod + auto confirmation | hard fail |

---

## 2. Recommended Kill Switches

### System Kill Switch
以下任一事件發生，全局停用 auto order：
- 任一 reconcile mismatch 未解決。
- 任一 unexpected fill / orphan order。
- 同一 broker operation 連續 2 次 reject。
- 偵測到重複下單。
- Webull account / region / permission 不符合預期。
- config 被手動修改但未通過 reload validation。

### Market/Data Kill Switch
- quote stale。
- FX 缺失。
- market session 不符。
- 停牌、不可交易、無 market data permission。
- short borrow unavailable。
- option chain / greeks / spread 缺資料（options later phase）。

### Risk Kill Switch（建議，真錢前啟用）
- 日內虧損超過 NAV 1%。
- 5 日累積虧損超過 NAV 2.5%。
- peak-to-trough drawdown 超過 5%。
- 單一標的集中度超過配置上限。

---

## 3. Same-Day Execution Gate

因目標是「當天能下單」，每筆 signal 都應帶 `signal_age`。

| Signal Type | 建議最大年齡 | 超時行為 |
|---|---:|---|
| immediate | 30–60 分鐘 | `SKIP_STALE_SIGNAL` |
| open | 開盤後指定窗口 | 超時 review |
| close | 收盤前指定窗口 | 超時 skip |
| scheduled | 到指定時間前仍有效 | 到期後 skip |
| no explicit time | 當日收盤前 | 收盤後 skip |

> 具體時間窗可後續調整，但必須顯式配置，不可讓舊 signal 自動下單。

---

## 4. Phase Gates

### Phase 0 — Thesis / Policy Gate
- 明確寫入：策略來源是 Christian；TA 只做 double confirmation。
- 明確寫入：TA unavailable 不等於放行。
- 明確寫入：MVP 是 UAT-only、human-confirmed。

### Phase 1 — Parser Gold Set Gate
- 真實歷史帖文建立 gold set。
- 錯方向 / 錯數量 false positive = P0 bug。
- 低信心、條件句、預期句必須進 `NEEDS_REVIEW` 或 skip。

### Phase 2 — Workflow Safety Gate
- replay 同一 post 不重複下單。
- crash recovery 不漏單。
- broker timeout 不直接 retry。
- reconcile mismatch stop-the-world。

### Phase 3 — UAT Gate
- UAT preview/place/cancel/status 全流程通過。
- 所有 ledger/audit event 可追蹤。
- kill switch drill 通過。

### Phase 4 — Shadow Gate
- 只產生 decision，不真實下單。
- 觀察 parser、TA latency、signal age、skip/review rate。
- 驗證同日完成率。

### Phase 5 — Micro-Capital Gate（真錢小額）
- 只允許 US liquid equities。
- 禁 options、short、HK。
- 每次 scale 不超過前一級 2x。

---

## 5. Acceptance Criteria

MVP 可接受標準：
- `prod + auto_confirm` 永遠 hard fail。
- TA timeout/error 永遠不自動下單。
- 同一 `idempotency_key` 永遠最多一次 broker `place_order`。
- 每個 skip/reject/modify 都寫 ledger。
- 每筆 order 可追溯到 post、instruction、TA verdict、sizing decision、broker response。
- 任一 reconciliation mismatch 會阻止所有新單。
