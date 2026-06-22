---
type: decision
created: 2026-06-15
updated: 2026-06-15
tags: [decision, auto-trading, orchestrator, pipeline, integration]
status: accepted
---

# 端到端 Pipeline Orchestrator（模擬倉可下單）

## 決策

新增 `src/pipeline/` orchestrator 包，把 Phase 1–5 各自獨立、單測全綠的模組串成一條可執行的 pipeline：

```
parse → TA fusion → snapshot → reconcile/bootstrap → sizing
     → execution gate → preview → confirm → place → record
```

在此之前，所有零件都做完且測過，但**沒有任何代碼把它們接起來**：`ingestion/`、`ta_gateway`、`decision_fusion` 零外部引用；唯一的入口 `python -m src.shadow observe …` 的 `ShadowPipeline.run()` 是佔位骨架（TA 寫死 skipped、sizing 計時空塊、broker 寫死 success）；全倉沒有運行時代碼呼叫 `place_order`。本決策補上這層膠水。

## 細節

### 新增模組
- `src/pipeline/orchestrator.py` — `TradingPipeline` + `InstructionOutcome`。擁有階段順序、reconcile-bootstrap、outcome 記帳。全程 fail-closed：TA 不可用 → `NEEDS_REVIEW`、reconcile mismatch → stop-the-world、重複 → `blocked`。
- `src/pipeline/wiring.py` — `build_pipeline()` DI 工廠（真實 Webull adapter/provider/sizing/gate/reconcile）、`--ta real|stub|skip`、`StubTAGateway`、`make_direct_instruction()`、`resolve_account()`。
- `src/pipeline/__main__.py` — CLI：`run-direct` / `run` / `status`。

### 關鍵決策

| 點 | 決策 | 理由 |
|---|---|---|
| 輸入入口 | 直接指令注入 + 真實帖文解析兩種 | 直接注入可確定性驗證下單鏈路；真實解析走完整產品路徑 |
| TA | 預設真實 `TradingAgentsGateway`，`--ta` 可切 stub/skip | 真實 TA ~30min/ticker；stub 提供即時出路；fail-closed 語義不變 |
| 確認 | 模擬倉 `confirmation_mode=auto`（跳過人工閘門） | `environment=uat + auto` 安全（guard 只硬擋 prod+auto）；真錢前改回 `confirm` |
| Reconcile | 首次本地無 baseline → 以 broker 快照 bootstrap + `mark_reconcile_ok` | 否則新帳號空本地 vs broker 持倉 → mismatch → stop-the-world，首單下不出去 |
| 帳號 ID | `WEBULL_UAT_ACCOUNT_ID` > config > 報錯 | config 的 `ACC001` 是 placeholder |

### 順帶發現並修復的 bug
- **`ExecutionGate.record_attempt()` 不存 `idempotency_key`**：`check_idempotency()` 按 `data["idempotency_key"]` 查，但 `ExecutionAttempt` 沒這欄位 → 重複下單檢測默默失效（測試靠 `_record_attempt_with_key` helper 手動塞 key 繞過）。修法：在 `ExecutionAttempt` 加 `idempotency_key` 欄位，orchestrator 改回用真正的 `record_attempt()`，並加 gate 級回歸測試。
- **`load_config()` 漏 flatten `portfolio:` 段**：之前只讀 `runtime`+`risk`，整個 portfolio 設定被默默丟棄（靠預設值巧合跑通）。已修。

### CLI

```bash
# 最快驗證下單鏈路（跳過 parser；TA 未就緒用 --ta stub）
python -m src.pipeline run-direct --symbol AAPL --action BUY --pct 1 --ta real

# 完整真實路徑：帖文 → claude 解析 → TA → sizing → 下單
python -m src.pipeline run --text "加倉AAPL 1%" --post-id smoke001 --ta real

python -m src.pipeline status   # 看 audit / order_placed / bootstrap
```

## 狀態

完成。**856 tests passed**。全鏈路已用真實 `build_pipeline` 工廠確認（fake I/O）：happy path 下單成功、重複鍵被擋、ledger 證據齊全。

**broker 傳輸已從假設的 `webull-skill` 文本 CLI 改為 Webull HK OpenAPI SDK shim**（見 [[#broker-傳輸-webull-hk-openapi]]）。**已實測上線模擬倉**：balance / AAPL quote / positions / open-orders / preview 全部成功；place 已到達 broker，唯一被擋是行事曆（非交易日測試 → `OAUTH_OPENAPI_NO_TRADING_DAY`）。下一個美股交易日重跑即成交。

## broker 傳輸（Webull HK OpenAPI）

實際帳號是 **Webull HK**（`developer.webull.hk`）模擬倉，交易美股（market=US、region_id=hk、environment=uat）。`webull-skill` CLI 成功時只輸出人類可讀文本、無 JSON 模式，無法程式解析，故：

- `scripts/webull_json.py`：**持久化 shim**，由 `.venv-webull/bin/python`（官方 SDK 需 <3.14）執行，複用 webull-skill 的 `.env`+token，stdin/stdout 行 JSON；把 SDK 回應歸一化成 provider 期望的形狀。SDK 只 init 一次（避開 token 10 req/30s 限流）。
- `WebullCLIAdapter`：保活該 shim（Popen + 行協議 + selectors 有界讀）。方法簽名不變，provider/orchestrator 不受影響。
- 憑證在 `.env`（gitignored）；plaintext `模擬倉 key.md` 已 gitignore。

**Live run 前置（環境，非代碼）**：`.venv-webull/` 已裝好 SDK + 已 2FA（token 在 `webull-openapi-skills-main/conf/`）；設 `WEBULL_UAT_ACCOUNT_ID` 即可跑。

## 相關

- [[wiki/decisions/2026-05-21-auto-trading-completion-phases|自動交易完成階段劃分]] — Phase 0–5 各模組。
- [[wiki/operations/auto-trading-runbook|運維 Runbook]] — 已加入 pipeline CLI 操作。
- [[wiki/architecture/implicit-contracts|Implicit Contracts]] — 本次發現的隱性契約。
- 後續（非本次）：把 `ShadowPipeline.run()` 重構為委託本 orchestrator，讓 shadow 觀察真正跑模擬單。
