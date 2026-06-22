---
type: wiki
updated: 2026-06-15
---

# Implicit Contracts

> 開發中發現的未明文規則。每條說明「違反會怎樣」。來源：[[wiki/decisions/2026-06-15-pipeline-orchestrator]]。

## Contracts

### 1. `ExecutionAttempt` 必須帶 `idempotency_key`
`ExecutionGate.check_idempotency()` 以 audit event 的 `data["idempotency_key"]` 查重，故 `record_attempt()` 寫出的 `ExecutionAttempt` 必須帶這欄位（`src/executor/models.py`）。

- **違反會怎樣**：重複 `place_order` 偵測默默失效 —— 同一指令可被下兩次（曾經的 bug，已修；見 `tests/test_executor_integration.py::test_record_attempt_blocks_duplicate`）。

### 2. 全新帳號 reconcile 會 stop-the-world
本地 `PortfolioLedger` 無 baseline 時，`ReconcileGate` 拿空本地 vs broker 持倉比對 → mismatch → `RuntimeGuard.activate_stop()` → 擋全部下單。

- **違反會怎樣**：模擬倉首單下不出去。
- **解法**：orchestrator 首次以 broker 快照 bootstrap baseline + `mark_reconcile_ok()`（`src/pipeline/orchestrator.py::_reconcile_or_bootstrap`）。真錢前應改為顯式 `sync` + 人工核對。

### 3. `load_config()` 必須 flatten `portfolio:` 段
`RuntimeConfig.portfolio`（`SizingConfig`）來自 YAML 的 `portfolio:` 區塊；`load_config()` 必須把它攤平進 config（`src/config/validation.py`）。

- **違反會怎樣**：`buying_power_buffer`、`price_slippage_buffer_pct`、`require_reconcile_before_sizing` 等被默默丟棄，sizing 跑預設值（曾經靠預設巧合跑通，已修）。

### 4. broker 傳輸 = Webull HK OpenAPI SDK shim（不是 webull-skill 文本 CLI）
`WebullCLIAdapter` 保活 `scripts/webull_json.py`（由 `.venv-webull/bin/python` 執行，官方 SDK 需 <3.14），經 stdin/stdout 行 JSON 交換；shim 複用 webull-skill 的 `.env`（app_key/secret、region=hk、env=uat）+ token（`webull-openapi-skills-main/conf/`），把 SDK 回應歸一化成 provider 期望的形狀。帳號由 `WEBULL_UAT_ACCOUNT_ID` > `config.account_ids` 解析（`src/pipeline/wiring.py::resolve_account`）。

- **為何不直接用 webull-skill CLI**：它成功時只輸出人類可讀文本、無 JSON 模式，無法程式解析。
- **為何持久化 shim**：每呼叫重 init SDK 會觸發 token check，10 req/30s 限流 → 429。SDK 只 init 一次即避開。
- **違反會怎樣**：`.venv-webull` 未裝 / token 過期 → `sdk init failed`（重做 `webull-skill auth` 2FA）；帳號未設 → resolve 報錯。
- **`OAUTH_*` 錯誤碼不是 auth 錯誤**：如 `OAUTH_OPENAPI_NO_TRADING_DAY`（非交易日）是業務拒單，`_looks_like_auth` 已收窄避免誤判。

### 5. `RuntimeGuard` 只硬擋 `prod + auto`
`assert_safe_to_run()` / `assert_mutation_allowed()` 只在 `environment == "prod" and confirmation_mode == "auto"` 時 hard fail；`uat + auto` 允許（模擬倉免人工）。`mode` 欄位本身**不**用於攔下單，只用於 MVP 允許清單檢查。

- **違反會怎樣（誤解）**：誤以為 `uat_confirm` 必須 `confirm` → 模擬倉被過度限制；或誤以為可 `prod + auto` → 真錢無閘門自動下單。
