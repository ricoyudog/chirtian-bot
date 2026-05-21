---
type: wiki
created: 2026-05-20
updated: 2026-05-20
tags: [operations, runbook, trading, auto-trading]
status: draft
---

# Auto Trading Operations Runbook

> 從 [[wiki/architecture/auto-trading-pipeline-High-level|auto-trading-pipeline]] 拆出的運維、事故、上線與回滾手冊草稿。MVP 預設 UAT-only；prod 需另過 go-live gate。

## 1. Operating Modes

| Mode | Description | Mutating Orders |
|---|---|---|
| `offline_replay` | historical replay / parser tests | no |
| `shadow` | live poll + parse + decision, no broker order | no |
| `uat_confirm` | UAT preview/place, every order manually confirmed | yes, UAT only |
| `prod_confirm` | prod with manual confirmation | later only |
| `prod_auto` | prod auto execution | out of MVP |

MVP allowed mode: `uat_confirm` only.

---

## 2. Startup Checklist

Before daemon starts:
- Confirm mode is `uat_confirm` or safer.
- Confirm Webull environment is UAT.
- Confirm account id allowlist matches broker account.
- Confirm region matches config.
- Confirm Substack auth works.
- Confirm Claude/LLM parser credentials work.
- Confirm TradingAgents credentials work if TA gate enabled.
- Confirm `state store` and `ledger` are writable.
- Run portfolio sync.
- Run reconcile.
- If reconcile fails, do not start execution worker.

---

## 3. Normal Operation

For each new post:
1. Save post.
2. Enqueue parse job.
3. Parse instructions.
4. Enqueue analysis job.
5. TradingAgents returns green/yellow/red/unavailable.
6. Green only proceeds to sizing.
7. Sync/reconcile account.
8. Size order.
9. Ask for manual confirmation.
10. Preview order.
11. Place UAT order.
12. Record broker response.
13. Poll status / reconcile fills.

---

## 4. Manual Review Policy

Manual review required when:
- parser confidence low
- TA yellow/red/unavailable
- stale signal
- sizing modified/clipped materially
- reconcile mismatch
- broker order unknown
- duplicate risk
- open order conflict
- prod mode requested

Default timeout:
- If user does not confirm within configured window, order becomes `EXPIRED_REVIEW` and is not placed.

All overrides must record:
- operator
- timestamp
- original recommendation
- changed fields
- reason

---

## 5. Incident Severity

| Severity | Examples | Action |
|---|---|---|
| SEV0 | duplicate real order, unexpected fill, prod guard bypass | kill switch, stop daemon, reconcile, postmortem |
| SEV1 | broker unknown order, reconcile mismatch, repeated rejects | pause execution, investigate |
| SEV2 | TA outage, parser degraded, stale quote | route to review / no trade |
| SEV3 | notification failure, dashboard lag | fix during normal ops |

---

## 6. Kill Switch Procedure

When triggered:
1. Stop execution worker.
2. Keep poller optional, but no new orders.
3. Cancel pending local execution jobs or mark `PAUSED_BY_KILL_SWITCH`.
4. Query broker open orders.
5. Reconcile positions and cash.
6. Write incident note.
7. Resume only after explicit clean reconcile and owner approval.

Kill switch triggers:
- reconcile mismatch
- unexpected fill
- duplicate order
- broker ack unknown unresolved
- account/region mismatch
- quote/data outage
- TA unavailable if TA gate is required
- prod unsafe config

---

## 7. Rollback Procedure

Rollback means stop new orders and return to a known safe state.

Steps:
1. Disable execution mode.
2. Drain or pause queue.
3. Snapshot ledger/state.
4. Query Webull account, positions, open orders.
5. Cancel unintended open orders if appropriate.
6. Rebuild local snapshot from broker source of truth.
7. Mark unresolved jobs as `DEAD_LETTER` or `NEEDS_REVIEW`.
8. Restart in `shadow` mode before returning to UAT.

---

## 8. Go / No-Go Checklist

### Before UAT
- Parser gold set passes.
- Durable queue works.
- Idempotency tests pass.
- Environment guard tests pass.
- Webull preview/place/cancel/status tested in UAT.
- Reconcile mismatch blocks execution.
- TA timeout does not auto order.
- Manual confirmation timeout works.

### Before Prod Later
- Shadow run completed.
- Kill switch drill completed.
- Rollback drill completed.
- Small live capital plan approved.
- Risk limits approved.
- Alert channel tested.
- Incident owner defined.

---

## 9. Post-Incident Template

```markdown
# Incident: <title>

- Time detected:
- Mode:
- Account/environment:
- Trigger:
- Orders affected:
- Positions affected:
- Root cause:
- Immediate action:
- Reconcile result:
- Data/ledger corrections:
- Prevention:
- Resume approval:
```
