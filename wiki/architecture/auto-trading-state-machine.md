---
type: wiki
created: 2026-05-20
updated: 2026-06-23
tags: [architecture, trading, state-machine, idempotency, auto-trading]
status: draft
---

# Auto Trading State Machine

> **實作（2026-06）**：durable queue=`src/state/queue.py`、audit=`src/state/ledger.py`、idempotency=`src/safety/idempotency.py` + `ExecutionGate.check_idempotency`（attempt 須帶 `idempotency_key`，見 [[wiki/architecture/implicit-contracts]]）。本頁為概念設計；實際狀態轉移見 [[wiki/decisions/2026-06-15-pipeline-orchestrator]]。

> 從 [[wiki/architecture/auto-trading-pipeline-High-level|auto-trading-pipeline]] 拆出的 workflow/state/idempotency 設計。目標：可恢復、可重放、不可重複下單。

## 1. Core Principle

所有交易相關動作必須可追蹤、可恢復、可重放。

Hard invariants:
1. 同一篇 post 重跑不會重複下單。
2. crash 後不漏 signal。
3. broker ack unknown 時不可直接 retry `place_order`。
4. 本地與 Webull 不一致時 stop-the-world。
5. 每個狀態轉移都寫 ledger/audit。

---

## 2. Canonical State Flow

```text
DISCOVERED_POST
  → POST_SAVED
  → INSTRUCTIONS_PARSED
  → ANALYSIS_REQUESTED
  → ANALYSIS_COMPLETED | ANALYSIS_FAILED
  → RECOMMENDATION_READY
  → PORTFOLIO_SYNCED
  → RECONCILED | RECONCILE_FAILED
  → SIZED | SIZING_SKIPPED | SIZING_NEEDS_REVIEW
  → HUMAN_REVIEW_PENDING | EXECUTION_READY
  → ORDER_PREVIEWED
  → ORDER_SUBMITTING
  → ORDER_ACKED | ORDER_UNKNOWN | ORDER_REJECTED
  → PARTIALLY_FILLED | FILLED | CANCELLED | DEAD_LETTER
```

### Human-required states
- `ANALYSIS_FAILED`
- `RECONCILE_FAILED`
- `SIZING_NEEDS_REVIEW`
- `HUMAN_REVIEW_PENDING`
- `ORDER_UNKNOWN`
- `DEAD_LETTER`

---

## 3. Required Data Models

### PostEnvelope
```json
{
  "post_id": "substack:20260520:slug-or-hash",
  "publication": "christian1hedge",
  "published_at": "2026-05-20T09:00:00-04:00",
  "detected_at": "2026-05-20T21:03:00+08:00",
  "content_hash": "sha256:...",
  "source_url": "https://...",
  "saved_path": "christian log/2026-05/20/title.md",
  "ingest_attempt": 1
}
```

### InstructionIntent
```json
{
  "instruction_id": "instr_...",
  "post_id": "substack:...",
  "sequence": 1,
  "action": "buy|sell|short|cover|option_place|option_cover",
  "symbol": "NVDA",
  "market": "US",
  "quantity_pct": 1.0,
  "time_modifier": "immediate|open|close|scheduled",
  "scheduled_for": null,
  "confidence": 0.92,
  "parse_span": "原文片段",
  "raw_text": "今天加倉 nvda 1%",
  "idempotency_key": "sha256(post_id + sequence + normalized action/symbol/qty)"
}
```

### AnalysisJob / Recommendation
```json
{
  "analysis_id": "ana_...",
  "instruction_id": "instr_...",
  "status": "completed|failed|timeout|degraded",
  "ta_verdict": "green|yellow|red|unavailable",
  "human_review_required": false,
  "reason_codes": ["TA_GREEN", "SAME_DIRECTION"],
  "completed_at": "2026-05-20T22:00:00+08:00"
}
```

### ExecutionIntent
```json
{
  "execution_id": "exec_...",
  "instruction_id": "instr_...",
  "idempotency_key": "same or derived key",
  "symbol": "NVDA",
  "side": "BUY",
  "quantity": 2,
  "order_type": "LIMIT",
  "limit_price": 180.0,
  "environment": "uat",
  "status": "ready|previewed|submitting|acked|unknown|rejected|filled|cancelled"
}
```

### ExecutionAttempt
```json
{
  "attempt_id": "att_...",
  "execution_id": "exec_...",
  "attempt_no": 1,
  "operation": "preview_order|place_order|get_order_status|cancel_order",
  "request_hash": "sha256:...",
  "broker_order_id": null,
  "status": "success|timeout|error|unknown",
  "response": {}
}
```

---

## 4. WorkQueue Contract

`state.json.pending_orders` 不足以承擔 durable queue。至少需要：

```text
enqueue(job)
lease(job_id, worker_id, ttl)
ack(job_id)
retry_after(job_id, timestamp, reason)
dead_letter(job_id, reason)
```

Required fields:
- `job_id`
- `job_type`
- `idempotency_key`
- `status`
- `attempt_count`
- `leased_by`
- `lease_expires_at`
- `next_retry_at`
- `last_error`

---

## 5. Idempotency Rules

### Post-level
- `post_id + content_hash` determines whether a post is new, edited, or duplicate.
- Edited old posts require explicit replay/review policy.

### Instruction-level
- Each parsed instruction gets a stable `instruction_id` and `idempotency_key`.
- Parser replay may update confidence/reasoning, but must not create a second executable instruction for the same semantic trade.

### Execution-level
- `place_order` must be guarded by unique `execution_id` / `idempotency_key`.
- If broker supports client order id, use it.
- If `place_order` times out, state becomes `ORDER_UNKNOWN`; next action is `get_order_status` / reconcile, not another `place_order`.

---

## 6. Concurrency Rules

MVP default:
- single account
- single worker
- US equities only
- buy/sell only

Locks:
- account-level lock for portfolio sync / reconcile
- symbol-level lock for execution
- execution-level lock for broker attempts

Rules:
- Same account + symbol with open order → pause new order or require review.
- Multiple instructions in same post execute in deterministic order.
- One failed instruction should not silently block the rest; each receives its own terminal state.

---

## 7. Tests to Write First

- Crash after post save before queue enqueue.
- Crash after queue enqueue before parse.
- Parser replay produces same instruction keys.
- Same post replay twice results in one execution intent.
- `place_order` timeout enters `ORDER_UNKNOWN`, then checks broker status.
- Reconcile mismatch blocks all execution.
- TA timeout enters `NEEDS_REVIEW`, not auto order.
- Prod + auto confirmation hard fails.
