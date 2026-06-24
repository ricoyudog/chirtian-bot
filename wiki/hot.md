---
type: wiki
updated: 2026-06-24
tags: [hot, entry]
pinned: true
---

# Christian Bot 最新狀態

> 約 500 字 | 硬上限 600 字 | 每次 session 更新 | 人與 AI 的第一入口

## 進行中變更
- **全鏈路在真實 Christian 帖上端到端跑通**(2026-06-24):真實帖 `2025-07-24`→parser(claude)→TradingAgents(DeepSeek)→fusion→白名單/broker 閘門,每段真實、安全門正確觸發。真實 TA 現對 AAPL/TSLA 打 `Underweight`→反對 BUY→正確擋下(fail-closed)。
- **真實單在 paper 帳號**:AAPL BUY 14 @ 295.77,order `037NNQ2UO080O0K8CAG8000000`(PENDING)。因 TA 看空擋 BUY,該單以 `run-direct --ta skip` 下。
- **更正先前高估**:舊 `037NFMNA...` 單是 run-direct(**未經 parser** 的直注),非 polled/解析帖;「解析帖→單」直到 2026-06-24 才跑通。
- Webull HK paper 帳號**僅支援 AAPL**;TSLA/PLTR/SMCI/NVDA 等全 `UNSUPPORTED_SYMBOL`。Ingestion + Substack auth gate 正常,見 [[wiki/operations/auto-trading-runbook|runbook]] §1.7。

## 最近坑點
- **Parser 硬依賴自建網關 `sub2api-production-4d3a.up.railway.app`**(`~/.claude/settings.json` `ANTHROPIC_BASE_URL`)。2026-06-24 回 **502「Upstream access forbidden」**→parser/`poll`/`run --post-file` 全癱到網關恢復。**非代碼問題**。
- **Webull 4 bug(2026-06-24 已修)**:① open-orders 字段錯層(真實字段在 `o["orders"][0]`+`total_quantity`→snapshot 遇掛單崩)② order_detail 要 `client_order_id` 非 `order_id` ③ run-direct `--post-id` 沒傳進(永遠 `instr:direct:0` 撞舊單)④ parser timeout 寫死 180s(改 `LLM_PARSER_TIMEOUT_SECONDS` env)。

## 最近交付
- 2026-06-24 修上列 4 bug + `scripts/probe_broker_support.py` 只讀診斷;測試 **136 passed 無回歸**。
- `a63d8d1` price-tick / `f1d8ac7` parser / `0eef592` Substack→orchestrator / `553562c`+`f25a7d9` Webull shim。
