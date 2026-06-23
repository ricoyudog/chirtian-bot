---
type: wiki
updated: 2026-06-23
---

# Architecture Index

> Structural insights about the codebase. Add entries as architecture knowledge is discovered.

> **狀態（2026-06）**：全鏈路已實作並實測上線（Substack → 真實 parser → TradingAgents → Webull HK paper，真實單已下）。見 [[wiki/decisions/2026-06-15-pipeline-orchestrator]]。

## Pages
- [[wiki/architecture/auto-trading-pipeline-High-level|Auto Trading Pipeline]] — 全鏈路系統架構；頂部「實作現況」為權威（設計 → 實際代碼對應表）。
- [[wiki/architecture/auto-trading-risk-gates|Auto Trading Risk Gates]] — 同日執行、TA double-confirm、no-trade/kill-switch gates。
- [[wiki/architecture/auto-trading-state-machine|Auto Trading State Machine]] — durable queue、idempotency、broker retry ambiguity、狀態轉移。
- [[wiki/architecture/implicit-contracts|Implicit Contracts]] — 實作中發現的隱性契約（SDK shim 傳輸、record_attempt、reconcile bootstrap 等）。
