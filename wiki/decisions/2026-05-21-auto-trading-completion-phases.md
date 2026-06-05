---
type: decision
created: 2026-05-21
updated: 2026-05-21
tags: [decision, auto-trading, implementation, phases]
status: proposed
---

# 自動交易完成階段劃分

## 決策

Christian Bot 自動交易實作拆成 5 個可驗收階段。每一階段都必須有明確停止條件；上一階段的安全與測試 gate 未完成，不進入下一階段。

本文件是實作順序的主要決策入口；各階段細節由下方連結的階段決策文件承接。

## 階段總覽

| 階段 | 名稱 | 主要成果 | 暫時不得做 |
|---:|---|---|---|
| 0 | 設計鎖定 | 文件矛盾收斂、OpenSpec/change 範圍準備好 | 不寫 runtime code |
| 1 | 基礎與安全骨架 | repo scaffold、設定驗證、state/queue/audit 基礎、核心安全測試 | 不接真 broker |
| 2 | Parser 與 LLM 執行方式 | Christian 指令 parser + 黃金測試集；LLM 以 Claude CLI 為主 adapter | 不把 LLM 輸出直接變成 broker order |
| 3 | Portfolio sizing 與對帳 | `quantity_pct` 轉成可執行股數；Webull/local reconcile gate | 不送出訂單 |
| 4 | UAT Executor | Webull UAT preview/place/cancel/status；人工確認；冪等執行 | 不開 prod |
| 5 | Shadow 到真錢 gate | shadow 觀察證據、kill-switch drill、小額真錢 go/no-go | 不做 prod auto |

## 開工前決策覆蓋表

| 開工前問題 | 所屬階段 | 狀態 | 解法 |
|---|---:|---|---|
| 第一個開工 slice 是什麼 | 第 1 階段 | 已決定 | 先做 foundation/state/audit/safety tests；不先接 broker |
| LLM 使用方式 | 第 2 階段 | 已決定 | [[wiki/decisions/2026-05-21-llm-claude-cli-first|優先使用 Claude CLI]]，封裝在 `LLMClient` adapter 後面 |
| Parser 黃金測試集與 fail-closed policy | 第 2 階段 | 已決定 | 第一批 30–50 case；schema/timeout/低信心 → `NEEDS_REVIEW` |
| TA timeout / fallback 矛盾 | 第 0 + 第 2 階段 | 實作前必須修正 | fallback 只能產生 review summary；TA unavailable 不可 auto approve |
| 狀態儲存選型 | 第 1 階段 | 已決定 | SQLite durable queue + JSONL append-only audit ledger（只追加稽核帳本） + 可重建 snapshot |
| 設定 ownership / reload policy | 第 1 階段 | 已決定 | 僅啟動時 validation；MVP 不支援 hot reload；config hash 寫入 audit |
| 人工審核 timeout 與 override 欄位 | 第 0 + 第 4 階段 | 初始值已決定 | 15 分鐘 timeout → `EXPIRED_REVIEW`；operator 只可 confirm / skip / reduce quantity |
| Webull integration transport | 第 4 階段 | 已決定 | CLI-first adapter；`BrokerClient` Protocol + `WebullCLIAdapter`；詳見 [[wiki/decisions/2026-05-21-phase-4-webull-uat-executor|Phase 4 決策]] |
| Portfolio sizing 在 executor 之前 | 第 3 階段 | 已決定 | Executor 只接收具體 `order_quantity` |
| Notification / alert channel | 第 5 階段外部 alert；第 1 階段 audit | MVP 最小方案已決定，live 前再選外部渠道 | MVP 需要 audit + console/runtime incident note；live capital 前必須選定並測試外部 alert |
| Prod / live capital gate | 第 5 階段 | 已決定 | Shadow evidence + drills + 另行 go/no-go decision 後，才可進 live capital |

## 階段退出條件

### 第 0 階段 — 設計鎖定
- [[wiki/architecture/auto-trading-risk-gates]] 與 [[wiki/architecture/auto-trading-pipeline-High-level]] 對 TA timeout/fallback 沒有矛盾。
- Human review timeout / allowed override fields 有明確初始值。
- 第一個 OpenSpec/change scope 小到可測、可 review。

### 第 1 階段 — 基礎與安全骨架
- Config schema 可 validate：mode、account allowlist、environment、confirmation mode、risk limits。
- `prod + auto_confirm` hard fail 有測試。
- Queue/state/audit 基礎能記錄 idempotency key、attempt、terminal state。
- 不依賴 Webull credential 也能跑完整 unit tests。

### 第 2 階段 — Parser 與 LLM 執行方式
- Claude CLI adapter 能輸出 schema-validated JSON。
- Parser 黃金測試集覆蓋 buy/sell/no-op/條件句/未來預期/低信心 ambiguous cases。
- 低 confidence 或 schema invalid 一律 `NEEDS_REVIEW`，不得自動 approve。

### 第 3 階段 — Portfolio sizing 與對帳
- Sizing tests 覆蓋 buying power clipping、lot size、round down、concentration cap、no position sell、open order conflict。
- Reconcile mismatch 會 stop-the-world。
- 所有 skip/modify/sizing decision 都寫 audit ledger。

### 第 4 階段 — UAT executor
- UAT preview/place/cancel/status 通過。
- `place_order` timeout 進 `ORDER_UNKNOWN`，下一步只查單/對帳，不重送。
- 同一 `idempotency_key` 最多一次 broker `place_order`。
- Manual confirmation timeout 可驗證。

### 第 5 階段 — 影子模式到真錢 gate
- 影子模式收集 parser/TA latency、same-day completion、skip/review rate、stale rate。
- Kill switch drill 與 rollback drill 完成。
- 小額真錢計畫另行批准；prod auto 仍 out of MVP。

## 相關決策

- [[wiki/decisions/2026-05-21-phase-1-foundation-state-and-safety]]
- [[wiki/decisions/2026-05-21-phase-2-parser-gold-set]]
- [[wiki/decisions/2026-05-21-llm-claude-cli-first]]
- [[wiki/decisions/2026-05-21-phase-3-portfolio-sizing-reconcile]]
- [[wiki/decisions/2026-05-21-phase-4-webull-uat-executor]]
- [[wiki/decisions/2026-05-21-phase-5-shadow-live-gates]]

## 相關來源文件

- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/architecture/auto-trading-state-machine]]
- [[wiki/architecture/auto-trading-pipeline-High-level]]
- [[wiki/operations/auto-trading-runbook]]
- [[wiki/product/auto-trading-prd-gap-list]]
