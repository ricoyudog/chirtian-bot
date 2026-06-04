# Stop-the-World Mechanism Feasibility Analysis

## Executive Summary

The existing codebase has clean extension points for a stop-the-world mechanism. The recommended approach is a **two-layer gate**: RuntimeGuard holds a reconcile status flag that blocks `assert_mutation_allowed()`, while WorkQueue gains a `paused` state that prevents new leases. This avoids a single point of failure and gives operators fine-grained control.

---

## 1. Current Architecture Map

### 1.1 RuntimeGuard (`src/safety/runtime_guard.py`)

RuntimeGuard is a **stateless check gate**. It holds a reference to `RuntimeConfig` and exposes two methods:

- **`assert_safe_to_run()`** (line 18) — Called once at daemon startup. Checks two conditions:
  1. `prod + auto` combination is fatal (line 20-24)
  2. Mode must be in `MVP_ALLOWED_MODES` set (line 26-30)
- **`assert_mutation_allowed()`** (line 32) — Called before any mutating broker operation. Only blocks the `prod + auto` combination (line 39-42).

**Key observation**: RuntimeGuard has no mutable state. It is a pure function of `RuntimeConfig`. This makes it safe to extend with an additional runtime flag without worrying about concurrency within a single process.

### 1.2 WorkQueue (`src/state/queue.py`)

WorkQueue is a **SQLite-backed durable queue** with lease semantics:

- **`lease(worker_id, ttl_seconds=300)`** (line 68) — Atomically claims the next available job. Selects from `pending` jobs with expired/no retry timer, or `leased` jobs with expired leases. Uses `SELECT ... LIMIT 1` with `ORDER BY created_at ASC` (line 77-89), then atomically updates to `leased` status (line 94-105).
- **`ack(job_id)`** (line 114) — Marks job as `completed`.
- **`retry_after(job_id, delay_seconds, reason)`** (line 126) — Returns job to `pending` with a retry delay.
- **`dead_letter(job_id, reason)`** (line 150) — Terminal state for poison messages.
- Uses WAL journal mode (line 28) for concurrent read/write safety.

**Key observation**: The `lease()` method's SQL query (line 77-89) is the ideal injection point for stop-the-world. Adding a `WHERE` clause to check a global pause flag would prevent any new work from being claimed without affecting in-flight leases.

### 1.3 AuditLedger (`src/state/ledger.py`)

Append-only JSONL ledger with:

- **`append(event)`** (line 15) — Writes a single AuditEvent as a JSON line.
- **`query(event_type, correlation_id, since)`** (line 33) — Reads all events and filters in-memory. Suitable for low-volume audit trails.
- **`verify_integrity()`** (line 45) — Validates every line is parseable JSON.

**Key observation**: The ledger is the natural place to record stop-the-world activation/deactivation events with full correlation IDs. The `event_type` field can carry `"stop_the_world_activated"` and `"stop_the_world_deactivated"`.

### 1.4 Data Models (`src/state/models.py`)

Two dataclasses:

- **`Job`** (line 14) — Queue job with status lifecycle: `pending -> leased -> completed | dead_lettered`. Has `attempt_count`, `leased_by`, `lease_expires_at`, `next_retry_at`, `last_error`.
- **`AuditEvent`** (line 30) — Audit trail entry with `event_id`, `timestamp`, `event_type`, `config_hash`, `source`, `data`, `correlation_id`.

**Key observation**: The `data: dict[str, Any]` field on AuditEvent is flexible enough to carry reconcile mismatch details without schema changes.

### 1.5 Config (`src/config/settings.py`)

- **`RuntimeConfig`** (line 17) — Pydantic v2 model with `mode`, `environment`, `region`, `account_ids`, `confirmation_mode`, and nested `RiskConfig`.
- **`RiskConfig`** (line 8) — Trade-level risk limits: `max_notional_usd`, `max_quantity`, `max_concentration_pct`, `symbol_whitelist`.

**Key observation**: RuntimeConfig is frozen at load time. A stop-the-world flag must be runtime-mutable and cannot live in this Pydantic model. It needs a separate mechanism.

---

## 2. Answering the Key Design Questions

### Q1: Can RuntimeGuard be extended with a reconcile check?

**Yes, cleanly.** The recommended extension:

```python
# In RuntimeGuard, add mutable state
class RuntimeGuard:
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self._stopped = False  # NEW: reconcile stop flag
        self._stopped_reason: str | None = None

    def assert_mutation_allowed(self) -> None:
        # Existing prod+auto check (line 39-42) stays
        if self.config.environment == "prod" and self.config.confirmation_mode == "auto":
            raise RuntimeError(...)

        # NEW: reconcile gate
        if self._stopped:
            raise RuntimeError(
                f"FATAL: mutation blocked — system stopped: {self._stopped_reason}"
            )

    def activate_stop(self, reason: str) -> None:
        self._stopped = True
        self._stopped_reason = reason

    def deactivate_stop(self) -> None:
        self._stopped = False
        self._stopped_reason = None

    @property
    def is_stopped(self) -> bool:
        return self._stopped
```

This is safe because:
- RuntimeGuard is constructed once at daemon startup and shared across the process
- Python's GIL ensures `self._stopped` reads/writes are atomic for boolean values
- The flag only gates forward — it cannot cause data corruption

### Q2: Should stop-the-world be at queue level (block lease) or guard level (block mutation)?

**Both, at different layers.** They serve different purposes:

| Layer | What it blocks | When it fires | Recovery |
|-------|---------------|---------------|----------|
| **Guard level** (`assert_mutation_allowed`) | Broker mutations (order submission) | Before order is sent to broker | Automatic after `deactivate_stop()` |
| **Queue level** (`lease` blocking) | New work being claimed | Before worker picks up next job | Automatic after pause cleared |

The guard-level check is the **hard gate** — even if a worker already has a leased job, the actual broker mutation will be blocked. The queue-level pause is the **soft gate** — prevents workers from picking up new work, allowing in-flight work to drain.

**Recommendation**: Implement guard-level first (simpler, fewer changes). Add queue-level as a refinement.

### Q3: How does the existing kill switch mechanism work?

The current "kill switch" is the `prod + auto` combination check in both `assert_safe_to_run()` (line 20) and `assert_mutation_allowed()` (line 39). It is:
- **Static** — determined entirely by config, not mutable at runtime
- **Terminal** — raises `RuntimeError`, crashing the daemon
- **Config-time** — can only be changed by editing the YAML and restarting

The stop-the-world mechanism must be **runtime-mutable** — activated by a reconcile mismatch during operation, not by config.

### Q4: What is the recovery path?

**Recommended three-level recovery:**

1. **Automatic recovery**: Reconcile succeeds on next check cycle. The reconciler calls `deactivate_stop()` on the guard.
2. **Manual recovery**: Operator sends a signal (e.g., SIGUSR1) or CLI command that clears the stop flag.
3. **Cold restart**: If the daemon is killed, the stop flag is lost (it is in-memory only). On restart, the reconcile check runs before any work is leased, so if the mismatch persists, stop-the-world reactivates immediately.

**Queue-level recovery** requires an additional mechanism since the SQLite database persists across restarts:

```python
# Option A: Separate metadata table
CREATE TABLE IF NOT EXISTS system_flags (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
# INSERT/UPDATE system_flags SET value='stopped' WHERE key='reconcile_status'
```

```python
# Option B: In-memory flag, re-validated on startup
# The daemon's startup sequence runs reconcile check before leasing,
# so no persistent flag is needed at queue level.
```

**Recommendation**: Option B (no persistent flag). The reconcile check itself is the source of truth. On restart, reconcile runs and either activates or does not activate stop-the-world based on actual state.

---

## 3. Concrete Implementation Recommendations

### Phase A: Guard-Level Stop-the-World (Minimal Viable)

**Files to modify:**
1. `src/safety/runtime_guard.py` — Add `_stopped` flag, `activate_stop()`, `deactivate_stop()`, extend `assert_mutation_allowed()`
2. `src/state/models.py` — No changes needed (AuditEvent `data` dict is flexible enough)
3. `src/state/ledger.py` — No changes needed

**New code in RuntimeGuard:**
```python
def assert_mutation_allowed(self) -> None:
    # Existing check stays
    if self.config.environment == "prod" and self.config.confirmation_mode == "auto":
        raise RuntimeError("FATAL: mutation blocked — prod environment with auto confirmation.")

    # NEW: reconcile stop gate
    if self._stopped:
        raise RuntimeError(
            f"FATAL: mutation blocked — system stopped: {self._stopped_reason}"
        )
```

### Phase B: Queue-Level Pause (Refinement)

**Files to modify:**
1. `src/state/queue.py` — Add `pause_lease()` / `resume_lease()` methods, modify `lease()` SQL

**Approach**: Add an in-memory `_paused` flag to WorkQueue. When paused, `lease()` returns `None` immediately without querying SQLite.

```python
class WorkQueue:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        self._paused = False  # NEW
        self._init_db()

    def pause(self, reason: str) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def lease(self, worker_id: str, ttl_seconds: int = 300) -> Optional[Job]:
        if self._paused:  # NEW: fast-return when stopped
            return None
        # ... existing lease logic ...
```

This is simpler than a SQL-level check and preserves the existing query logic unchanged. Since WorkQueue is single-process (SQLite), no cross-process coordination is needed.

### Phase C: Reconcile Orchestrator (New Module)

**New file: `src/safety/reconcile.py`**

This module ties RuntimeGuard and WorkQueue together:

```python
class ReconcileGate:
    """Runs periodic reconcile checks and manages stop-the-world state."""

    def __init__(
        self,
        guard: RuntimeGuard,
        queue: WorkQueue,
        ledger: AuditLedger,
    ):
        self.guard = guard
        self.queue = queue
        self.ledger = ledger

    def check_and_gate(self, reconcile_result: ReconcileResult) -> None:
        if reconcile_result.mismatch:
            self.guard.activate_stop(reconcile_result.reason)
            self.queue.pause(reason=reconcile_result.reason)
            self._audit("stop_the_world_activated", reconcile_result)
        elif self.guard.is_stopped:
            self.guard.deactivate_stop()
            self.queue.resume()
            self._audit("stop_the_world_deactivated", reconcile_result)

    def _audit(self, event_type: str, result: ReconcileResult) -> None:
        self.ledger.append(AuditEvent(
            event_type=event_type,
            source="reconcile_gate",
            data={"reason": result.reason, "details": result.details},
        ))
```

### Phase D: Startup Integration

The daemon startup sequence (not yet implemented in codebase) should follow this order:

```
1. load_config()           -> src/config/validation.py:12
2. validate_startup()      -> src/config/validation.py:22
3. RuntimeGuard(config)    -> src/safety/runtime_guard.py:15
4. guard.assert_safe_to_run()  -> line 18
5. WorkQueue(db_path)      -> src/state/queue.py:22
6. AuditLedger(ledger_path) -> src/state/ledger.py:11
7. ReconcileGate(guard, queue, ledger)
8. reconcile_gate.check_and_gate(initial_result)  # gate on startup
9. queue.lease() loop begins
```

---

## 4. Risk Assessment

| Risk | Mitigation |
|------|-----------|
| `_stopped` flag race condition | Python GIL makes boolean reads/writes atomic; for multi-threaded daemon, use `threading.Lock` |
| Stop-the-world fires on transient mismatch | Add tolerance threshold to `ReconcileResult` (e.g., only stop after N consecutive mismatches) |
| Operator cannot clear stop remotely | Add SIGUSR1/SIGUSR2 signal handler or CLI command to `deactivate_stop()` |
| In-flight leases complete after stop | This is acceptable — the guard blocks the mutation, not the lease. Worker will ack/retry the job harmlessly |
| Stop flag lost on crash | Feature, not bug — on restart, reconcile re-checks and re-activates if still mismatched |

---

## 5. Implementation Priority

1. **Guard-level stop** (Phase A) — 1 file, ~15 lines of new code. Blocks the dangerous path immediately.
2. **ReconcileGate orchestrator** (Phase C) — New module, ~40 lines. Wires the pieces together.
3. **Queue-level pause** (Phase B) — 1 file, ~10 lines. Prevents workers from wasting cycles on jobs they cannot mutate.
4. **Startup integration** (Phase D) — Depends on daemon main loop being implemented.

Phases A and C can be done together as a single unit of work. Phase B is a refinement that can follow.
