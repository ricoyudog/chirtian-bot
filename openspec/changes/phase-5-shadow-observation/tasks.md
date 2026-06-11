## 1. Metrics Collector

- [x] 1.1 Create `src/shadow/metrics.py` with `MetricsCollector` class — accepts `AuditLedger` dependency, provides `record_stage(signal_id, stage, latency_ms, outcome, error_type?)` method
- [x] 1.2 Implement `shadow_metric.*` event_type prefix convention — each metric recorded as `AuditLedger.append()` with event_type `shadow_metric.{stage}`
- [x] 1.3 Implement `MetricsReport.generate()` — queries AuditLedger for all `shadow_metric.*` events in observation period, computes p50/p95/max latencies per stage, counts outcomes, calculates stale signal rate
- [x] 1.4 Add stale signal classification logic — signal is stale when total pipeline latency exceeds configurable window (default 15 min) AND not caused by market closure
- [x] 1.5 Write unit tests for MetricsCollector — verify event recording, report generation, stale rate calculation, 5% threshold warning

## 2. Observation Runner

- [x] 2.1 Create `src/shadow/runner.py` with `ShadowObservationRunner` class — orchestrates detection → parse → sizing → execution gate → broker pipeline in shadow mode
- [x] 2.2 Create `src/shadow/state.py` with `ObservationStateStore` — SQLite-backed (WAL mode) at `runtime/shadow_state.db`, persists observation_id, started_at, signals_processed, status
- [x] 2.3 Implement observation period tracking — auto-extend if 1 week passed but < 10 signals, stop at 4 weeks if still insufficient
- [x] 2.4 Implement weekend signal deferral — classify weekend/holiday signals as DEFERRED, store for next trading day execution
- [x] 2.5 Implement shadow run summary generation — write `runtime/shadow_summaries/YYYY-MM-DD-shadow-run-summary.md` with metrics report and go/no-go readiness checklist
- [x] 2.6 Implement CLI entry point `python -m shadow observe start|stop|status` with `src/shadow/__main__.py`
- [x] 2.7 Write integration tests for observation runner — test period tracking, auto-extend, max duration, summary generation

## 3. Alert Drill

- [x] 3.1 Create `src/shadow/drill.py` with `AlertDrillRunner` class — simulates kill switch scenario end-to-end
- [x] 3.2 Implement drill execution flow — simulate anomaly → trigger kill switch → send alert to console + audit ledger → wait for operator confirmation
- [x] 3.3 Implement drill result persistence — write `runtime/incidents/YYYY-MM-DD-drill-kill-switch.md` with type, timing, result, failure details
- [x] 3.4 Implement go/no-go alert channel gate — check `runtime/incidents/` for successful drill result; return NO_GO if none found
- [x] 3.5 Write unit tests for AlertDrillRunner — test success path, timeout path, operator no-response path

## 4. Integration & Documentation

- [x] 4.1 Wire `ShadowObservationRunner` with existing pipeline modules (parser, sizing, executor, safety) using dependency injection
- [x] 4.2 Add `runtime/` directory structure to `.gitignore` (shadow_state.db, shadow_summaries/, incidents/)
- [x] 4.3 Update `wiki/decisions/2026-05-21-phase-5-shadow-live-gates.md` status from `proposed` to `accepted`
- [x] 4.4 Write end-to-end smoke test — manual trigger of observation runner with a test signal, verify metrics recorded and state persisted
