---
type: decision
created: 2026-05-21
updated: 2026-05-21
tags: [decision, auto-trading, phase-5, shadow, prod, live-gate]
status: accepted
---

# 第 5 階段 — 任何真錢前先有影子模式觀察證據

## 決策

UAT executor 完成後，先進 shadow/evidence phase。任何 live capital 或 prod mode 都要另過 go/no-go gate，不因 UAT 成功自動開啟。

## Phase 4 UAT 與 Phase 5 的關係

不需要獨立的 UAT 階段。模擬倉本身就是測試環境 — Phase 5 的模擬倉觀察期同時涵蓋 UAT 驗證。核心流程（偵測 → 解析 → TA 確認 → 下單）在模擬倉跑通即可。

## 影子模式（以模擬倉代替）

Webull 帳戶目前為模擬倉，因此不需要額外建影子模式。直接用模擬倉跑實戰等級測試即可：

- 真實下單流程，但無真錢風險
- 真實延遲數據（TA、解析、執行）
- 真實訂單狀態（可驗證 reconcile、duplicate prevention）

觀察期：**1 週 + 至少 10 個訊號處理**。若 1 週內訊號不足，自動延長至滿足門檻，最長 4 週。若 4 週仍未達 10 個訊號，先暫停檢討訊號來源。

必要觀察指標：
- detection latency
- parse latency
- Claude CLI latency/error rate
- TA latency / unavailable rate
- same-day completion rate
- stale signal rate（pipeline 延遲導致，目標 ≤5%；週末訊號算 deferred 不算 stale）
- NEEDS_REVIEW rate
- skip/reject/modify reasons
- duplicate prevented count
- reconcile mismatch count

## 告警與通知決策點

MVP 在真錢前可先使用：
- console output（終端輸出）
- append-only audit ledger（只追加稽核帳本）
- 在 runtime/incidents 或等效本地路徑建立帶日期的 incident note

任何真錢前，必須明確選定並測試 alert channel。可接受候選包括：有 operator 主動盯盤的 terminal-only、Telegram/Discord/email，或其他已記錄渠道。若沒有測試過 alert channel，live capital = `NO_GO`。

**Alert channel 測試標準**：必須完成端到端演練 — 從模擬偵測異常、觸發 kill switch、alert 送達、到 operator 確認處理，全流程驗證。單純發一條測試訊息不算通過。

## 小額真錢前的 go/no-go

**決策者：operator（即專案 owner）。** 決策必須記錄在 `wiki/decisions/`，作為審計軌跡。

進入小額真錢前：
- kill switch drill 已完成
- rollback drill 已完成
- alert channel 已測試
- manual review workflow 已測試
- 沒有未解決的 `ORDER_UNKNOWN`
- 沒有 duplicate order incident
- reconcile 狀態乾淨
- risk limits 已明確批准

## 真錢邊界

若日後批准：
- 只允許 US liquid equities
- 只允許 buy/sell
- 不允許 options
- 不允許 short
- 不允許 HK
- 使用小額 notional cap
- 每次 scale 不超過前一級 2x

## 拒絕方案

| 方案 | 拒絕原因 |
|---|---|
| UAT 成功後直接 go prod | UAT 不足以證明 real-time data / latency / ops behavior |
| 第一個 live phase 就 prod auto | irreversible side-effect risk 太高 |
| 把 TradingAgents 當 alpha proof | Project framing 是 Christian 作為策略來源；TA 是 confirmation gate |

## 驗收標準

- Shadow run summary 需以帶日期 note 形式存在。
- Incident/kill-switch drill note 需存在。
- 任何真錢前，go/no-go decision 必須記錄在 `wiki/decisions/`。

## 相關文件

- [[wiki/operations/auto-trading-runbook]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/product/auto-trading-prd-gap-list]]
