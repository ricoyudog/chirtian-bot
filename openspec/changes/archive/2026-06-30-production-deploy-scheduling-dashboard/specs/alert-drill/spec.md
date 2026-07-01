## MODIFIED Requirements

### Requirement: Alert drill executes end-to-end kill switch simulation

The system SHALL provide an `AlertDrillRunner` that simulates a full kill switch scenario: detect anomaly → trigger kill switch → deliver alert → operator confirms receipt. The `confirm_callback` parameter SHALL be required — `None` is not accepted.

#### Scenario: Full drill completes successfully
- **WHEN** the operator initiates an alert drill with a valid `confirm_callback` registered
- **THEN** the drill runner SHALL simulate an anomaly event, invoke the kill switch, send an alert through the configured channel, and wait for operator confirmation, recording the total drill duration

#### Scenario: No confirm_callback provided
- **WHEN** `run_drill()` is called with `confirm_callback=None`
- **THEN** the drill SHALL immediately return `DrillResult(result="FAILED", failure_reason="NO_CONFIRM_CALLBACK")` without executing any simulation steps

#### Scenario: Alert delivery fails
- **WHEN** the alert channel fails to deliver within a configurable timeout
- **THEN** the drill SHALL be marked as FAILED with the failure reason, and the result SHALL be written to `runtime/incidents/` as a dated drill note

#### Scenario: Operator does not confirm within timeout
- **WHEN** the operator does not confirm alert receipt within the drill timeout
- **THEN** the drill SHALL be marked as FAILED with reason `"OPERATOR_NO_RESPONSE"`, and the result SHALL be recorded
