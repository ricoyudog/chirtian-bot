# QA Test Cases: phase-1-foundation-state-and-safety

## Change Summary
Python safety harness for auto-trading: config validation, runtime guard, SQLite work queue, JSONL audit ledger, idempotency dedup. 38 automated tests, all passing.

## Atom Sequence
qa-smoke → qa-backend → qa-exploratory

## Smoke Tests (qa-smoke)

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| S1 | Project installs cleanly | `pip install -e ".[dev]"` in venv | No errors, all deps resolved | P1 |
| S2 | All imports succeed | Import all public modules | No ImportError | P1 |
| S3 | Full test suite passes | `python -m pytest -v` | 38 passed, 0 failed | P1 |
| S4 | Lint clean | `ruff check src/ tests/` | All checks passed | P1 |

## Backend Tests (qa-backend)

### Config Validation

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| B1 | Config loads from project root | `load_config("config.yaml")` | Valid RuntimeConfig returned | P1 |
| B2 | Invalid mode rejected | config with `mode: "invalid"` | ValidationError raised | P1 |
| B3 | Prod + auto confirm hard fail | `environment=prod, confirmation_mode=auto` | RuntimeError from `assert_safe_to_run()` | P1 |
| B4 | Missing risk section | config without `risk` key | ValidationError raised | P1 |
| B5 | Empty account_ids | `account_ids: []` | ValidationError raised | P1 |
| B6 | Config hash deterministic | Same config loaded twice | Identical SHA-256 hash | P2 |

### Runtime Guard

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| B7 | Valid modes pass guard | `offline_replay`, `shadow`, `uat_confirm` | No exception | P1 |
| B8 | MVP guard rejects prod_confirm | `mode=prod_confirm` | RuntimeError | P1 |
| B9 | MVP guard rejects prod_auto | `mode=prod_auto` | RuntimeError | P1 |

### Work Queue (SQLite)

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| B10 | Enqueue → lease → ack happy path | Standard job lifecycle | Job status: completed | P1 |
| B11 | Enqueue → lease → retry → lease → ack | Retry lifecycle | Job recovered and completed | P1 |
| B12 | Enqueue → lease → dead_letter | Fatal failure path | Job status: dead_lettered | P1 |
| B13 | Duplicate idempotency key blocked | Same key enqueued twice | DuplicateKeyError on 2nd attempt | P1 |
| B14 | Lease returns None when empty | No pending jobs | None returned | P2 |
| B15 | Expired lease reclaimed | Lease TTL expired | Job re-leased by new worker | P1 |
| B16 | Attempt count increments on retry | retry_after called | attempt_count incremented | P2 |

### Audit Ledger (JSONL)

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| B17 | Append and read back single event | Write AuditEvent, query all | Event matches what was written | P1 |
| B18 | Query by event_type | Multiple events, filter by type | Only matching events returned | P1 |
| B19 | Query by correlation_id | Linked events | Only linked events returned | P1 |
| B20 | Query by since timestamp | Events spanning time range | Only events after threshold | P1 |
| B21 | Integrity check valid ledger | All valid JSON lines | verify_integrity() returns True | P1 |
| B22 | Integrity detects corruption | Malformed line injected | verify_integrity() returns False | P1 |
| B23 | Config hash in every event | Append events with config_hash | All events contain config_hash | P1 |

### Idempotency

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| B24 | Same inputs → same key | Identical params twice | Identical key | P1 |
| B25 | Different inputs → different keys | Vary post_id or action | Different keys | P1 |
| B26 | Case normalization | `action="buy"` vs `action="BUY"` | Same key | P2 |
| B27 | Guard blocks duplicate enqueue | Same instruction via IdempotencyGuard | 2nd blocked | P1 |

### Integration

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| I1 | Full flow: config → guard → queue → audit | Load config, validate, enqueue, lease, ack | All events audited with config hash | P1 |
| I2 | Invalid config fails fast | Invalid config.yaml | Startup fails, no queue ops | P1 |
| I3 | Idempotency in full flow | Same instruction enqueued twice | 2nd blocked, audit shows duplicate attempt | P1 |
| I4 | Prod+auto blocks everything | prod_auto config | Startup fails, no queue/audit possible | P1 |
| I5 | Queue crash recovery | Enqueue → delete queue → new WorkQueue → lease | Pending job picked up | P1 |
| I6 | Ledger corruption at startup | Corrupted JSONL file | Integrity check detects corruption | P1 |

## Exploratory (qa-exploratory)

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| E1 | Edge case: empty payload | `enqueue("test", key, {})` | Handles gracefully | P2 |
| E2 | Very long idempotency key | 10KB key string | Behavior defined (error or truncate) | P2 |
| E3 | Concurrent lease attempts | Two workers leasing simultaneously | No double-lease, one gets None | P2 |
| E4 | Ledger file permissions | Read-only ledger path | Appropriate error on append | P2 |
| E5 | Retry after 0 seconds | `retry_after(job_id, 0, "test")` | Immediately available for lease | P2 |
| E6 | Dead letter is terminal | dead_letter → try lease again | Not claimable | P2 |
