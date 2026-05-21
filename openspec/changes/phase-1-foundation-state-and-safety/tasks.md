# Tasks: Phase 1 — Foundation, State & Safety Skeleton

## 1. Project Scaffold & Config

- [ ] Initialize `pyproject.toml` with project metadata, dependencies (`pydantic>=2.0`, `pyyaml`, `pytest`, `ruff`), and entry points
- [ ] Create `src/` package layout with `__init__.py` files for `config/`, `safety/`, `state/`
- [ ] Create `tests/` directory with `conftest.py` (shared fixtures: tmp SQLite, tmp ledger, sample configs)
- [ ] Create `config.yaml` schema at project root with Phase 1 fields (runtime, risk, portfolio, executor sections)
- [ ] Implement `src/config/settings.py` — Pydantic v2 models: `RuntimeConfig`, `RiskConfig`, with field validators
- [ ] Implement `src/config/validation.py` — `load_config(path)`, `validate_startup(config)`, `compute_config_hash(config)`

**Estimated**: ~1.5 hours

---

## 2. Runtime Mode Guard

- [ ] Implement `src/safety/runtime_guard.py` — `RuntimeGuard` class with `assert_safe_to_run()` and `assert_mutation_allowed()`
- [ ] Add guard rules: `prod + auto_confirm` hard fail, MVP mode allowlist (`offline_replay`, `shadow`, `uat_confirm`)
- [ ] Write `tests/test_runtime_guard.py` — cover: prod+auto hard fail, valid modes pass, invalid mode rejected, MVP mode restriction

**Estimated**: ~0.5 hours

---

## 3. Durable Work Queue

- [ ] Implement `src/state/models.py` — `Job` dataclass/model with all queue fields (job_id, job_type, idempotency_key, status, attempt_count, leased_by, lease_expires_at, next_retry_at, last_error, created_at, updated_at)
- [ ] Implement `src/state/queue.py` — `WorkQueue` class with SQLite backend
  - [ ] `_init_db()` — create table if not exists, enable WAL mode
  - [ ] `enqueue(job_type, idempotency_key, payload)` — insert with `UNIQUE(idempotency_key)` constraint
  - [ ] `lease(worker_id, ttl_seconds)` — atomically claim next pending job, set lease expiry
  - [ ] `ack(job_id)` — mark as completed
  - [ ] `retry_after(job_id, delay_seconds, reason)` — reset to pending after delay
  - [ ] `dead_letter(job_id, reason)` — move to terminal dead_lettered state
  - [ ] `get(job_id)` — retrieve by ID
- [ ] Write `tests/test_queue.py` — cover:
  - [ ] enqueue → lease → ack happy path
  - [ ] enqueue → lease → retry_after → lease → ack
  - [ ] enqueue → lease → dead_letter
  - [ ] duplicate idempotency_key raises error
  - [ ] lease with no pending jobs returns None
  - [ ] expired lease can be reclaimed
  - [ ] attempt_count increments on retry

**Estimated**: ~2 hours

---

## 4. Audit Ledger

- [ ] Add `AuditEvent` model to `src/state/models.py` — event_id, timestamp, event_type, config_hash, source, data, correlation_id
- [ ] Implement `src/state/ledger.py` — `AuditLedger` class with JSONL backend
  - [ ] `append(event)` — write JSON line, raise on failure
  - [ ] `query(event_type, correlation_id, since)` — read-only filter
  - [ ] `verify_integrity()` — validate all lines are parseable JSON
- [ ] Write `tests/test_ledger.py` — cover:
  - [ ] append single event and read back
  - [ ] append multiple events, query by type
  - [ ] query by correlation_id
  - [ ] query by since timestamp
  - [ ] verify_integrity passes for valid ledger
  - [ ] verify_integrity detects malformed lines
  - [ ] config_hash present in every event

**Estimated**: ~1.5 hours

---

## 5. Idempotency Key Helpers

- [ ] Implement `src/safety/idempotency.py` — `generate_idempotency_key(post_id, sequence, action, symbol, quantity_pct)` using SHA-256
- [ ] Add `IdempotencyGuard` class that wraps WorkQueue's UNIQUE constraint with explicit `check_and_enqueue()` method
- [ ] Write `tests/test_idempotency.py` — cover:
  - [ ] same inputs → same key (deterministic)
  - [ ] different inputs → different keys
  - [ ] case normalization (action/symbol uppercased)
  - [ ] float precision handling for quantity_pct
  - [ ] duplicate key blocked on second enqueue

**Estimated**: ~1 hour

---

## 6. Safety Integration Tests

- [ ] Write `tests/test_safety_integration.py` — full flow tests:
  - [ ] Config load → validation → guard → config hash in audit
  - [ ] Config load with invalid fields → startup fails fast
  - [ ] Valid config → enqueue job → lease → audit event recorded → ack → audit event recorded
  - [ ] Idempotency: same instruction enqueued twice → second blocked → audit shows duplicate attempt
  - [ ] Runtime guard: prod+auto config fails at startup, no queue operations possible
  - [ ] Queue crash simulation: enqueue → process killed (simulated) → restart → lease picks up pending job
  - [ ] Ledger integrity check at startup detects corruption
- [ ] Ensure all tests pass with `pytest` and no external credentials needed

**Estimated**: ~1.5 hours

---

## Summary

| Group | Name | Estimated | Dependencies |
|-------|------|-----------|--------------|
| 1 | Project Scaffold & Config | ~1.5h | None |
| 2 | Runtime Mode Guard | ~0.5h | Group 1 |
| 3 | Durable Work Queue | ~2h | Group 1 |
| 4 | Audit Ledger | ~1.5h | Group 1 |
| 5 | Idempotency Key Helpers | ~1h | Groups 1, 3 |
| 6 | Safety Integration Tests | ~1.5h | Groups 1-5 |

**Total estimated**: ~8 hours
