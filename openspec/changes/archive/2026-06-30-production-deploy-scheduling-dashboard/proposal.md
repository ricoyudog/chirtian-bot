## Why

Christian Bot 已端到端跑通（Phase 1–5 全棧：parser → TA fusion → sizing → execution gate → broker），但運行形態完全是 operator 手動 `python -m src.pipeline poll`。沒有任何代碼讓它在背景持續運行——無常駐進程、無定時調度、無結構化 run record、無 dashboard、無告警 channel、無部署腳本。核心問題：**所有零件都做完且測過，但沒有生產化運行層**。

## What Changes

新增「調度層」與「觀測層」兩個零侵入外掛層，讓 Christian Bot 從手動 CLI 升級為常駐、定時、可觀測、可告警的生產化運行形態。全程保持 `uat_confirm + paper`，不碰真錢。

- 新增結構化 run record（`run_id` + `runs.jsonl`），提供可回溯的執行歷史
- 新增常駐 poll daemon（60s tick、重入鎖、熔斷器、dead-man switch、tick-abort）
- 新增 Telegram 告警 bot（失敗告警、kill switch `/stop`、drill `confirm_callback`）
- 新增 FastAPI 觀測 dashboard（run 歷史、即時持倉、per-stage 延遲、SSE 事件推送、四心跳）
- 新增 Docker 三 service 部署（daemon + dashboard + bot，共享 `runtime/` volume）
- 新增 Parser Cross-Check：3 × DeepSeek V4 Flash 並行抽取 + 2/3 多數決
- **BREAKING**: `AlertDrillRunner.run_drill()` 的 `confirm_callback` 從可選改為強制
- TA fusion 階段從串行改為並行（多 symbol 場景）
- 新增 Rollback Drill（回滾訂單、回滾 config、Docker 回滾三場景）

## Capabilities

### New Capabilities
- `run-record`: 結構化 run_id（`{date}-{seq}-{uuid[:8]}`）+ append-only JSONL 記錄（`runtime/runs.jsonl`），含 `stage_timings`、signals_processed、orders_placed、errors、outcome
- `poll-daemon`: 常駐 daemon（`python -m src.ops`），60s tick 調用現有 `poll_once()`，重入鎖（`fcntl.flock`）、心跳（`daemon_heartbeat.json`）、熔斷器（連續 5 次失敗 → kill_switch.flag + Telegram 告警）、dead-man switch（三層健康檢查）、tick-abort（SIGTERM 時優雅中斷 TA subprocess）
- `telegram-alert`: Telegram bot（`python-telegram-bot`）提供三項服務：失敗告警（含 run_id、錯誤摘要）、kill switch `/stop`（寫 `kill_switch.flag`）、drill `confirm_callback`（operator-in-the-loop）
- `deploy-dashboard`: FastAPI 觀測 dashboard，路由含 `/api/runs`、`/api/runs/{id}`、`/api/metrics`（per-stage p50/p95）、`/api/safety`、`/api/events/tail`（SSE）、`/api/health`（四心跳合併）、`/api/posts`、`/api/positions`（daemon 調 broker API → 寫 `positions.db` → dashboard 只讀 SQLite）
- `docker-deploy`: Docker Compose 三 service（daemon + dashboard + bot），共享 `runtime/` named volume，healthcheck + `restart: unless-stopped`，`stop_grace_period=120s`，完整 `.env.example` + `SETUP.md`
- `parser-crosscheck`: `CrossCheckParser`，3 × DeepSeek V4 Flash 並行 subprocess（`ThreadPoolExecutor`），2/3 多數決（symbol + action），0/3 一致時 `NEEDS_REVIEW` + Telegram 通知，投票記錄寫入 `runtime/parser_votes.jsonl`
- `rollback-drill`: 三個回滾場景——回滾 paper 訂單（`cancel_order` + audit）、回滾 config（`config.yaml` rollback + daemon 重啟）、Docker 回滾（`docker compose down && up` 保留 volume）

### Modified Capabilities
- `alert-drill`: `run_drill()` 的 `confirm_callback` 從 `Optional[Callable]` 改為強制參數，`None` 時 return `DrillResult(result="FAILED", failure_reason="NO_CONFIRM_CALLBACK")`（P0-1）

## Impact

- `src/` 新增模組：`src/ops/`（daemon + run_record）、`src/notify/`（Telegram bot）、`src/dashboard/`（FastAPI）、`src/analyzer/parser_crosscheck.py`
- 修改現有模組：`src/shadow/drill.py`（confirm_callback 強制）、`src/pipeline/orchestrator.py`（TA 並行化）、`src/pipeline/wiring.py`（TA 強制性檢查）
- `runtime/` 新增檔案：`runs.jsonl`、`daemon_heartbeat.json`、`daemon.lock`、`kill_switch.flag`、`positions.db`、`parser_votes.jsonl`、`bot_heartbeat.json`
- 新增根目錄檔案：`Dockerfile`、`docker-compose.yml`、`docker-compose.test.yml`、`.env.example`、`SETUP.md`
- 依賴現有模組：`src/ingestion/poll.py`、`src/pipeline/orchestrator.py`、`src/safety/runtime_guard.py`、`src/state/ledger.py`、`src/shadow/drill.py`、`src/shadow/metrics.py`
- 不修改任何現有安全代碼（`RuntimeGuard`、`ExecutionGate`、`ReconcileGate`）

## GitHub Issue

- Parent: https://github.com/ricoyudog/chirtian-bot/issues/34
- 6 Task Groups: #35 #36 #37 #38 #39 #40
