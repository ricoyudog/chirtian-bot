---
type: decision
created: 2026-05-21
updated: 2026-06-05
tags: [decision, auto-trading, phase-4, webull, uat, executor]
status: decided
---

# 第 4 階段 — Webull UAT executor 只能在安全 gate 後實作

## 決策

Webull executor 在第 4 階段才實作，且只允許 UAT + manual confirmation。Prod execution 不屬於 MVP。

Executor 的責任是把已通過 parser、TA gate、risk gate、sizing、reconcile 的 `ExecutionIntent` 轉為 Webull UAT order flow。

## 開工前已鎖定決策（2026-06-05 確認）

### D4-1: Transport 層 — CLI-first

- 選擇 **方案 A: CLI adapter**（`subprocess` call `webull-skill`）。
- `BrokerClient` Protocol 定義純接口，`WebullCLIAdapter` 實現 Protocol。
- Protocol 隔離確保未來可無損切換至 MCP 或 Python import adapter。
- **Why CLI**：研究文件已有完整 CLI 範例；subprocess 最易測試（mock subprocess）；MVP 不引入 MCP server 依賴。

### D4-2: ExecutionIntent 數據模型

- 放在 `src/executor/models.py`（executor 專屬模組，不擴展 portfolio models）。
- **欄位映射**：

```
SizingDecision                 →  ExecutionIntent
─────────────────────────────────────────────────
instruction_id                 →  instruction_id (carry through)
symbol                         →  symbol
action (BUY/SELL)              →  side (BUY/SELL)
order_quantity                 →  quantity
estimated_price                →  limit_price
-                              →  execution_id (new, exec-level id)
-                              →  idempotency_key (sha256 of instruction_id + side + quantity)
-                              →  order_type (MVP 固定 LIMIT)
-                              →  environment (from RuntimeConfig)
-                              →  status (initial: "ready")
```

- **order_type**：MVP 固定 `LIMIT`（因為 `SizingDecision.estimated_price` 存在且 MARKET 會忽略定價）。
- **idempotency_key**：`sha256(instruction_id + side + str(quantity))` — instruction_id 已保證唯一，加上 side+quantity 防止同一 instruction 被 modify 後重複。
- 同時定義 `ExecutionAttempt` Pydantic model（對應狀態機文件的 JSON schema）。

### D4-3: Audit 策略 — 復用 AuditLedger

- 選擇 **復用 `src/state/ledger.py` 的 `AuditLedger`**。
- 新增 `event_type="execution_attempt"`，data payload 放 `request_hash` + `broker_order_id` + `broker_response`。
- 不新建第三個 ledger；`PortfolioLedger` 繼續用於 portfolio-level 事件。
- **Why**：AuditLedger 已有 correlation_id / event_type / data 結構，executor audit 是通用稽核的一種 event type，不需要獨立儲存。

### D4-4: Manual Confirmation — 狀態機驅動

- 選擇 **狀態機驅動**（與現有 `WorkQueue` 集成）。
- `ExecutionIntent.status` 進入 `HUMAN_REVIEW_PENDING`，由 WorkQueue 管理 lease + timeout。
- 超時後狀態變 `EXPIRED_REVIEW`，不 place order。
- 具體交互層（CLI prompt / file-based）作為獨立 adapter，不影響狀態流轉邏輯。
- operator 動作維持原決策：confirm / skip / reduce_quantity。
- reduce_quantity：operator 輸入新數量，必須 < 原始 quantity，否則 reject。

### D4-5: Task Group 分組（6 Groups）

| Group | 名稱 | 主要交付 |
|-------|------|----------|
| 1 | Executor Data Models & Protocol | `ExecutionIntent`, `ExecutionAttempt` Pydantic models; `BrokerClient` Protocol |
| 2 | Webull CLI Adapter | `WebullCLIAdapter` implements `BrokerClient`; subprocess wrapper; config/env routing |
| 3 | Order Builder & Execution Gate | `OrderBuilder` (SizingDecision→Webull order JSON); `ExecutionGate` (env guard, idempotency, ORDER_UNKNOWN) |
| 4 | Manual Confirmation Flow | 狀態機驅動 HUMAN_REVIEW_PENDING→confirm/skip/reduce→EXPIRED_REVIEW timeout |
| 5 | WebullAccountProvider | 實現 `AccountDataProvider` Protocol，用 Webull CLI 取代 FakeAccountProvider |
| 6 | Integration Tests & Smoke Checks | UAT account-list/balance/position smoke; preview/place/cancel/status; idempotency double-place guard |

## 整合方向

Adapter-first 設計：

```text
Executor -> BrokerClient interface -> WebullCLIAdapter (subprocess)
```

Business logic 不可依賴特定 transport。未來可新增 WebullMCPAdapter 或 WebullSDKAdapter。

## 必要下單流程

```text
ExecutionIntent
→ environment/account/region guard
→ manual confirmation
→ preview_order
→ place_order
→ record broker response to AuditLedger
→ poll status / reconcile fills
```

## 人工審核初始預設

MVP 初始預設：

- confirmation timeout：15 分鐘
- timeout terminal state：`EXPIRED_REVIEW`
- operator 允許動作：`confirm`, `skip`, `reduce_quantity`
- operator 預設不允許：increase quantity、widen risk limit、switch prod、bypass reconcile
- 每次 override 必須記錄 operator、timestamp、original recommendation、changed fields、reason

## Timeout 與 unknown policy

`place_order` timeout 或 ack unknown：
- state 變成 `ORDER_UNKNOWN`
- 下一步只能 `get_order_status` / open orders / reconcile
- 絕不可盲目 retry `place_order`

## 驗收標準

- UAT account-list/balance/position/open-orders smoke checks 通過。
- Preview/place/cancel/status 已在 UAT 測試。
- Manual confirmation timeout 會變成 `EXPIRED_REVIEW`，且不會 place order。
- Duplicate idempotency key 不可呼叫 broker place 兩次。
- Broker response 與 request hash 必須寫入 AuditLedger（event_type=execution_attempt）。

## 明確非目標

- 不做 prod order。
- 不做 prod auto。
- MVP 不做 options/short/HK，除非另行批准。
- 不允許 hidden retry of mutating broker calls。
- 不做 MARKET order（MVP 固定 LIMIT）。

## 相關文件

- [[wiki/research/webull-openapi-skill]]
- [[wiki/operations/auto-trading-runbook]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/architecture/auto-trading-state-machine]]
