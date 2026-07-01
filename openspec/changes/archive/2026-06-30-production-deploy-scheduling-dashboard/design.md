## Context

Christian Bot Phase 1–5 完成全棧：parser (GLM-5.2) → TA fusion (DeepSeek V4 Pro) → sizing → execution gate → broker (Webull paper)。但運行形態完全是 operator 手動 CLI。缺失：常駐進程、定時調度、結構化 run record、dashboard、告警、部署腳本。

調度層與觀測層的核心安全原則：**調度層 = 自動按按鈕的人；觀測層 = 純只讀**。兩者都不修改任何一行安全代碼（`RuntimeGuard`、`ExecutionGate`、`ReconcileGate` 全部不變）。Daemon 自動觸發 poll → pipeline 會撞上與手動執行完全同一套 guard。

建構順序：Phase 0（本文件覆蓋的缺口修補）→ M1 run-record + parser-crosscheck → M2 daemon + 熔斷器 + TA 並行 → M3 Telegram alert → M4 dashboard → M5 Docker → M6 rollback drill。

參考決策：[[wiki/decisions/2026-06-29-production-deploy-scheduling-dashboard.md]]（完整 Phase 0 缺口分析與決定）。

## Goals / Non-Goals

**Goals:**
- 結構化 run_id 和執行歷史（`runs.jsonl`），支援按 run 查詢、per-stage latency 聚合
- 常駐 daemon，60s tick 自動 poll + pipeline，含重入鎖、熔斷器、dead-man switch、tick-abort
- Telegram 告警 bot：失敗告警、kill switch `/stop`、drill confirm_callback
- FastAPI 觀測 dashboard：run 歷史、即時持倉（broker→SQLite）、per-stage 延遲、SSE 事件、四心跳
- Docker 三 service 部署：daemon + dashboard + bot，共享 `runtime/` volume
- Parser cross-check：3 × DeepSeek V4 Flash 並行 + 2/3 多數決
- Rollback drill：回滾訂單、回滾 config、Docker 回滾三場景
- 所有修補不修改現有安全代碼

**Non-Goals:**
- 不碰真錢（Stage B，需單獨 Phase 5 go/no-go 後才進行）
- 不改動 `RuntimeGuard`、`ExecutionGate`、`ReconcileGate`
- 不接 ConfirmationManager 到 Telegram（`confirmation_mode=auto` 不調它）
- 不建 Grafana/Prometheus（遠超 MVP；數據已 JSONL + SQLite 落盤）
- 不開碎股（fractional shares）

## Unknowns & Investigation

- **TA 單次實際耗時？** — 目前 timeout 設 1800s（30min），但實際 DeepSeek V4 Pro + TradingAgents deep mode 的典型運行時間未知。需要第一次端到端測試後實測數據來校準並行化的實際收益和 `stop_grace_period` buffer。若實際 ~5min，串行化風險低；若 ~25min，並行化是硬需求。
- **DeepSeek V4 Flash 對 Christian 語言的抽取品質？** — 用戶確認「已經夠聰明」，但沒有定量 backtest 數據。建議 M1 實作 `CrossCheckParser` 後，用既有 gold set（Phase 2）跑一次對比測試，確認 Flash 的 precision/recall 與 GLM-5.2 可比。
- **Substack session 過期頻率？** — Substack cookies 的有效期未知（取決於 Substack 的 session policy）。需要在 24/7 運行後觀察實際過期週期，再調校語義層檢測的 N 值（暫定連續 6 次零帖 → 告警）。
- **`RuntimeGuard.assert_mutation_allowed()` 是否覆蓋盤後下單？** — `check_environment()` 只檢查 `environment=="uat"` 不含 market hours。防護來自 sizing 的 `SKIP_STALE_QUOTE`。若實際運營中發現盤後仍能成交 paper 訂單，需額外增加 `trading_session_filter`。

## Decisions

### 1. Run ID Scheme: `{date}-{seq}-{uuid[:8]}` append JSONL

**Decision:** 每次 pipeline 執行產生唯一 `run_id`，格式 `2026-07-05-001-a1b2c3d4`。寫入 `runtime/runs.jsonl`（append-only JSONL，與 `AuditLedger` 同模式）。

**Why:** 人類可讀（一眼看出日期和序號）+ 唯一性（uuid[:8] 保證）。Append JSONL 是既有模式（`AuditLedger`），效能無虞，無鎖競爭。

**Alternatives:** UUID-only（不可讀）、自增整數（重啟後需恢復計數器）。

### 2. Daemon Architecture: Single-Process Python with Tick Loop

**Decision:** 單一 Python 進程，while loop 內每 60s 調用 `poll_once()`。不使用 crontab 或多進程架構。

**Why:** Crontab 無重入鎖、無心跳、無優雅停機、無共享狀態。Python daemon 可與 pipeline 共享進程內狀態，統一 SIGTERM 處理。

### 3. Circuit Breaker: N=5 → Kill Switch + Telegram

**Decision:** 連續 5 次 tick 失敗 → 寫 `kill_switch.flag` + 發 Telegram 告警 + daemon 退出。任何一次成功 tick 歸零計數器。

**Why:** 5 × 60s = 5 分鐘連續失敗指向系統性故障（非 transient）。Stop-the-world 符合 fail-closed 原則。Operator 診斷後手動刪除 flag 恢復。

**Alternatives:** 只發告警繼續重試（可能永久靜默失敗）、backoff 暫停（Substack 長時間故障時反覆抖動）。

### 4. Tick-Abort: threading.Event + SIGTERM to TA Subprocess

**Decision:** SIGTERM → `threading.Event.set()` → pipeline 各 stage 檢查。TA stage 收到 abort 時發 SIGTERM 給子進程，回傳 `available=False`（fail-closed），標記 `TA_UNAVAILABLE`。總清理時間 ≤15s。`stop_grace_period=120s`。

**Why:** Docker 預設 `stop_grace_period=10s`，TA 可達 30min。不 abort 則 SIGKILL 硬殺 → TA subprocess 變孤兒、run record 半條、lock 未釋放。

**Alternatives:** 設 `stop_grace_period=1800s`（不現實——Docker 操作體驗極差）、不處理（SIGKILL 後果不可接受）。

### 5. Dead-Man Switch: Three Independent Layers

**Decision:** (1) Docker healthcheck 檢查 `daemon_heartbeat.json` mtime ≤ 120s；(2) Dashboard `/api/health` 回傳 `stale: true` 而非 500；(3) 外部 health check（Stage B 必須，Stage A 可選）。

**Why:** 心跳檔永遠存在（daemon 崩潰不刪除），只靠存在性判斷會誤報 alive。三層獨立因為任何一層都可能跟 daemon 一起掛。

### 6. Telegram Bot Scope: Alert + Kill Switch + Drill Callback

**Decision:** Bot 只做三件事：(1) pipeline 失敗告警、(2) `/stop` 寫 kill_switch.flag、(3) drill `confirm_callback`。不接 `ConfirmationManager`。

**Why:** `confirmation_mode=auto` 時 orchestrator 不調 `ConfirmationManager`。避免 in-memory 狀態機複雜化。留 Stage B 真錢 `prod_confirm` 時再評估。

### 7. Dashboard Positions: Daemon → Broker API → Local SQLite → Dashboard Read-Only

**Decision:** Daemon 每 tick 調 broker API 拉即時持倉，寫 `runtime/positions.db`。Dashboard `/api/positions` 只讀 SQLite（`SELECT ... WHERE tick_at = MAX(tick_at)`）。

**Why:** Broker 為 ground truth（reconcile 可能有 bug）。Daemon 每 60s 一次調用在 rate limit（10 req/30s）內。Dashboard 不觸 broker API，保持純只讀原則。

**Alternatives:** Ledger 回放計算持倉（依賴 reconcile bug-free）、dashboard 直接調 broker API（違反觀測層原則 + rate limit 風險）。

### 8. Parser Cross-Check: 3 × DeepSeek V4 Flash Parallel + 2/3 Majority

**Decision:** `CrossCheckParser` 用 `ThreadPoolExecutor` 並行調用 3 個 DeepSeek V4 Flash。Symbol + action 2/3 一致即採納，qty 取中位數。0/3 一致 → `NEEDS_REVIEW` + Telegram operator。投票記錄寫入 `parser_votes.jsonl`。

**Why:** Parser 層缺乏獨立驗證——TA fusion 驗證技術面，不驗證「帖文是否被正確理解」。並行確保不增加延遲。2/3 多數決避免一致決過緊（每帖人審）。

**Alternatives:** 一致決 3/3（自動化失效——幾乎每帖都要人審）、單一模型（現狀——無驗證）。

### 9. TA Parallelization: Phase 1 (Parallel TA) + Phase 2 (Serial Sizing/Order)

**Decision:** `process_parse_result()` 拆為兩階段：Phase 1 用 `ThreadPoolExecutor` 並行所有 symbol 的 TA 分析；Phase 2 串行 sizing + order。

**Why:** TA 各 symbol 完全獨立（無共享狀態），可安全並行。Sizing 依賴 portfolio snapshot（buying power）、order 寫入 portfolio ledger——並行會導致重複扣減 buying power、超買。

### 10. JSONL Rotation & Housekeeping: SQL-Based, Not Cron

**Decision:** JSONL 按月輪替（`runs-2026-07.jsonl`），保留 13 個月。`positions.db` 每天 SQL housekeeping（`DELETE ... WHERE tick_at < date('now', '-30 days')`）。Daemon 啟動時 purge 過期 JSONL（`find ... -mtime +395 -delete`）。

**Why:** 用戶決定不用 cronjob——SQL housekeeping 內建於 daemon 生命週期，減少外部依賴。13 個月支援跨年度對比（今年 7 月 vs 去年 7 月）。

### 11. Dashboard Security: Bind 127.0.0.1 + Docker expose + SSH Tunnel + Kill-Switch Secret

**Decision:** 四層防護：(1) bind `127.0.0.1`、(2) Docker `expose` 非 `ports`、(3) 遠端用 SSH tunnel、(4) `POST /api/kill-switch` 驗證 `X-Kill-Switch-Secret` header。

**Why:** 無認證的 kill switch 是攻擊面。SSH tunnel 是最簡遠端方案（零額外依賴）。

### 12. Confirm Callback Required (P0-1): Breaking Change to alert-drill

**Decision:** `run_drill()` 的 `confirm_callback` 從 `Optional[Callable]` 改為強制參數。`None` 時 return `DrillResult(result="FAILED", failure_reason="NO_CONFIRM_CALLBACK")`。

**Why:** `datetime.now()` 偽造 operator 確認 → auto-pass 不滿足 Phase 5「端到端演練」標準。Fail-fast at code level。

### 13. Claude CLI Retained in Docker

**Decision:** Docker image 同時包含 Claude CLI + DeepSeek SDK。Daemon 走 DeepSeek cross-check；operator 手動 `cmd_parse`/`cmd_run` 仍走 Claude。

**Why:** Claude 是整個專案的默認 LLM 介面，砍掉會廢掉現有 CLI 命令。DeepSeek 全掛時 Claude 為 parser fallback。

### 14. TA Must Be Mandatory When Whitelist Is Empty (P0-3)

**Decision:** `build_pipeline()` 中斷言：`ta_gateway is None AND len(symbol_whitelist) == 0 → RuntimeError`。Daemon 啟動時 fail-fast。

**Why:** 空白名單的設計前提是 TA 在線。代碼層不強制則 `--ta skip` + 空白名單 = 零閘門。與 Parser Cross-Check (P0-11) 互補。

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| TA 串行改並行引入 race condition | Sizing/order 保持串行；TA 階段各 symbol 無共享狀態，`ThreadPoolExecutor` 安全 |
| DeepSeek V4 Flash 抽取品質低於 GLM-5.2 | M1 後用 gold set backtest；保留 Claude/GLM-5.2 為 fallback |
| Substack session 過期 → 長期無訊號 | 語義層檢測（連續 N=6 次零帖 + 偏離 Christian 發帖模式 → Telegram 告警） |
| `positions.db` 與 broker 不同步 | Daemon 每 tick 拉 broker API 覆蓋寫入；broker 為 ground truth |
| Tick-abort 時 TA subprocess 不響應 SIGTERM | Python subprocess 有 `timeout` 參數；SIGKILL 在 stop_grace_period 耗盡時由 Docker 兜底 |
| Docker volume 損毀 | M6 rollback drill 驗證 `docker compose down && up` 後 volume 持久化 |
| 三 service 同時掛（host 斷網） | Stage B 加入外部 health check（healthchecks.io）作為獨立告警 channel |

## Data Model

### RunRecord (JSONL: `runtime/runs.jsonl`)

```
{
  run_id: "2026-07-05-001-a1b2c3d4",
  started_at: "2026-07-05T14:30:00Z",
  ended_at: "2026-07-05T14:30:45Z",
  mode: "uat_confirm",
  environment: "uat",
  signals_processed: 1,
  instructions: [
    {
      instruction_id: "...",
      symbol: "NVDA",
      action: "BUY",
      outcome: "PLACED",
      stage_timings: {
        detect:    {started_at: "...", duration_ms: 500},
        parse:     {started_at: "...", duration_ms: 2100},
        llm:       {skipped: true},
        ta:        {started_at: "...", duration_ms: 1080000},
        sizing:    {started_at: "...", duration_ms: 300},
        exec:      {started_at: "...", duration_ms: 800},
        broker:    {started_at: "...", duration_ms: 1200}
      }
    }
  ],
  errors: [],
  outcome: "success"
}
```

### Parser Votes (JSONL: `runtime/parser_votes.jsonl`)

```
{
  run_id: "2026-07-05-001-a1b2c3d4",
  post_id: "...",
  model_votes: [
    {model_id: "deepseek-flash-1", symbol: "NVDA", action: "BUY", quantity_pct: 5.0, confidence: 0.92},
    {model_id: "deepseek-flash-2", symbol: "NVDA", action: "BUY", quantity_pct: 5.0, confidence: 0.88},
    {model_id: "deepseek-flash-3", symbol: "AMD",  action: "BUY", quantity_pct: 5.0, confidence: 0.45}
  ],
  final_decision: {symbol: "NVDA", action: "BUY", quantity_pct: 5.0},
  strategy: "majority_2of3"
}
```

### Position Snapshots (SQLite: `runtime/positions.db`)

```sql
CREATE TABLE position_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    tick_at TEXT NOT NULL,
    symbol TEXT NOT NULL,
    position_qty REAL NOT NULL,
    market_value REAL NOT NULL,
    unrealized_pnl REAL NOT NULL,
    pnl_pct REAL NOT NULL
);
CREATE INDEX idx_snapshots_tick ON position_snapshots(tick_at);
```

### Heartbeat Files

```
runtime/daemon_heartbeat.json:  {"last_tick": "ISO8601", "pid": int, "status": "ok"}
runtime/bot_heartbeat.json:     {"last_heartbeat": "ISO8601", "pid": int, "status": "ok"}
runtime/kill_switch.flag:       (empty file — existence is the signal)
runtime/daemon.lock:            (fcntl.flock — OS-level file lock)
```

## API Contracts

### Dashboard Routes

| Method | Path | Description |
|---|---|---|
| GET | `/` | Dashboard HTML (`static/index.html`) |
| GET | `/api/runs` | Run list with summaries (paginated) |
| GET | `/api/runs/{run_id}` | Single run detail (cross-ref audit_ledger) |
| GET | `/api/metrics` | Per-stage p50/p95/max latencies |
| GET | `/api/safety` | RuntimeGuard status + kill switch state |
| GET | `/api/events/tail` | SSE stream tailing audit_ledger.jsonl |
| GET | `/api/health` | Combined daemon+dashboard+bot+safety health |
| GET | `/api/posts` | Substack posts feed (from processed_posts.json + cross-ref runs) |
| GET | `/api/positions` | Current holdings (from positions.db) |
| POST | `/api/kill-switch` | Write kill_switch.flag (requires X-Kill-Switch-Secret) |

All data sources are local files (JSONL + SQLite). Dashboard never calls broker API directly.

### Telegram Bot Commands

| Command | Description |
|---|---|
| `/stop` | Write `runtime/kill_switch.flag`, reply confirmation |
| (push) | Pipeline error alert: run_id + error summary + affected stage |
| (push) | Circuit breaker activation: 5 consecutive failures + kill switch engaged |
| (push) | Parser cross-check 0/3 disagreement: post excerpt + all three model outputs |

## Migration Plan

1. **Phase 0**: 完成本文件所有 P0-1 ~ P0-11 checkbox
2. **M1**: 新建 `src/ops/run_record.py` + `src/analyzer/parser_crosscheck.py`，不修改既有模組
3. **M2**: 新建 `src/ops/daemon.py` + `src/ops/__main__.py`，修改 `orchestrator.py`（TA 並行化）+ `wiring.py`（TA 強制性檢查）
4. **M3**: 新建 `src/notify/telegram.py` + `src/notify/bot.py`，修改 `drill.py`（confirm_callback 強制）
5. **M4**: 新建 `src/dashboard/app.py` + `static/`
6. **M5**: 新建 `Dockerfile` + `docker-compose.yml` + `.env.example` + `SETUP.md`
7. **M6**: Rollback drill 演練，記錄到 `runtime/incidents/`

Rollback: `docker compose down` → 保留 `runtime/` volume → `docker compose up`（使用上一版 image tag）。

## Open Questions

- TA 實際單次耗時需第一次端到端測試後實測
- DeepSeek V4 Flash 抽取品質需 gold set backtest 後確認
- Substack session 實際過期週期需 24/7 運行後觀察
