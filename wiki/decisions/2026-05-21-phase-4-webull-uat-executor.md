---
type: decision
created: 2026-05-21
updated: 2026-05-21
tags: [decision, auto-trading, phase-4, webull, uat, executor]
status: proposed
---

# 第 4 階段 — Webull UAT executor 只能在安全 gate 後實作

## 決策

Webull executor 在第 4 階段才實作，且只允許 UAT + manual confirmation。Prod execution 不屬於 MVP。

Executor 的責任是把已通過 parser、TA gate、risk gate、sizing、reconcile 的 `ExecutionIntent` 轉為 Webull UAT order flow。

## 整合方向

先採 adapter-first 設計：

```text
Executor -> BrokerClient interface -> Webull adapter
```

Webull adapter 的底層預設 **CLI-first**，除非第 4 階段開始前 MCP 被證明更安全、更易測。business logic 不可依賴特定 transport。

## 必要下單流程

```text
ExecutionIntent
→ environment/account/region guard
→ manual confirmation
→ preview_order
→ place_order
→ record broker response
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
- Broker response 與 request hash 必須寫入 audit ledger。

## 明確非目標

- 不做 prod order。
- 不做 prod auto。
- MVP 不做 options/short/HK，除非另行批准。
- 不允許 hidden retry of mutating broker calls。

## 相關文件

- [[wiki/research/webull-openapi-skill]]
- [[wiki/operations/auto-trading-runbook]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/architecture/auto-trading-state-machine]]
