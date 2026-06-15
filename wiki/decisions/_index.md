---
type: wiki
updated: 2026-06-15
---

# 決策索引

> 重要架構、產品、運維與實作決策的入口。

## 自動交易實作階段

- [[wiki/decisions/2026-05-21-auto-trading-completion-phases|自動交易完成階段劃分]] — 5 階段實作順序與退出條件。
- [[wiki/decisions/2026-06-15-pipeline-orchestrator|端到端 Pipeline Orchestrator]] — 把 Phase 1–5 模組串成可執行 pipeline（模擬倉可下單）；含 TA 可插拔、reconcile bootstrap、修復 record_attempt 幂等 bug。
- [[wiki/decisions/2026-05-21-phase-1-foundation-state-and-safety|第 1 階段 — 基礎、狀態與安全骨架]] — scaffold、config validation、durable state、audit、安全測試，先於 broker work。
- [[wiki/decisions/2026-05-21-phase-2-parser-gold-set|第 2 階段 — Parser 黃金測試集先於自動化]] — parser 範圍、黃金測試集、fail-closed policy。
- [[wiki/decisions/2026-05-21-phase-3-portfolio-sizing-reconcile|第 3 階段 — Portfolio sizing 與對帳 gate]] — 百分比轉股數、buying power、lot size、reconcile blocking。
- [[wiki/decisions/2026-05-21-phase-4-webull-uat-executor|第 4 階段 — Webull UAT executor 只能在安全 gate 後實作]] — UAT/manual-confirm executor 與 broker unknown policy。
- [[wiki/decisions/2026-05-21-phase-5-shadow-live-gates|第 5 階段 — 任何真錢前先有影子模式觀察證據]] — shadow metrics，以及 live capital 前的 go/no-go gate。

## LLM 執行方式

- [[wiki/decisions/2026-05-21-llm-claude-cli-first|LLM 執行方式 — 優先使用 Claude CLI]] — MVP LLM adapter 以 Claude CLI 為主，失敗時 fail closed 到 review。
