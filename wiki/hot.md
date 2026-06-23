---
type: wiki
updated: 2026-06-23
tags: [hot, entry]
pinned: true
---

# Christian Bot 最新狀態

> 約 500 字 | 硬上限 600 字 | 每次 session 更新 | 人與 AI 的第一入口

## 進行中變更
- **全鏈路已接通並實測上線**(模擬倉):Substack → parser → TradingAgents → Webull。**真實下單成功**(broker order_id `037NFMNA3C80O0K8CAG8000000`)。
- **唯一待辦(環境,非代碼)**:Substack 付費 session 過期 → `poll`(自動拉最新帖)暫時拉不到。等 operator 在瀏覽器登入一次即可(見 [[wiki/operations/auto-trading-runbook|runbook]] §1.7)。`run --post-file`(本地帖)不受影響。

## 已驗證(本 session)
- ② 真實 parser(claude/glm-5.2):**修了 5 個潛伏 bug** 後可正確解析真實 Christian 帖(賣出tsla→SELL TSLA、加倉short pltr→SHORT PLTR)。見 [[wiki/decisions/2026-06-15-pipeline-orchestrator]]。
- ③ 真實 TradingAgents(DeepSeek):回傳評級(Overweight / Underweight);`ta_gateway` 注入 DEEPSEEK_API_KEY。
- ④ Webull HK broker:真實單下成功(price-tick 修正 $0.01)。AAPL 支援;**TSLA 此模擬倉不支援**(UNSUPPORTED_SYMBOL)。
- ① Ingestion:`poll` 指令 + seen-state + `process_parse_result`(避免重複 LLM 解析)。

## 最近坑點
- **`ClaudeCliClient` 之前根本沒解 claude 的 envelope/fences/budget** → 真實 LLM 從沒跑通(gold-set 測試 mock 了 client,掩蓋了)。已修。
- **`_build_prompt` 沒帶 `_SYSTEM_PROMPT`** → 模型不知輸出契約、自創格式。已修。
- **Webull HK paper 帳號不支援 TSLA**(只 AAPL 等);白名單要對齊帳號實際支援的標的。
- Substack 用 **magic-link** 登入(非驗證碼、無 captcha);session 在 `~/.config/mcp-substack/storage-state.json`。

## 最近交付
- `a63d8d1` fix(executor): round limit price to $0.01 tick
- `f1d8ac7` fix(parser): make real LLM parsing work end-to-end
- `0eef592` feat(ingestion): wire Substack → orchestrator + harden TA gateway
- `553562c` / `f25a7d9` Webull HK OpenAPI SDK shim
