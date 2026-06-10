# QA Report

## Session Metadata

| Field | Value |
|-------|-------|
| Session ID | QA-phase-4-webull-uat-executor-20260609-001 |
| Tester | Agent + Human review |
| Date | 2026-06-09 |
| Build / Commit | 38fa82d |
| Change | phase-4-webull-uat-executor |
| Risk Level | HIGH |

## Charter

Verify that the first broker integration layer (Webull UAT executor) correctly and safely transforms SizingDecisions into auditable UAT order flows with proper safety gates.

## Human Test Case Results

No human test cases provided — atom-generated cases used from specs.

| # | Scenario | Expected | Actual | Status | Evidence |
|---|----------|----------|--------|--------|----------|
| 1 | Happy path BUY: SizingDecision → place | Full flow with audit trail | 762 tests pass, 0 fail | PASS | pytest output |
| 2 | Prod environment blocked | EnvironmentBlockedError raised | Guard in ExecutionGate.check_environment | PASS | test_order_builder.py |
| 3 | Idempotency guard blocks duplicate place | DuplicateExecutionError raised | Guard in ExecutionGate.check_idempotency | PASS | test_executor_integration.py |
| 4 | ORDER_UNKNOWN after timeout | Status transitions to "unknown" | handle_unknown sets status correctly | PASS | test_executor_integration.py |
| 5 | Confirmation 15 min timeout | EXPIRED_REVIEW, dead-lettered | Deadline tracking + dead_letter | PASS | test_executor_integration.py |
| 6 | Broker auth failure | BrokerAuthError raised | Detected from stderr or JSON detail | PASS | test_webull_adapter.py |

## Smoke Test Results

| Check | Status | Notes |
|-------|--------|-------|
| All modules importable | PASS | 12 modules imported without error |
| Core flow instantiable | PASS | RuntimeConfig, SizingDecision, Factory, OrderBuilder all construct correctly |
| Full test suite green | PASS | 762 passed, 6 skipped, 0 failures |

## Backend Walkthrough

### Entry Point
- **Path**: `src/executor/factory.py:10`
- **Function**: `build_execution_intent(sizing, config)`
- **Route**: Library API (no HTTP route)

### Call Chain

| Layer | File | Function | Input | Output | Side Effects |
|-------|------|----------|-------|--------|--------------|
| L1 | factory.py:10 | `build_execution_intent` | SizingDecision + RuntimeConfig | ExecutionIntent or None | None |
| L2 | order_builder.py:22 | `OrderBuilder.build_order_json` | ExecutionIntent | Webull order dict (10 keys) | None |
| L3 | execution_gate.py:35 | `check_environment` | RuntimeConfig.environment | None or EnvironmentBlockedError | None |
| L3 | execution_gate.py:53 | `check_idempotency` | idempotency_key string | None or DuplicateExecutionError | Ledger read |
| L3 | execution_gate.py:90 | `record_attempt` | ExecutionAttempt | None | AuditLedger append |
| L4 | confirmation.py:58 | `enter_review` | ExecutionIntent | job_id string | WorkQueue INSERT, deadline stored |
| L4 | confirmation.py:102 | `confirm` | execution_id | ExecutionIntent (ready) | WorkQueue UPDATE |
| L5 | webull_adapter.py:108 | `preview_order` | account_id, order_json | payload dict | Temp file + subprocess |
| L5 | webull_adapter.py:112 | `place_order` | account_id, order_json | payload dict | Temp file + subprocess |

### Happy Path
- Input: SizingDecision(EXECUTABLE, AAPL, BUY, qty=10, price=180)
- Flow: Factory → OrderBuilder → Gate(env+idempotency) → Preview → Confirm → Place → Audit
- Data store: AuditLedger (2 events: preview_order + place_order)
- **Status: PASS**

### Error Paths

| Error | Detection Point | Exception | Propagation | Status |
|-------|-----------------|-----------|-------------|--------|
| Prod blocked | ExecutionGate.check_environment | EnvironmentBlockedError | Raised before any broker call | PASS |
| Duplicate place | ExecutionGate.check_idempotency | DuplicateExecutionError | Queries ledger for matching key+op+status | PASS |
| Broker timeout | WebullCLIAdapter._run_cli | BrokerTimeoutError | Chained from TimeoutExpired | PASS |
| Confirmation timeout | ConfirmationManager.check_timeouts | No exception (status change) | Status→expired_review, job→dead_lettered | PASS |
| Broker auth failure | WebullCLIAdapter._run_cli | BrokerAuthError | Detected from stderr/JSON detail | PASS |

### Auth Pyramid

| Level | Applicable | Notes |
|-------|-----------|-------|
| Unauthenticated | N/A | Library, not web service |
| Authenticated | N/A | No user identity system |
| Authorized | N/A | No role-based access |
| Admin | N/A | No admin concept |
| **Environment guard** | Yes | ExecutionGate.check_environment is the sole access gate: only "uat" allowed |
| **Broker auth** | Yes | WebullCLIAdapter detects auth failures from CLI output |

### Data Integrity

| Aspect | Status | Notes |
|--------|--------|-------|
| Audit ledger append-only | PASS | Only `append()` method, no update/delete |
| Ledger tamper-evident | PARTIAL | `verify_integrity()` checks JSON validity only, no hash chain or HMAC |
| Idempotency guard correctness | PASS | Checks triple: key + operation("place_order") + status("success") |
| Confirmation timeout independent of WorkQueue lease | PASS | Uses internal `_deadlines` dict, not WorkQueue TTL |

## Exploratory Findings

| # | Finding | Severity | Category | Evidence | Bug Filed? |
|---|---------|----------|----------|----------|------------|
| 1 | `model_copy(update={...})` bypasses Pydantic field validators (e.g., quantity ge=1) | minor | Data Integrity | `intent.model_copy(update={'quantity': -1})` succeeds without error | No — already mitigated in `reduce_quantity` with explicit validation |
| 2 | `compute_idempotency_key("", "", 0)` succeeds — empty/zero inputs produce a hash | minor | Edge Case | Function accepts any string/int without validation | No — ExecutionIntent model validators prevent empty symbols and zero quantities |
| 3 | `check_idempotency` loads ALL execution_attempt events into memory (linear scan) | minor | Performance | `self._ledger.query(event_type="execution_attempt")` with no limit | No — acceptable for MVP ledger sizes |

## Bug Reports

No bugs with severity >= major found.

## QA Conclusion

| Field | Value |
|-------|-------|
| Status | PASSED |
| Blocking Bugs | 0 |
| Archive Recommendation | PROCEED |
| Notes | All safety gates verified. 3 minor exploratory findings (model_copy bypass, empty inputs, linear scan) — none blocking. Audit ledger tamper-evidence is weak (JSON-only validation) but acceptable for MVP. |

## Evidence Inventory

| # | Type | Path / URL | Referenced In |
|---|------|-----------|---------------|
| 1 | Test output | pytest: 762 passed, 6 skipped, 0 failures | Smoke + Functional |
| 2 | Lint output | ruff: All checks passed | Smoke |
| 3 | GitHub review comment | https://github.com/ricoyudog/chirtian-bot/issues/28#issuecomment-4656761824 | Review |
| 4 | GitHub verify comment | https://github.com/ricoyudog/chirtian-bot/issues/28#issuecomment-4656739792 | Verify |
