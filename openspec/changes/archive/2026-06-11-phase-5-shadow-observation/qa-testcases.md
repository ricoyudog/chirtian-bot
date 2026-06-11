# QA Test Cases — phase-5-shadow-observation

| # | Scenario | Input / Action | Expected Output | Assigned Atom | Priority |
|---|----------|----------------|-----------------|---------------|----------|
| 1 | Module imports successfully | `from src.shadow.metrics import MetricsCollector` | No import error | qa-smoke | P1 |
| 2 | All tests pass | `pytest tests/ --ignore=tests/gold_set` | 407/407 passed | qa-smoke | P1 |
| 3 | CLI entry point loads | `python -m shadow observe --help` | Shows help text | qa-smoke | P1 |
| 4 | MetricsCollector records to ledger | `record_stage("sig-1", "detection", 120.5, "success")` | Event in ledger with event_type `shadow_metric.detection` | qa-backend | P1 |
| 5 | MetricsCollector rejects invalid stage | `record_stage("sig-1", "bad_stage", 100, "success")` | ValueError | qa-backend | P1 |
| 6 | MetricsCollector rejects invalid outcome | `record_stage("sig-1", "detection", 100, "bad_outcome")` | ValueError | qa-backend | P1 |
| 7 | Stale signal classified on weekday above threshold | `classify_stale(20min latency, weekday timestamp, 15min window)` | Returns True | qa-backend | P1 |
| 8 | Stale signal NOT classified on weekend | `classify_stale(20min latency, Saturday timestamp, 15min window)` | Returns False | qa-backend | P1 |
| 9 | Stale rate exceeds 5% threshold | 10 signals, 1 stale → generate_report | stale_rate_exceeded = True | qa-backend | P1 |
| 10 | Stale rate within 5% threshold | 20 signals, 1 stale → generate_report | stale_rate_exceeded = False | qa-backend | P1 |
| 11 | MetricsReport has p50/p95/max per stage | Record multiple stages, generate_report | Each stage has count, p50_ms, p95_ms, max_ms | qa-backend | P1 |
| 12 | MetricsReport since filter works | Old event + new event, since=new | Only new event in report | qa-backend | P2 |
| 13 | ObservationStateStore start/stop | `start()` then `stop()` | status: completed | qa-backend | P1 |
| 14 | Cannot start two active observations | `start()` twice | RuntimeError | qa-backend | P1 |
| 15 | Auto-extend when past 1 week, < 10 signals | Backdate start 8 days, 5 signals | should_extend() = True | qa-backend | P1 |
| 16 | Max duration reached at 4 weeks | Backdate start 5 weeks | is_max_duration_reached() = True | qa-backend | P1 |
| 17 | Stop marks insufficient_signals | Past 1 week + 3 signals | status: insufficient_signals | qa-backend | P1 |
| 18 | State persists across restart | start on store1, read on store2 | Same observation_id | qa-backend | P1 |
| 19 | Signal increments count | process_signal x2 | signals_processed = 2 | qa-backend | P1 |
| 20 | Deferred signal on weekend | Process signal on Saturday | outcome: deferred, deferred_until set | qa-backend | P1 |
| 21 | Trading day detection | Saturday / holiday | is_trading_day = False | qa-backend | P2 |
| 22 | Next trading day from Friday | Friday input | Returns Monday 9:30 | qa-backend | P2 |
| 23 | Shadow run summary generated | process signals, generate_summary | File at runtime/shadow_summaries/ with go/no-go checklist | qa-backend | P1 |
| 24 | Summary includes all checklist items | Generate summary | Kill switch, alert channel, ORDER_UNKNOWN, etc. | qa-backend | P2 |
| 25 | AlertDrill auto-pass | run_drill() without callback | result: PASS, incident note written | qa-backend | P1 |
| 26 | AlertDrill timeout failure | run_drill with slow callback, 0.01s timeout | result: FAILED | qa-backend | P1 |
| 27 | AlertDrill callback exception | run_drill with raising callback | result: FAILED, error has CONFIRM_CALLBACK_ERROR | qa-backend | P1 |
| 28 | Drill gate blocks without drill | check_drill_passed() with no incidents dir | Returns False | qa-backend | P1 |
| 29 | Drill gate passes after success | run_drill(), check_drill_passed() | Returns True | qa-backend | P1 |
| 30 | Incident note persisted | run_drill() | File at runtime/incidents/ with all fields | qa-backend | P1 |
| 31 | Full stack smoke: start→process→drill→summary→stop | Build full stack via build_shadow_stack | All components work end-to-end | qa-backend | P1 |
| 32 | CLI observe start | `python -m shadow observe start` | "Observation started: <uuid>" | qa-cli | P1 |
| 33 | CLI observe status | `python -m shadow observe status` | JSON with active status | qa-cli | P1 |
| 34 | CLI observe stop | `python -m shadow observe stop` | JSON with completed status | qa-cli | P1 |
| 35 | CLI observe summary | `python -m shadow observe summary` | Shadow run summary markdown | qa-cli | P2 |
| 36 | No existing module regressions | Full test suite | All 363 pre-existing tests pass | qa-backend | P1 |
