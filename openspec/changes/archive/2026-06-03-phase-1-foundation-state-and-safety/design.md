# Design: Phase 1 — Foundation, State & Safety Skeleton

## 1. Package Layout

```
src/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── settings.py          # Pydantic settings models
│   └── validation.py        # Startup validation + config hash
├── safety/
│   ├── __init__.py
│   ├── runtime_guard.py     # Mode guard (prod + auto_confirm hard fail)
│   └── idempotency.py       # Key generation + dedup check
├── state/
│   ├── __init__.py
│   ├── queue.py             # SQLite durable work queue
│   ├── ledger.py            # JSONL append-only audit ledger
│   └── models.py            # Data models (Job, AuditEvent, etc.)
└── ...
tests/
├── conftest.py              # Shared fixtures (tmp SQLite, tmp ledger)
├── test_config_validation.py
├── test_runtime_guard.py
├── test_idempotency.py
├── test_queue.py
├── test_ledger.py
└── test_safety_integration.py
```

---

## 2. Config Schema (Pydantic)

### 2.1 Decision: Pydantic v2 BaseModel with YAML loader

使用 Pydantic v2 定義 config schema，從 `config.yaml` 讀入後做 full validation。啟動時 fail fast，任何 invalid 欄位直接 raise。

### 2.2 Config Model

```python
class RuntimeConfig(BaseModel):
    mode: Literal["offline_replay", "shadow", "uat_confirm", "prod_confirm", "prod_auto"]
    environment: Literal["uat", "prod"]
    region: str
    account_ids: list[str]
    confirmation_mode: Literal["auto", "confirm", "skip"]
    risk: RiskConfig

class RiskConfig(BaseModel):
    max_notional_usd: float = 10000
    max_quantity: int = 1000
    max_concentration_pct: float = 10.0
    symbol_whitelist: list[str] = []
```

### 2.3 Startup Validation Rules

| Rule | Validation |
|------|-----------|
| Mode consistency | `prod_auto` only if `environment == "prod"` |
| Safety guard | `environment == "prod"` AND `confirmation_mode == "auto"` → hard fail |
| Account allowlist | `account_ids` non-empty |
| Region | Must match supported regions |
| Risk limits | All numeric limits > 0 |

### 2.4 Config Hash

啟動時計算 config SHA-256 hash，存入 `config_hash` 字串。每次 audit event 都附帶此 hash，讓每筆 decision 可追溯當時設定。

```python
import hashlib, json

def compute_config_hash(config: RuntimeConfig) -> str:
    canonical = json.dumps(config.model_dump(mode="json"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
```

---

## 3. Runtime Mode Guard

### 3.1 Decision: Single entry point `assert_safe_to_run()`

在 daemon 啟動時（或任何 mutating operation 前）呼叫 `assert_safe_to_run(config)`。

```python
class RuntimeGuard:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def assert_safe_to_run(self) -> None:
        """Raises RuntimeError if unsafe configuration detected."""
        if self.config.environment == "prod" and self.config.confirmation_mode == "auto":
            raise RuntimeError(
                "FATAL: prod environment with auto confirmation is not allowed. "
                "Set confirmation_mode to 'confirm' or switch environment to 'uat'."
            )

    def assert_mutation_allowed(self) -> None:
        """Call before any mutating broker operation."""
        if self.config.confirmation_mode != "auto":
            # Log that manual confirmation is required
            pass
```

### 3.2 MVP Mode

MVP allowed mode: only `uat_confirm` and safer (`offline_replay`, `shadow`). `prod_confirm` and `prod_auto` are not yet supported.

---

## 4. Durable Work Queue (SQLite)

### 4.1 Decision: SQLite for durability, single-writer

MVP 使用 SQLite 作為 durable queue storage。Single account、single worker 不需要分散式鎖。SQLite WAL mode 提供合理的 concurrent read。

### 4.2 Schema

```sql
CREATE TABLE IF NOT EXISTS work_queue (
    job_id         TEXT PRIMARY KEY,
    job_type       TEXT NOT NULL,
    idempotency_key TEXT UNIQUE,
    payload        TEXT NOT NULL,  -- JSON
    status         TEXT NOT NULL DEFAULT 'pending',
    attempt_count  INTEGER NOT NULL DEFAULT 0,
    leased_by      TEXT,
    lease_expires_at TEXT,
    next_retry_at  TEXT,
    last_error     TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 4.3 Interface

```python
class WorkQueue:
    def __init__(self, db_path: Path):
        ...

    def enqueue(self, job_type: str, idempotency_key: str, payload: dict) -> str:
        """Returns job_id. Raises DuplicateKeyError if key exists."""

    def lease(self, worker_id: str, ttl_seconds: int = 300) -> Optional[Job]:
        """Atomically claim the next pending job."""

    def ack(self, job_id: str) -> None:
        """Mark job as completed."""

    def retry_after(self, job_id: str, delay_seconds: int, reason: str) -> None:
        """Re-queue for retry after delay."""

    def dead_letter(self, job_id: str, reason: str) -> None:
        """Move to dead letter queue. Terminal state."""

    def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
```

### 4.4 Status Flow

```
pending → leased → completed
                  → retry_pending → pending (after next_retry_at)
                  → dead_lettered (terminal)
```

---

## 5. Append-Only Audit Ledger (JSONL)

### 5.1 Decision: JSONL for simplicity and auditability

每行一個 JSON event。Append-only：不提供 delete/update。旋轉策略由後續 phase 處理。

### 5.2 Event Schema

```python
class AuditEvent(BaseModel):
    event_id: str              # UUID
    timestamp: datetime        # ISO-8601
    event_type: str            # e.g., "config_loaded", "job_enqueued", "safety_violation"
    config_hash: str           # SHA-256 of config at time of event
    source: str                # Module/component that produced the event
    data: dict                 # Event-specific payload
    correlation_id: Optional[str] = None  # Links related events
```

### 5.3 Interface

```python
class AuditLedger:
    def __init__(self, ledger_path: Path):
        ...

    def append(self, event: AuditEvent) -> None:
        """Append event. Raises if write fails — never silently drops."""

    def query(
        self,
        event_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> list[AuditEvent]:
        """Read-only query. For replay / audit inspection."""

    def verify_integrity(self) -> bool:
        """Check that every line is valid JSON. For startup health check."""
```

---

## 6. Idempotency Key Helpers

### 6.1 Decision: SHA-256 of deterministic fields

Idempotency key = SHA-256 of canonical JSON composed from stable identifiers（post_id + sequence + normalized action/symbol/qty）。

```python
def generate_idempotency_key(
    post_id: str,
    sequence: int,
    action: str,
    symbol: str,
    quantity_pct: float,
) -> str:
    canonical = json.dumps({
        "post_id": post_id,
        "sequence": sequence,
        "action": action.upper(),
        "symbol": symbol.upper(),
        "quantity_pct": quantity_pct,
    }, sort_keys=True)
    return "idem:" + hashlib.sha256(canonical.encode()).hexdigest()[:16]
```

### 6.2 Dedup Check

透過 `work_queue.idempotency_key` UNIQUE constraint 實作。Enqueue 時如果 key 已存在，raise `DuplicateKeyError`。

---

## 7. Key Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Pydantic v2 for config | Type-safe validation, YAML load, IDE support |
| 2 | SQLite for queue | Durable, single-writer, WAL mode, no external deps |
| 3 | JSONL for audit | Append-only, human-readable, grep-friendly |
| 4 | SHA-256 idempotency keys | Deterministic, stable across replays |
| 5 | Startup validation only | MVP 不支援 hot reload；config 改動應 restart |
| 6 | Config hash in every audit event | 可追溯每筆 decision 對應的當時設定 |
| 7 | Single worker model | MVP scope：single account、single worker、US equities only |
| 8 | No external deps for tests | Tests 不需要 Webull / LLM / broker credential |

---

## 8. Dependencies

| Package | Purpose |
|---------|---------|
| `pydantic>=2.0` | Config models + validation |
| `pyyaml` | Load config.yaml |
| `pytest` | Testing |
| `ruff` | Linting + formatting |

No broker, LLM, or external API dependencies in Phase 1.

---

## 9. Testing Strategy

| Test Category | What It Covers |
|---------------|----------------|
| Config validation | Invalid mode combos, missing fields, out-of-range values |
| Runtime guard | `prod + auto_confirm` hard fail, MVP mode restriction |
| Queue lifecycle | enqueue → lease → ack, enqueue → lease → retry_after → lease → ack, enqueue → lease → dead_letter |
| Queue idempotency | Duplicate key rejected, same key after dead_letter |
| Ledger append | Write event, read back, query by type/correlation_id |
| Ledger integrity | Malformed line detection |
| Idempotency keys | Deterministic generation, different inputs → different keys |
| Config hash | Same config → same hash, different config → different hash |
| Integration | Full flow: config load → guard → enqueue → lease → audit → ack |
