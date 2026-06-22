---
type: wiki
updated: 2026-06-22
tags: [hot, entry]
pinned: true
---

# Christian Bot 最新狀態

> 約 500 字 | 硬上限 600 字 | 每次 session 更新 | 人與 AI 的第一入口

## 進行中變更
- **Webull HK OpenAPI 接入完成並已實測上線**(模擬倉)。orchestrator 全鏈路經真實 broker 跑通:balance / quote / positions / preview 全部成功,place 已到達 broker。
- 首筆模擬單**僅因非交易日被擋**(週日測試 → `OAUTH_OPENAPI_NO_TRADING_DAY`)。下一個美股交易日重跑同一指令即會成交。
- 賬號 `FQGU74FVLF506T2VKVRNK7M559`(DEM 模擬倉),USD 段購買力 ~$1.13M。

## 最近決策
- [[wiki/decisions/2026-06-15-pipeline-orchestrator|端到端 Pipeline Orchestrator]] — parse→fuse→sizing→gate→place 膠水。broker 傳輸已從假設的 `webull-skill` 文本 CLI 改為 **SDK JSON shim**(見下)。
- [[wiki/decisions/2026-05-21-auto-trading-completion-phases|階段劃分]] — Phase 0–5 全完成 + orchestrator 已接線。

## 架構脈搏
- **穩定**:config/safety/parser/sizing/reconcile/executor 各模組(856 tests passed)。
- **broker 傳輸**:`scripts/webull_json.py` 持久化 shim,由 `.venv-webull/bin/python`(SDK 需 <3.14)執行,複用 webull-skill 的 `.env`+token,stdin/stdout 行 JSON;SDK 只 init 一次(避開 token 10 req/30s 限流)。`WebullCLIAdapter` 保活該 shim。
- **待整合**:`src/ingestion/`(Substack 偵測)仍未接線、未 commit;`ShadowPipeline.run()` 仍佔位。

## 最近坑點
- **webull-skill CLI 成功時只輸出文本、無 JSON 模式** → 無法程式解析;故改走 SDK shim(見 [[wiki/architecture/implicit-contracts]])。
- **每呼叫一次就重 init SDK → 觸發 token 限流(429)** → 改持久化 shim,全鏈一次 token check。
- **`OAUTH_*` 錯誤碼不是 auth 錯誤**(如 `NO_TRADING_DAY`)→ `_looks_like_auth` 收窄,別誤判。
- 模擬倉 equity 很大($8.8M),1% 即超 `max_notional_usd=$10k` → 用小 pct(如 0.1)才不會被 MODIFY_SIZE 擋。

## 最近交付
- `f25a7d9` feat(executor): Webull HK OpenAPI integration via persistent SDK shim
- `7c69b3a` docs(wiki): document end-to-end pipeline orchestrator
- `9de40a2` fix(executor): persist idempotency_key on ExecutionAttempt so dedup works
- `f9d0050` feat(pipeline): end-to-end orchestrator for paper/UAT order placement
