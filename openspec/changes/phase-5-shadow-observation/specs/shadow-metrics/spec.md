## ADDED Requirements

### Requirement: Metrics collector records per-stage latency and outcome

The system SHALL provide a `MetricsCollector` that records latency and outcome for each pipeline stage: detection, parse, LLM call, TA confirmation, sizing, execution gate, and broker order.

#### Scenario: Successful pipeline execution with metrics captured
- **WHEN** a signal is processed through the full pipeline
- **THEN** the collector SHALL record timestamps at each stage entry/exit, computing per-stage latency in milliseconds, and the overall end-to-end latency

#### Scenario: Pipeline stage fails or times out
- **WHEN** a pipeline stage fails or exceeds its timeout threshold
- **THEN** the collector SHALL record the failure with stage name, error type, and elapsed time before failure

---

### Requirement: Stale signal rate is tracked with 5% threshold

The system SHALL compute stale signal rate and flag when it exceeds the 5% threshold. Stale signals are those where pipeline delay (not market closure) caused the signal to miss its valid execution window.

#### Scenario: Pipeline delay causes stale signal
- **WHEN** total pipeline latency causes the execution price to deviate beyond the expected range from the signal price
- **THEN** the collector SHALL classify the signal as stale and increment the stale signal counter

#### Scenario: Stale rate exceeds threshold
- **WHEN** stale signal count / total signal count > 0.05
- **THEN** the collector SHALL emit a warning in the observation summary flagging the stale rate

---

### Requirement: Aggregate metrics report at observation period end

The system SHALL produce an aggregated metrics report when the observation period completes.

#### Scenario: Report includes all required observation metrics
- **WHEN** the observation period ends
- **THEN** the report SHALL include: detection latency (p50/p95/max), parse latency (p50/p95/max), Claude CLI latency and error rate, TA latency and unavailable rate, same-day completion rate, stale signal rate, NEEDS_REVIEW rate, skip/reject/modify reasons breakdown, duplicate prevented count, and reconcile mismatch count

#### Scenario: Metrics are persisted to audit ledger
- **WHEN** any metric is recorded
- **THEN** it SHALL be written to the existing `AuditLedger` with a distinct `event_type` prefix `shadow_metric.` so it is queryable alongside other audit events
