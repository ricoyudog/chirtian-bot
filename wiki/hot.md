---
type: wiki
updated: 2026-06-15
tags: [hot, entry]
pinned: true
---

# Christian Bot 最新狀態

> 約 500 字 | 硬上限 600 字 | 每次 session 更新 | 人與 AI 的第一入口

## 進行中變更
- **端到端 orchestrator 已完成並 commit**（`src/pipeline/`）。Phase 0–5 各模組首次串成可執行 pipeline，模擬倉可下單。
- 剩餘 blocker 僅環境前置：本機缺 `webull-skill` CLI + `WEBULL_UAT_ACCOUNT_ID`，故尚未實打模擬單。代碼鏈路已用真實工廠確認通。

## 最近決策
- [[wiki/decisions/2026-06-15-pipeline-orchestrator|端到端 Pipeline Orchestrator]] — parse→fuse→sizing→gate→place 膠水；TA 可插拔（real/stub/skip）、模擬倉 `auto` 確認、reconcile bootstrap。
- [[wiki/decisions/2026-05-21-auto-trading-completion-phases|階段劃分]] — Phase 0–5 全完成；已補「階段整合」段說明 orchestrator 接線。

## 架構脈搏
- **穩定**：config/safety/parser/sizing/reconcile/executor/shadow 各模組（單測全綠，860 passed）。
- **演進中**：`src/pipeline/` orchestrator 已上線（`run-direct`/`run`/`status` CLI）；`src/ingestion/`（Substack 偵測）仍未接線、未 commit。
- **待整合**：`ShadowPipeline.run()` 仍是佔位骨架，後續應委託本 orchestrator，讓 shadow 觀察真正跑模擬單。

## 最近坑點
- **`ExecutionGate.record_attempt()` 不存 `idempotency_key`** → 重複下單檢測默默失效。已修：`ExecutionAttempt` 加欄位（見 [[wiki/architecture/implicit-contracts]]）。
- **`load_config()` 漏 flatten `portfolio:` 段** → sizing 設定被默默丟棄（靠預設巧合跑通）。已修。
- **全新帳號 reconcile mismatch → stop-the-world** → orchestrator 首次以 broker 快照 bootstrap baseline。
- `webull-skill` 須在 PATH 且已登入；帳號經 `WEBULL_UAT_ACCOUNT_ID` 解析。

## 最近交付
- `f9d0050` feat(pipeline): end-to-end orchestrator for paper/UAT order placement
- `9de40a2` fix(executor): persist idempotency_key on ExecutionAttempt so dedup works
