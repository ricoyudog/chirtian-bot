## 1. Run Record & Parser Cross-Check (M1)

- [x] 1.1 Create `src/ops/` package with `__init__.py`
- [x] 1.2 Create `src/ops/run_record.py` — `RunRecorder` class: generates `run_id` (`{date}-{seq}-{uuid[:8]}`), starts/ends runs, appends to `runtime/runs.jsonl`
- [x] 1.3 Implement `stage_timings` tracking: per-instruction per-stage `started_at` + `duration_ms` + `skipped` flag
- [x] 1.4 Implement run lifecycle: `start_run()`, `end_run(outcome)`, `record_instruction_outcome()`, `record_error(stage, message)`
- [x] 1.5 Write unit tests for `RunRecorder`: run_id uniqueness, stage_timings correctness, error recording, SIGTERM abort recording
- [x] 1.6 Create `src/analyzer/parser_crosscheck.py` — `CrossCheckParser` class: accepts DeepSeek API config, implements `parse(post_id, raw_text) → ParseResult`
- [x] 1.7 Implement 3 × parallel DeepSeek V4 Flash subprocess calls via `ThreadPoolExecutor`
- [x] 1.8 Implement 2/3 majority voting logic: compare symbol + action across 3 models; accept majority; 0/3 → `NEEDS_REVIEW`
- [x] 1.9 Implement voting trail: write `runtime/parser_votes.jsonl` with model_votes array, final_decision, strategy
- [x] 1.10 Ensure `CrossCheckParser` output (`ParseResult`) is structurally identical to `InstructionParser` output
- [x] 1.11 Write unit tests for `CrossCheckParser`: 3/3 agreement, 2/3 agreement, 0/3 disagreement, 2/3 disagreement-on-action, one-model-timeout, all-models-timeout

## 2. Poll Daemon (M2)

- [x] 2.1 Create `src/ops/daemon.py` — main tick loop: `while not stop_event: poll_once() → pipeline → RunRecorder → heartbeat`
- [x] 2.2 Create `src/ops/__main__.py` — CLI entry: `python -m src.ops`
- [x] 2.3 Implement reentrancy lock via `fcntl.flock` / `msvcrt.locking` on `runtime/daemon.lock`, prevent dual-start
- [x] 2.4 Implement heartbeat: write `runtime/daemon_heartbeat.json` on every tick (`last_tick`, `pid`, `status`)
- [x] 2.5 Implement circuit breaker: `consecutive_failures` counter; N=5 → write `kill_switch.flag` + Telegram alert + exit; reset on success
- [x] 2.6 Implement dead-man switch readiness: heartbeat file age checkable by Docker healthcheck (≤ 120s)
- [x] 2.7 Implement tick-abort: register SIGTERM handler → `threading.Event.set()`; TA stage checks event → SIGTERM subprocess
- [x] 2.8 Implement kill_switch.flag check at startup: exists → invoke `RuntimeGuard.activate_stop()` → refuse to start
- [x] 2.9 Implement startup SQLite integrity check: `PRAGMA integrity_check` on `shadow_state.db` + `positions.db`; fail → refuse to start
- [x] 2.10 Implement startup JSONL purge: delete `runs-*.jsonl` older than 13 months
- [x] 2.11 Modify `src/pipeline/orchestrator.py` `process_parse_result()`: split into Phase 1 (parallel TA via `ThreadPoolExecutor`) + Phase 2 (serial sizing/order)
- [x] 2.12 Modify `src/pipeline/wiring.py` `build_pipeline()`: add P0-3 assertion — `ta_gateway is None AND len(symbol_whitelist) == 0 → RuntimeError`
- [x] 2.13 Wire daemon to use `CrossCheckParser` (not `InstructionParser`) for automatic poll path
- [x] 2.14 Implement daemon positions snapshot: each tick → pull broker API positions → write `runtime/positions.db` (table `position_snapshots`)
- [x] 2.15 Implement JSONL monthly rotation: detect month boundary → start new `runs-YYYY-MM.jsonl`
- [x] 2.16 Write integration tests: daemon startup/shutdown, lock contention, circuit breaker trigger+reset, tick-abort with mock TA subprocess

## 3. Telegram Alert Bot (M3)

- [x] 3.1 Create `src/notify/` package with `__init__.py`
- [x] 3.2 Create `src/notify/telegram.py` — `TelegramNotifier` class: sends formatted alert messages with run_id, error summary, stage
- [x] 3.3 Create `src/notify/bot.py` — Telegram bot (`python-telegram-bot`): registers `/stop` handler, push alert functions
- [x] 3.4 Implement `/stop` command: write `runtime/kill_switch.flag`, reply confirmation message
- [x] 3.5 Implement pipeline error push: on any stage exception → push message (run_id + error summary + affected stage)
- [x] 3.6 Implement circuit breaker alert push: on consecutive_failures=5 → push message (breaker activated + kill switch engaged)
- [x] 3.7 Implement parser cross-check 0/3 alert push: on no_consensus → push message (post excerpt + 3 model outputs)
- [x] 3.8 Implement drill `confirm_callback`: send "drill confirmation request" message → wait for operator reply → return timestamp or None on timeout
- [x] 3.9 Modify `src/shadow/drill.py` `run_drill()`: make `confirm_callback` required parameter; `None` → `DrillResult(result="FAILED", failure_reason="NO_CONFIRM_CALLBACK")`
- [x] 3.10 Implement bot heartbeat: periodically write `runtime/bot_heartbeat.json`
- [x] 3.11 Write integration tests: `/stop` → kill_switch.flag written, drill confirm_callback with mock Telegram API, error push formatting

## 4. FastAPI Dashboard (M4)

- [x] 4.1 Create `src/dashboard/` package with `__init__.py`
- [x] 4.2 Create `src/dashboard/app.py` — FastAPI app with CORS, static file serving, route registration
- [x] 4.3 Implement `GET /api/runs` — paginated list from `runs.jsonl`
- [x] 4.4 Implement `GET /api/runs/{run_id}` — single run detail cross-ref `audit_ledger.jsonl`
- [x] 4.5 Implement `GET /api/metrics` — per-stage p50/p95/max from `runs.jsonl` stage_timings; reuse `MetricsCollector.generate_report()`
- [x] 4.6 Implement `GET /api/safety` — RuntimeGuard.is_stopped + kill_switch.flag existence
- [x] 4.7 Implement `GET /api/events/tail` — SSE stream tailing `audit_ledger.jsonl`
- [x] 4.8 Implement `GET /api/health` — combined: daemon (heartbeat age ≤ 120s → ok/stale), dashboard (uptime), bot (bot_heartbeat.json age), safety (guard status)
- [x] 4.9 Implement `GET /api/posts` — from `processed_posts.json` cross-ref `runs.jsonl`
- [x] 4.10 Implement `GET /api/positions` — from `positions.db` (latest tick); return symbol, position_qty, market_value, unrealized_pnl, pnl_pct
- [x] 4.11 Implement `POST /api/kill-switch` — validate `X-Kill-Switch-Secret` header → write `kill_switch.flag`; 403 on invalid/missing
- [x] 4.12 Implement `GET /` — serve `static/index.html` (dashboard SPA)
- [x] 4.13 Bind dashboard to `127.0.0.1` (not `0.0.0.0`), configure CORS for localhost only
- [x] 4.14 Write integration tests: all routes return expected shape, kill-switch auth, SSE stream, health stale detection

## 5. Docker Deployment (M5)

- [x] 5.1 Create `Dockerfile` — multi-stage or single-stage with: Python venv, Node.js, Claude CLI, DeepSeek SDK, Webull SDK, mcp-substack
- [x] 5.2 Create `docker-compose.yml` — three services: daemon, dashboard, bot; shared `runtime/` named volume
- [x] 5.3 Configure daemon service: `restart: unless-stopped`, `stop_grace_period: 120s`, `mem_limit: 1GB`, healthcheck (heartbeat ≤ 120s)
- [x] 5.4 Configure dashboard service: `restart: unless-stopped`, `mem_limit: 256MB`, healthcheck (curl /api/health → 200), `expose` not `ports`
- [x] 5.5 Configure bot service: `restart: unless-stopped`, healthcheck (process alive + API reachable)
- [x] 5.6 Create `.env.example` — all required env vars with placeholder values, annotated required vs optional
- [x] 5.7 Configure Substack `storage-state.json` as host bind-mount `:ro` in daemon service
- [x] 5.8 Create `SETUP.md` — manual setup steps: Substack session export, Webull auth, Claude auth, DeepSeek API key, Telegram bot token
- [x] 5.9 Implement Substack session expiry detection: N=6 consecutive zero-post polls + deviates from Christian posting pattern → Telegram alert
- [x] 5.10 Create `docker-compose.test.yml` — `mode: offline_replay` + stubbed deps, verify all healthchecks pass
- [x] 5.11 Verify acceptance criteria: 3 services healthy ≤ 30s, kill switch ≤ 2 ticks, daemon crash auto-restart ≤ 10s, volume persistence across down+up

## 6. Rollback Drill (M6)

- [x] 6.1 Implement rollback scenario 1: place paper order → cancel_order() → verify cancellation → audit event → confirm portfolio ledger consistency → write `runtime/incidents/<date>-rollback-order-cancel.md`
- [x] 6.2 Implement rollback scenario 2: backup config.yaml → replace with known-good → restart daemon → verify healthcheck → write `runtime/incidents/<date>-rollback-config.md`
- [x] 6.3 Implement rollback scenario 3: docker compose down → verify runtime/ volume retained → docker compose up → verify 3 services healthy + run history preserved → write `runtime/incidents/<date>-rollback-docker.md`
- [x] 6.4 Run end-to-end kill switch drill with real Telegram callback (P0-1 verification) → verify PASS → write incident note
- [x] 6.5 Verify all P0-1 ~ P0-11 checkboxes in wiki/decisions/2026-06-29-production-deploy-scheduling-dashboard.md are complete
