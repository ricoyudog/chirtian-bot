---
type: decision
created: 2026-06-29
updated: 2026-06-30
tags: [decision, auto-trading, ops, deploy, dashboard, scheduling, telegram, sizing, risk, scope]
status: accepted
---

# 生產化部署、調度 Daemon 與觀測 Dashboard

## 決策

新增「**調度層**」與「**觀測層**」兩個零侵入外掛層，讓 Christian Bot 從 operator 手動跑 `python -m src.pipeline poll/run` 升級為**常駐、定時、可觀測、可告警**的生產化運行形態。全程保持 `uat_confirm + paper`，不碰真錢。小額真錢為 Stage B，單獨過 Phase 5 go/no-go。

```
調度層（自動按按鈕的人）              觀測層（純只讀）
┌─────────────────────┐      ┌─────────────────────┐
│  poll daemon (60s)  │      │  FastAPI dashboard   │
│  Telegram bot       │      │  run record JSONL    │
│  kill switch /stop  │      │  metrics / SSE       │
│  drill callback     │      │  safety status       │
└──────┬──────────────┘      └──────────┬──────────┘
       │                                │
       │  複用現有 pipeline              │  只讀 runtime/*.jsonl
       │  + RuntimeGuard                │  + shadow_state.db
       ▼                                ▼
┌─────────────────────────────────────────────┐
│        現有安全層（完全不動）                  │
│  RuntimeGuard / idempotency / reconcile     │
│  kill-switch / fail-closed / audit ledger   │
└─────────────────────────────────────────────┘
```

## 現狀與缺口

Christian Bot 已端到端跑通（[[wiki/hot]] 2026-06-24），但運行形態完全是 operator 手動：

| 缺口 | 現狀 | 影響 |
|---|---|---|
| 無常駐進程 | `python -m src.pipeline poll` 手動執行 | 無法自動捕捉 Christian 發帖 |
| 無定時調度 | 無 cron / daemon | 錯過帖文窗口即丟失信號 |
| 無 `run_id` | Pipeline 每次執行無結構化 run record | 無法回溯某次 poll 的結果、無法按 run 聚合 metrics |
| 無 dashboard | 全靠 CLI `status` / `audit` 手動查 | 無法一眼看到系統是否健康 |
| 無告警 channel | 錯誤只印 stderr | operator 不在電腦前即完全無感知 |
| 無部署腳本 | 每次重啟需手動重建環境 | 不可復現、不可審計 |

**核心問題**：現在所有零件都做完且測過，但**沒有任何代碼讓它在背景持續運行**。

## 核心安全原則

> **調度層 = 自動按按鈕的人；觀測層 = 純只讀。兩者都不修改任何一行安全代碼。**

1. **不修改一行安全代碼**：`RuntimeGuard`（`src/safety/runtime_guard.py`）、idempotency（`ExecutionGate.check_idempotency()`）、reconcile（`ReconcileGate.check_and_gate()`）、kill-switch（`RuntimeGuard.activate_stop()`）、fail-closed 全部保持不變。daemon 自動觸發 poll → pipeline 會撞上與手動執行**完全同一套 guard**。

2. **`config.yaml` 維持 `uat_confirm + auto`**：`mode: uat_confirm`、`environment: uat`、`confirmation_mode: auto`。`prod_*` 組合仍被 `assert_safe_to_run()`（`src/safety/runtime_guard.py:44-48`）**硬擋**——即使有人誤改 config，guard 也會 raise `RuntimeError` 阻止啟動。

3. **調度層不做決策**：daemon 只負責「定時呼叫 poll_once → pipeline」，不做 signal 判斷、不做 sizing、不下單。所有決策仍在 `TradingPipeline` 內，受既有 fail-closed 保護。

4. **觀測層純只讀**：dashboard 只 tail `runtime/*.jsonl` + 讀 `shadow_state.db`（SQLite WAL 模式，並發安全），唯一可操作入口是 kill switch（寫 `runtime/kill_switch.flag`，由 `RuntimeGuard` 在下一個 tick 讀取並 stop-the-world）。

5. **真錢分階段**：Stage A（本次）全程 paper；Stage B 小額真錢需單獨過 Phase 5 go/no-go gates（kill switch drill 端到端驗證、alert channel 就緒、rollback 驗證）。

## 細節

### 分階段 Milestone

#### M1：結構化 run record + run_id

**新建**：`src/ops/run_record.py`

- `RunRecorder`：每次 pipeline 執行產生唯一 `run_id`（`{date}-{seq}-{uuid[:8]}`），記錄 `started_at`、`ended_at`、`mode`、`signals_processed`、`orders_placed`、`errors`、`outcome`。
- 寫入 `runtime/runs.jsonl`（append-only JSONL，與 `audit_ledger.jsonl` 同模式）。
- **複用**：`AuditLedger` 的 append JSONL 模式（`src/state/ledger.py:15-26`）；`AuditEvent` 結構（`src/state/models.py:30-37`）。
- dashboard、metrics、告警全部以 `run_id` 為查詢鍵。

#### M2：常駐 poll daemon

**新建**：`src/ops/daemon.py`、`src/ops/__main__.py`

- `python -m src.ops` 啟動 daemon。
- **Tick 邏輯**：每 60s 調用 `poll_once()`（`src/ingestion/poll.py:10-42`）——無新帖即返回空 list，零開銷。
- **重入鎖**：`runtime/daemon.lock`（`fcntl.flock` / `msvcrt.locking`），防止雙開。
- **SIGTERM 軟停**：收到信號後完成當前 tick 再退出，不中斷進行中的 pipeline。
- **崩潰恢復**：依靠既有 `processed_posts.json`（`ProcessedPostStore`，`src/ingestion/seen_store.py:11-46`）+ idempotency key（`ExecutionGate.check_idempotency()`）保證重啟後不重複處理。
- **心跳**：每個 tick 寫 `runtime/daemon_heartbeat.json`（`{"last_tick": "ISO8601", "pid": int, "status": "ok"}`），dashboard 藉此判斷 daemon 存活。
- **異常隔離**：單次 poll 崩潰不殺 daemon——catch 所有例外，寫 audit event + 繼續下個 tick。

#### M3：Telegram 告警

**新建**：`src/notify/telegram.py`、`src/notify/bot.py`

- **Telegram Bot**（`python-telegram-bot`）：paper+auto 模式下**不綁定每筆訂單確認**（orchestrator 在 `confirmation_mode=auto` 時不調 `ConfirmationManager`，`src/pipeline/orchestrator.py:295-307`），只服務三件事：
  1. **失敗告警**：pipeline 任何 stage 報錯 → 推播訊息（含 run_id、錯誤摘要）。
  2. **kill switch `/stop`**：operator 在 Telegram 發 `/stop` → bot 寫 `runtime/kill_switch.flag` → daemon 下個 tick 前檢查 → `RuntimeGuard.activate_stop("operator_kill_switch")` → stop-the-world。
  3. **drill `confirm_callback`**：升級 `AlertDrillRunner.run_drill()`（`src/shadow/drill.py:43-109`）為 operator-in-the-loop——drill 觸發時 bot 向 operator 請求確認，operator 在 Telegram 回覆 → `confirm_callback` 返回 operator 確認時間戳 → drill 判定 PASS/FAIL。此舉滿足 Phase 5「kill switch drill 端到端」驗收標準。
- **不接 ConfirmationManager**：`ConfirmationManager`（`src/executor/confirmation.py`）是 in-memory 狀態機（ready → human_review_pending → ready | cancelled），paper+auto 下用不到。Telegram 不與其耦合，留給 Stage B 真錢 `prod_confirm` 模式時再評估。

#### M4：FastAPI 觀測 dashboard

**新建**：`src/dashboard/app.py` + `src/dashboard/static/`

- **只讀數據源**：
  - `runtime/runs.jsonl`（run 歷史）
  - `runtime/audit_ledger.jsonl`（事件流）
  - `runtime/portfolio_ledger.jsonl`（持倉事件）
  - `runtime/daemon_heartbeat.json`（daemon 心跳）
  - `runtime/kill_switch.flag`（是否存在）
  - `runtime/shadow_state.db`（SQLite WAL，並發安全讀取）
- **路由**：

| 路由 | 功能 | 數據源 |
|---|---|---|
| `/` | Dashboard 主頁（HTML） | `static/index.html` |
| `/api/runs` | Run 列表 + 摘要 | `runs.jsonl` |
| `/api/runs/{run_id}` | 單次 run 詳情 | `runs.jsonl` + cross-ref `audit_ledger.jsonl` |
| `/api/metrics` | 延遲 p50/p95、信號數、stale rate | 複用 `MetricsCollector.generate_report()`（`src/shadow/metrics.py:117-166`） |
| `/api/safety` | RuntimeGuard 狀態、reconcile status、kill switch 狀態 | `RuntimeGuard.is_stopped`（`src/safety/runtime_guard.py:127-129`）+ `kill_switch.flag` |
| `/api/events/tail` | SSE 即時事件推送 | tail `audit_ledger.jsonl` 新行 |
| `/api/health` | Daemon 心跳 + dashboard 自身健康 | `daemon_heartbeat.json` + `{"status": "ok"}` |

- **唯一可操作入口**：`POST /api/kill-switch` → 寫 `runtime/kill_switch.flag` → 下個 tick `RuntimeGuard.activate_stop()`。

#### M5：Docker 部署

**新建**：`Dockerfile` + `docker-compose.yml`

```yaml
# 三 service，共享 runtime/ volume
services:
  daemon:     # python -m src.ops（poll daemon）
  dashboard:  # uvicorn src.dashboard.app:app
  bot:        # python -m src.notify.bot（Telegram）
```

- `runtime/` 為 Docker named volume，三 service 共用（daemon 寫、dashboard 讀、bot 讀寫 `kill_switch.flag`）。
- `.env` 注入 secrets（`TELEGRAM_BOT_TOKEN`、`WEBULL_UAT_ACCOUNT_ID` 等）。
- `restart: unless-stopped` + `healthcheck` 確保崩潰自動重啟。

### 複用點

| 複用點                                             | 來源                                                        | 用法                                            |
| ----------------------------------------------- | --------------------------------------------------------- | --------------------------------------------- |
| `poll_once()`                                   | `src/ingestion/poll.py:10-42`                             | daemon tick 直接調用，無帖即返回空 list                  |
| `build_pipeline()`                              | `src/pipeline/wiring.py:116-216`                          | daemon 啟動時建構一次，同 `cmd_poll` 裝配                |
| `ProcessedPostStore`                            | `src/ingestion/seen_store.py:11-46`                       | 崩潰恢復靠 `processed_posts.json` + idempotency    |
| `MetricsCollector.generate_report()`            | `src/shadow/metrics.py:117-166`                           | dashboard `/api/metrics` 直接複用                 |
| `AlertDrillRunner.run_drill(confirm_callback=)` | `src/shadow/drill.py:43-109`                              | Telegram bot 提供 operator-in-the-loop callback |
| `AuditLedger` / `AuditEvent`                    | `src/state/ledger.py:10-71` / `src/state/models.py:30-37` | RunRecorder 複用 append JSONL 模式                |
| `ObservationStateStore`                         | `src/shadow/state.py:19-199`                              | dashboard 讀取 SQLite WAL，無需改碼                  |
| `RuntimeGuard`                                  | `src/safety/runtime_guard.py:29-135`                      | daemon 與 dashboard 都只讀/只寫 flag，不修改 guard 邏輯   |
| `TradingPipeline`                               | `src/pipeline/orchestrator.py`                            | daemon 原封不動調用，所有 fail-closed 語義不變             |

## 關鍵決策

| 點 | 決策 | 理由 |
|---|---|---|
| daemon 節奏 | 每 60s poll 一次 | 用戶拍板「每分鐘檢查有沒有發帖」；`poll_once` 無帖即返回，輕量零開銷；貼合 Christian 按日發帖頻率（遠低於 rate limit） |
| dashboard 形態 | FastAPI 輕量 Web | 用戶拍板；數據已結構化落盤（JSONL + SQLite）是核心優勢，無需外加 TSDB；輕量 Web 比 Grafana+Prometheus 更快落地 |
| 告警 channel | Telegram bot | 用戶拍板；含 `confirm_callback` 可對接 kill switch drill，滿足 Phase 5 operator-in-the-loop 標準 |
| 部署姿態 | Stage A 全程 paper，真錢分階段 | 用戶拍板「兩者都要，分階段」；Stage A 先驗證 24/7 運行穩定性、告警就緒、drill 通過；Stage B 小額真錢需單獨 go/no-go |
| confirmation 不接 Telegram | paper+auto 下用不到 ConfirmationManager | `confirmation_mode=auto` 時 orchestrator 不調 `ConfirmationManager`（`src/pipeline/orchestrator.py:295-307`）；避免 in-memory 狀態機複雜化；留 Stage B 再評估 |
| 全天 poll | 盤外下單由現有 fail-closed risk gate 自然擋 | 不增加交易時段判斷——既有 gate 鏈（`RuntimeGuard.assert_mutation_allowed()` + sizing `SKIP_STALE_QUOTE`）提供基礎防護；後續可選擇性加 `trading_session_filter`（2026-06-30 更正：`check_environment()` 只檢 `environment=="uat"`，不含 market hours；防護來自他處） |
| run_id 方案 | `{date}-{seq}-{uuid[:8]}` append JSONL | 人類可讀 + 唯一；append 模式與 `AuditLedger` 一致，效能無虞 |
| parser cross-check | 3 × DeepSeek V4 Flash 並行 + 2/3 多數決 | parser 層缺乏抽取結果的獨立驗證——LLM hallucination 可能讀錯 symbol，TA fusion 無法救（TA 驗證技術面而非文字理解）；並行確保不增加延遲；2/3 多數決避免一致決過緊；0/3 一致時上升 Telegram operator |
| TA 並行化 | `ThreadPoolExecutor` 並行分析多 symbol；sizing 保持串行 | Christian 一帖可推多股，串行 TA 可能衝破收盤（3 股 × ~15min = 45min vs 收盤前 ~1hr 窗口）；TA 各 symbol 完全獨立可安全並行；sizing/order 必須串行以保證 portfolio snapshot 一致性 |
| DeepSeek V4 Flash 選擇 | parser 採用 DeepSeek V4 Flash 而非繼續 GLM-5.2 | 用戶拍板「已經夠聰明」；與 TA（DeepSeek V4 Pro）同供應商降低依賴面；低成本適合 3× 並行呼叫 |

## 拒絕方案

| 方案 | 拒絕理由 |
|---|---|
| 立即推進 `prod_confirm` 小額真錢 | 需先補齊 kill switch/rollback drill、alert channel 端到端測試等多個 Phase 5 gate（見 [[wiki/decisions/2026-05-21-phase-5-shadow-live-gates]]）；本階段先 paper 生產化，真錢為 Stage B |
| daemon 內嵌下單確認流程 | `auto` 模式下 orchestrator 不調 `ConfirmationManager`；daemon 只是「自動按按鈕」，不應承擔確認職責；無謂複雜化 |
| Grafana + Prometheus | 遠超 MVP 形態；數據已 JSONL 落盤，無需外加 TSDB + exporter；輕量 FastAPI dashboard 更快落地（可作未來選項，待規模化後再引入） |
| 修改 `RuntimeGuard` 以放行 daemon | 任何放行都破壞 fail-closed 語義；`assert_safe_to_run()` 的硬擋（`prod + auto → RuntimeError`）是設計保障，不可接受 |
| 用 crontab 代替 daemon | crontab 無重入鎖、無心跳、無優雅停機、無狀態共享；Python daemon 可與 pipeline 共享進程內狀態，且可統一 SIGTERM 處理 |
| dashboard 直接呼叫 broker API 查詢 | 破壞觀測層「純只讀落盤數據」原則；broker API 有 rate limit（10 req/30s），dashboard 查詢可能觸發限流；應只消費本地 JSONL/SQLite |

## Phase 0 — 開工前計劃缺口修補

> 2026-06-30 Agent Team Review 全面審查後補充，2026-06-30 逐項討論完成。M1–M5 的**架構設計**合理，但 Phase 5 gate 覆蓋、Docker 依賴聲明、API 路由與 prototype 匹配、parser 安全、TA 並行化、tick-abort 等方面有缺口。以下 11 項已逐一討論、決定、記錄。所有 checkbox 勾選後 → 進入 M1。

### P0-1：Kill Switch Drill — 強制 operator-in-the-loop

**問題**：`AlertDrillRunner.run_drill()` 在 `confirm_callback=None` 時以 `datetime.now()` 偽造 operator 確認 → auto-pass。若 Telegram bot（M3）未就緒或當機，drill 仍 PASS。**Phase 5 要求**（[[wiki/decisions/2026-05-21-phase-5-shadow-live-gates]] line 50）是「端到端演練 — 從模擬偵測異常、觸發 kill switch、alert 送達、到 operator 確認處理」，auto-pass 不滿足此標準。

**修補**（擇一）：(A) 將 `run_drill()` 的 `confirm_callback` 改為強制參數——不傳入即 drill FAIL；(B) 在 M2/M3 之間加 milestone gate：M3 Telegram callback 接好並端到端驗證後，drill 才算有效。

**→ 已選定 (A)**：fail-fast at code level，`None` 即 `FAILED`，不可偽造；與 Phase 5 二值判定（PASS/FAIL）精神一致。

- [x] 改 `src/shadow/drill.py:run_drill()`：`confirm_callback` 為強制參數，None 時 return `DrillResult(result="FAILED", failure_reason="NO_CONFIRM_CALLBACK")`
- [x] M3 完成後：用真實 Telegram callback 跑一次 drill，確認 PASS

### P0-2：Rollback Drill — 補充設計

**問題**：Phase 5 gate 要求「rollback drill 已完成」，但本計劃全文 **0 次**提及 rollback。這是 Phase 5 最大的單一缺口。

**修補**：新增 **M6 Rollback Drill**（建議納入 M5 Docker 部署一併處理）：

- [x] 場景 1：回滾一張已下的 paper 訂單（`cancel_order` + audit 記錄）
- [x] 場景 2：回滾 daemon config 到已知良好狀態（`config.yaml` rollback + daemon 重啟）
- [x] 場景 3：Docker rollback（`docker compose down && docker compose up`，保留 `runtime/` volume，驗證 daemon 恢復正常）
- [x] 所有 drill 結果記錄到 `runtime/incidents/`

### P0-11：Parser Cross-Check — 三模型並行抽取 + 多數決

**問題**：目前 parser extraction 是**單次 LLM 調用**（GLM-5.2，經 `claude` CLI subprocess），無抽取結果的獨立驗證。若 LLM hallucination 將 symbol 讀錯（如 NVDA → NFLX），TA fusion 會老老實實分析錯誤標的——TA 驗證的是「技術面是否支持交易」，而非「帖文是否被正確理解」。Parser 層和 TA 層保護的是**不同的安全邊界**。

**修補**：Parser 層引入 **3 模型並行抽取 + 2/3 多數決 cross-check**。

- [x] **模型選擇**：DeepSeek V4 Flash（已驗證對 Christian 交易語言理解力足夠）
- [x] **並行調用**：3 次獨立 `subprocess.run`（`ThreadPoolExecutor`），總延遲 ≈ 最慢單次
- [x] **不一致策略（Q1 決定）**：
  - symbol + action **2/3 一致** → 以多數為準，qty 取多數或中位數
  - **0/3 一致**（三個全不同）→ `NEEDS_REVIEW` + Telegram 通知 operator
- [x] **解析邏輯**：新建 `src/analyzer/parser_crosscheck.py`，封裝 `CrossCheckParser`（內部並行調用 3 個 DeepSeek Flash instance → 比對 → 產出最終 `ParseResult` 或 `NEEDS_REVIEW`）
- [x] **資料層**：每次 cross-check 的 raw 輸出寫入 `runtime/parser_votes.jsonl`（含 3 個模型各自的 symbol/action/qty/confidence，便於回溯 audit）
- [x] **與 P0-3 互補**：Parser cross-check 保護「抽取正確性」；TA 強制性（P0-3）保護「TA 不可跳過」。兩者共同閉合 `--ta skip` 時的防護真空

**與既有解析的關係**：

- `InstructionParser`（`src/analyzer/parser.py`）保持不變，仍為 GLM-5.2 單次調用
- `CrossCheckParser` 作為**替代進入點**：daemon 走 cross-check 路徑；operator 手動 `cmd_parse` 仍可走既有路徑（保留對比基線）
- Pipeline 下游（orchestrator → TA fusion → sizing）只接收最終 `ParseResult`，不感知上游如何產生

**設計決定**：

| 點 | 決定 | 理由 |
|---|---|---|
| 模型 | DeepSeek V4 Flash | 足夠聰明、低成本、與 TA（DeepSeek V4 Pro）同供應商降低依賴面 |
| 調用方式 | 3 × 並行 subprocess | 不讓 cross-check 實質增加端到端延遲 |
| 多數決策略 | 2/3 一致即採納 | 避免一致決過緊（每帖都要人審）；0/3 時才上升 operator |
| 不一致記錄 | `parser_votes.jsonl` | 可回溯 audit：哪個模型投了什麼、最終決定為何 |

### 關聯發現：TA fusion 串行化 — 多 symbol 延遲堆疊

> 此為既有實作缺陷，非 Phase 0 缺口，但與 P0-11 同屬延遲優化範疇，一併記錄。

**問題**：`orchestrator.py:167` 用列表推導式逐個處理 instruction，每個 `_fuse()` 內 `subprocess.run(TA, timeout=1800s)` 為 blocking 調用。一帖多股（如 NVDA + AMD + MSFT）時，TA 串行執行：

```
TA(NVDA) ──~N min──→ TA(AMD) ──~N min──→ TA(MSFT) ──~N min──→ ...
```

Christian 通常在美東 3pm 前發帖，若 TA 單次實際耗時 ≥15min，三股總延遲 ≥45min，可能衝破收盤（4pm），後續 symbol 的訂單在盤後執行或無法成交。

**修補**：

- [x] TA 階段改**並行**（`ThreadPoolExecutor`）：各 symbol 的 TA 分析完全獨立（無共享狀態），可安全並行；總延遲 ≈ 最慢單次
- [x] Sizing + order 階段**保持串行**：sizing 依賴 portfolio snapshot（buying power），order 寫入 portfolio ledger——並行會導致重複扣減 buying power、超買
- [x] 兩階段分離：`process_parse_result()` 拆為 Phase 1（並行 TA）→ Phase 2（串行 sizing/order）

### P0-3：TA Fusion 強制性 — 代碼層強制

**問題**：計劃決定移除 `symbol_whitelist` 的**前置條件**是「TA fusion 須改 mandatory」。但 `orchestrator.py:384` 在 `ta_gateway is None` 時直接 `FUSION_APPROVE`。若 `--ta skip` + 空白名單同時成立，所有 symbol 零閘門通關。安全不變量應由機器強制，不能只靠文件。

**修補**：在 `build_pipeline()` 或 `RuntimeGuard.assert_safe_to_run()` 中加入：

- [x] 斷言：`ta_gateway is None AND len(symbol_whitelist) == 0 → RuntimeError("TA must be mandatory when whitelist is empty")`
- [x] 此檢查在 daemon 啟動時執行，fail-fast

### P0-4：Daemon Dead-man Switch

**問題**：有心跳檔（`daemon_heartbeat.json`），但**無人監控心跳是否停止更新**。daemon OOM kill / Docker restart loop 耗盡 → dashboard 顯示過時狀態，無告警。Telegram bot 自己也是 Docker service，可能跟 daemon 一起掛。

**修補**：

- [x] Docker `healthcheck` for daemon：檢查 `daemon_heartbeat.json` 年齡 ≤ 120s
- [x] Docker `healthcheck` for bot：檢查 Telegram bot process 存活 + API 連通
- [x] 可選：外部 health check（cron on host / healthchecks.io webhook）作為獨立告警 channel
- [x] Dashboard `/api/health` 回傳 `stale: true` 當心跳過期（前端顯示紅條）

### P0-5：Daemon 熔斷器（Circuit Breaker）

**問題**：M2 說「catch 所有例外，繼續下個 tick」。若 Substack gateway 502（已知痛點，[[wiki/hot]]），daemon 會**永久靜默失敗**。100 次連續失敗 tick 也不觸發任何告警。

**修補**：

**→ 已選定 (C)**：連續 5 次失敗 = 系統性故障（非 transient），寫 `kill_switch.flag` + Telegram 告警 + daemon 退出；符合 fail-closed 原則。

- [x] Daemon 加入連續失敗計數器（`consecutive_failures`）
- [x] 連續 N=5 次失敗後：發 Telegram 告警 + 寫 `runtime/kill_switch.flag`
- [x] 任何一次成功 tick → 重置計數器

### P0-6：Docker 依賴完整聲明

**問題**：`.env` 範例只提到 `TELEGRAM_BOT_TOKEN`、`WEBULL_UAT_ACCOUNT_ID`，實際上容器還需要：

| 隱含依賴 | 用途 |
|---|---|
| `claude` CLI + `ANTHROPIC_API_KEY` | Parser LLM |
| Node.js + `mcp-substack` | Substack polling |
| `storage-state.json` | Substack 付費 session（需手動生成，cookies 會過期） |
| `.venv-webull/` + Webull SDK + auth token | 所有下單操作 |
| `DEEPSEEK_API_KEY` + `TradingAgents/` venv | TA deep confirm（`--ta real` 時） |

**修補**：

**→ Substack `storage-state.json`：選定 (A) Host bind-mount**。Headless browser in container 不現實（CAPTCHA/2FA）。Host 瀏覽器匯出 → bind-mount `:ro` 進 container。Cookie 過期檢測用**語義層**（連續 N=6 次 poll 零帖 + 不符合 Christian 發帖時段模式 → Telegram 告警），而非依賴檔案 mtime。

**→ Claude CLI：保留於 Docker container**。Daemon 走 DeepSeek cross-check（P0-11），但 operator 手動 `cmd_parse` / `cmd_run` 仍需 Claude；DeepSeek 全掛時 Claude 為 parser fallback。

- [x] 提供完整 `.env.example`（含所有 env var，標註必須 vs 可選）
- [x] Dockerfile 中明確安裝 Node.js、Claude CLI、DeepSeek SDK、Webull SDK、mcp-substack
- [x] 文件化哪些需預先手動配置：
  - Substack session：Host 瀏覽器登入 → `npx playwright open --save-storage=...` 匯出 `storage-state.json`
  - Webull token：`webull login` → 持久化 token，過期需重登
  - Claude auth：`claude login` 或 `ANTHROPIC_API_KEY`
  - DeepSeek API key：`DEEPSEEK_API_KEY`（同 TA 用）
- [x] Substack `storage-state.json` 過期檢測 + 重新認證 SOP（寫入 `SETUP.md`）

### P0-7：Dashboard API 路由擴充

**問題**：`wiki/dashboard-prototype.html` 需要以下數據，但計劃 M4 的 7 個路由未覆蓋：

| Prototype 面板 | 需要的數據 | 當前狀態 |
|---|---|---|
| Substack Posts feed | 貼文列表、parsed signal、連結 run_id | ❌ 無路由 |
| Positions & Allocation | 即時持倉、市值、PnL、分配 % | ❌ 無路由 |
| Pipeline Latency per-stage | 每階段 p50/p95（detect/parse/llm/ta/sizing/exec/broker） | ⚠️ `/api/metrics` 可能粒度不足 |
| 四心跳卡片 | daemon + dashboard + bot + RuntimeGuard 各自心跳 | ⚠️ 只有 daemon 有心跳檔 |

**修補**：

**→ Positions 數據策略：選定「Daemon 調 broker API → 寫本地 SQLite → Dashboard 只讀 SQLite」**。Broker 為 ground truth，reconcile 可能有不一致但 broker raw 數據不會。Daemon 每 tick（60s）調一次 broker API 查持倉，完美在 rate limit（10 req/30s）內。Dashboard 只讀本地 SQLite，不觸 broker API，不違反觀測層原則。

SQLite schema（新建 `runtime/positions.db`，與既有 `shadow_state.db` 共存）：
```
position_snapshots (snapshot_id, run_id, tick_at, symbol, position_qty, market_value, unrealized_pnl, pnl_pct)
```
Dashboard `/api/positions` 直接 `SELECT ... WHERE tick_at = MAX(tick_at)`，毫秒級。

- [x] 新增 `GET /api/posts`：從 `processed_posts.json` + cross-ref `runs.jsonl`
- [x] 新增 `GET /api/positions`：daemon 每 tick 調 broker API 拉即時持倉 → 寫 `runtime/positions.db` → dashboard 只讀 SQLite
- [x] `RunRecorder`（M1）預留 `stage_timings` 欄位，供 `/api/metrics` 產出 per-stage p50/p95
- [x] 驗證 `MetricsCollector.generate_report()` 產出 per-stage latency 粒度；若不夠，擴充
- [x] 四心跳：dashboard `/api/health` 合併回傳 daemon + dashboard + bot + RuntimeGuard 狀態；bot 需定期寫 `runtime/bot_heartbeat.json`

### P0-8：JSONL 輪替 / 備份 / 磁碟防護

**問題**：24/7 運行下 `runs.jsonl` + `audit_ledger.jsonl` + `portfolio_ledger.jsonl` 每月 ~17MB，無上限增長最終撐爆磁碟。無備份策略。

**修補**：

**→ JSONL 保留 13 個月**（跨年度對比需求：今年 7 月 vs 去年 7 月的交易模式）。

**→ 備份不用 cronjob**：SQLite 本身做 housekeeping（`positions.db` 跑 `DELETE ... WHERE tick_at < datetime('now', '-30 days')`；`shadow_state.db` 同理）。JSONL 按月輪替保留 13 個月，舊檔由 daemon 啟動時 purge（`find runtime/ -name 'runs-20*.jsonl' -mtime +395 -delete`）。

- [x] JSONL 按月輪替：`runs-2026-07.jsonl`，月初自動切換，保留 13 個月
- [x] `positions.db`：SQL housekeeping，每天 purge 超過 30 天的 row（`DELETE ... WHERE tick_at < date('now', '-30 days')`）
- [x] `shadow_state.db`：同上，合理保留窗口（待與既有 schema 對齊後決定）
- [x] Daemon 啟動時清理過期 JSONL（超過 13 個月）
- [x] Docker service `mem_limit` 設定（daemon 1GB，dashboard 256MB）
- [x] SQLite `PRAGMA integrity_check`：daemon 啟動時對 `shadow_state.db` + `positions.db` 執行，任一 fail → 拒絕啟動

### P0-9：Dashboard 安全

**問題**：`POST /api/kill-switch` 無認證。任何人能訪問端口即可觸發 kill switch。

**修補**：

- [x] Dashboard bind `127.0.0.1`（非 `0.0.0.0`）
- [x] 若需遠端訪問：SSH tunnel 或 reverse proxy with auth
- [x] Docker Compose 不 expose dashboard port 到 host（`expose` 而非 `ports`，只供內部網路）

### P0-10：Docker 信號與生命週期

**問題**：Docker `stop_grace_period` 預設 10s。M2 設計「收到 SIGTERM → 完成當前 tick → 退出」，但 TA 分析是 blocking `subprocess.run(timeout=1800s)`。Docker 10s 等不到 → SIGKILL 硬殺 → TA subprocess 變孤兒、`runs.jsonl` 半條記錄、`daemon.lock` 未釋放。

**核心矛盾**：延長 `stop_grace_period` 無法解決——TA 可達 30min，不可能設 1800s。需要 tick-abort。

**→ Tick-Abort 設計（必須，非可選）**：

```
SIGTERM → threading.Event.set() → pipeline 各 stage 檢查:
  parser (10-30s):  等完成
  TA (30min):       若 event.is_set() → SIGTERM 給子進程 → available=False
  sizing (<1s):     等完成
  order (<5s):      等完成

所有 stage 完成/abort → 寫 run record (ended_at + reason="SIGTERM_ABORT") → 釋放 lock → 退出
```

TA 被 abort 時：`ta_gateway.analyze()` 回傳 `available=False`（fail-closed），當前 instruction 標記 `TA_UNAVAILABLE`，非 error 而是 abort。總清理時間 ≤15s。

**修補**：

- [x] Daemon `stop_grace_period` ≥ 120s（清理 ≤15s，buffer 充裕）
- [x] Tick-abort mechanism：`threading.Event`，pipeline 各 stage 檢查；TA stage 收到 abort → SIGTERM 子進程
- [x] `docker-compose.test.yml`：`mode: offline_replay` + stubbed 依賴，CI 驗證三 service health check 通過
- [x] 操作驗收標準：
  - 三 service 30s 內 healthy
  - Kill switch 2 tick 內生效
  - Daemon crash → 10s 內自動重啟（`restart: unless-stopped` + healthcheck `interval=10s, retries=1`）
  - Volume 持久化：`docker compose down && up` 後 run 歷史保留

### Phase 0 決策彙總

| # | 項目 | 性質 | 關鍵決定 |
|---|---|---|---|
| P0-1 | Kill Switch Drill | Safety gate | (A) `confirm_callback` 強制，`None`=FAIL；M3 後端到端驗證 |
| P0-2 | Rollback Drill | Safety gate | 新增 M6：回滾訂單、回滾 config、Docker 回滾三場景 |
| P0-3 | TA Fusion 強制性 | Safety invariant | `ta_gateway is None AND whitelist=[] → RuntimeError`，daemon 啟動時 fail-fast |
| P0-4 | Dead-man Switch | Reliability | 三層：Docker healthcheck + dashboard stale 檢測 + 外部獨立告警（Stage B 必須） |
| P0-5 | Circuit Breaker | Reliability | (C) 連續 5 次失敗 → kill_switch.flag + Telegram 告警 + daemon 退出；成功歸零 |
| P0-6 | Docker 依賴 | Deployment | Substack session: host bind-mount (A)；Claude CLI 保留於 container；DeepSeek SDK 新增 |
| P0-7 | Dashboard 路由 | Observability | Positions: daemon 調 broker → 寫 `positions.db` → dashboard 只讀 SQLite；M1 預留 `stage_timings` |
| P0-8 | JSONL 輪替/備份 | Operations | SQL housekeeping 非 cronjob；JSONL 保留 13 個月按月輪替；DB 30 天滾動 purge |
| P0-9 | Dashboard 安全 | Security | `127.0.0.1` + Docker `expose` 非 `ports` + SSH tunnel 遠端 + kill-switch secret header |
| P0-10 | Docker 生命週期 | Deployment | Tick-abort **必須**（非可選）；`stop_grace_period=120s`；TA stage 收到 SIGTERM → 發 SIGTERM 給子進程 |
| P0-11 | Parser Cross-Check | Safety invariant | 3 × DeepSeek V4 Flash 並行；2/3 多數決；0/3 → Telegram operator；`parser_votes.jsonl` audit |
| TA 並行 | （既有缺陷） | Performance | `process_parse_result()` 拆 Phase 1 並行 TA + Phase 2 串行 sizing/order |

### Phase 0 完成標準

所有 P0-1 ~ P0-11 的 checkbox 勾選 → 更新本節狀態為 `completed` → 進入 M1 實作。

**狀態：`completed`**（2026-06-30 — M1–M6 全部實作完成，三個 rollback drill 場景 + P0-1 kill switch drill 全 PASS，P0-1 ~ P0-11 全數勾選）。

---

## 更新後的 M1–M6 Milestone

| Milestone | 內容 | 相依 |
|---|---|---|
| **M1** | 結構化 run record + run_id（`src/ops/run_record.py`）+ Parser Cross-Check（P0-11） | — |
| **M2** | 常駐 poll daemon（`src/ops/daemon.py`）+ 熔斷器（P0-5）+ TA 並行化 | M1 |
| **M3** | Telegram 告警 + kill switch `/stop` + drill `confirm_callback`（`src/notify/`） | M2 |
| **M4** | FastAPI 觀測 dashboard（`src/dashboard/`）+ P0-7 擴充路由 + P0-9 安全綁定 | M1 |
| **M5** | Docker 部署（`Dockerfile` + `docker-compose.yml`）+ P0-6 依賴聲明 + P0-4 健康檢查 + P0-8 輪替/備份 + P0-10 信號/測試 | M2, M3, M4 |
| **M6** | Rollback drill（P0-2）— 回滾訂單、回滾 config、Docker 回滾 | M5 |

### Stage A → Stage B 升級條件

| # | 條件 | 來源 |
|---|---|---|
| 1 | 至少 7 天連續運行，**零 daemon crash** | Phase 5 觀察期鏡像 |
| 2 | 至少 10 個信號成功處理（poll → parse → TA → size → order，paper） | Phase 5 信號門檻 |
| 3 | Kill switch drill 以真實 Telegram callback **端到端通過**（P0-1） | Phase 5 |
| 4 | Rollback drill 三個場景全部 **PASS**（P0-2 / M6） | Phase 5 |
| 5 | Alert channel 端到端測試通過（Telegram `/stop` → daemon stop） | Phase 5 |
| 6 | 無未解決 `ORDER_UNKNOWN`（M2 daemon tick 含定期掃描） | Phase 5 |
| 7 | 無 duplicate order incident | Phase 5 |
| 8 | Reconcile 狀態乾淨 | Phase 5 |
| 9 | Risk limits 已明確批准並記錄於 `wiki/decisions/` | Phase 5 |
| 10 | Operator（專案 owner）簽署 go/no-go → `wiki/decisions/` | Phase 5 |

## 驗收標準

1. 決策文檔存在於 `wiki/decisions/2026-06-29-production-deploy-scheduling-dashboard.md`，frontmatter 合法、語言繁體中文、格式與系列對齊。
2. `wiki/decisions/_index.md`「自動交易實作階段」小節已追加本決策索引條目，wikilink 可點跳轉。
3. 文檔涵蓋：核心安全原則（醒目位置）、M1–M5 milestone（各寫明新建文件與複用接口）、複用點表、關鍵決策表、拒絕方案表。
4. 所有 wikilink 目標文件存在且可跳轉。
5. **不包含**任何實作代碼、config 修改、`wiki/hot.md` 更新（待實作完成後另行走）。

## 倉位與 sizing 邊界決定（討論追加）

> 2026-06-29 討論生產化部署時，以「買 xxx 5%」「$10k 帳戶買 $1200 美光」等場景壓測，一併釐清 sizing / 倉位 / 範圍邊界。以下為結論，待另立 openspec change 實作，本檔僅記錄決定。

### 背景核實（已實作，非缺口）

- 倉位、總資金、1% 換算早在 Phase 3 設計並實作（[[wiki/decisions/2026-05-21-phase-3-portfolio-sizing-reconcile]]）：Webull 為 source of truth，`equity` 即時拉取，`1% = equity × 1%` 為買入 notional（**非**「每筆風險 1%」），無止損單。
- 「$10k 買 5%」→ `target_notional = $500`；sizing 內 8 個分支（正常 / 太貴 / 現金不足 / 集中度 / 掛單衝突 / 報價過期…）全部已實作於 `src/portfolio/sizing.py`。

### 決定

| # | 項 | 決定 | 前置 / 約束 |
|---|---|---|---|
| 1 | 移除 `symbol_whitelist` | 接受 | **前置**：TA fusion 須改 mandatory，不可 passthrough（`ta_gateway=None` 時會直接 APPROVE，見 `src/pipeline/orchestrator.py:384`；否則 parser 獨自決定買什麼） |
| 2 | sizing round-up tolerance | 接受 | budget 買不起 1 整股、但差額 ≤ `round_up_tolerance_usd=200`（**絕對值，不加比例 cap**）時進位買 1 股；仍受 buying_power / concentration 硬上限約束；新增 `ROUNDED_UP_TO_WHOLE_SHARE` reason code |
| 3 | 死配置清理 | 接受 | 刪除 `fractional_shares_enabled`、`min_residual_notional_usd`（config + settings + 設計文件偽代碼有，`sizing.py` 從未引用） |
| 4 | 碎股 fractional shares | 暫不考慮 | 維持整股 floor；買不起 1 股即 `SKIP_TOO_SMALL`（#2 round-up 為唯一例外） |

### round-up 邊界（$200 絕對值的實際影響）

| 指令 | 預算 | 最多花到 | 占 equity | 超支倍數 |
|---|---|---|---|---|
| 1% | $100 | ~$300 | 3% | 3× |
| 5% | $500 | ~$700 | 7% | 1.4× |
| 10% | $1000 | ~$1200 | 12% | 1.2× |

小預算指令被放大的比例較高；確認採絕對值、不加比例 cap。

### 拒絕方案

| 方案 | 拒絕理由 |
|---|---|
| 開啟碎股（`entrust_type=AMOUNT`） | 暫不考慮；維持整股 floor 語義 |
| round-up 加比例 cap（如 `min($200, 25%×budget)`） | 採純絕對值，避免雙參數 |
| 「$100 買 $1200」這類 8–12× 差距也進位 | 差額遠超 tolerance，仍 `SKIP_TOO_SMALL` |

### 後續

#1–#3 另立 openspec change 實作（同 Phase 1–5 流程），不在本部署決策內動代碼；索引見 [[wiki/product/auto-trading-prd-gap-list]] Later 段。

## 相關文件

- [[wiki/decisions/2026-05-21-phase-5-shadow-live-gates]] — Phase 5 shadow 觀察 gate，真錢前的 go/no-go 清單。
- [[wiki/decisions/2026-06-15-pipeline-orchestrator]] — Pipeline orchestrator 設計，daemon 複用的核心 `TradingPipeline` 與 `build_pipeline`。
- [[wiki/operations/auto-trading-runbook]] — 現有運維 runbook，pipeline CLI 操作手冊。
- [[wiki/architecture/auto-trading-risk-gates]] — 14 道 risk gate 定義，daemon 運行時全部保持不變。
- [[wiki/product/auto-trading-prd-gap-list]] — PRD 缺口清單，dashboard/metrics 需求來源。
