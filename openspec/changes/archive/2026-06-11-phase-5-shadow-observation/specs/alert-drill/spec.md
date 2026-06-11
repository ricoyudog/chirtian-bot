## ADDED Requirements

### Requirement: Alert drill executes end-to-end kill switch simulation

The system SHALL provide an `AlertDrillRunner` that simulates a full kill switch scenario: detect anomaly → trigger kill switch → deliver alert → operator confirms receipt.

#### Scenario: Full drill completes successfully
- **WHEN** the operator initiates an alert drill
- **THEN** the drill runner SHALL simulate an anomaly event, invoke the kill switch, send an alert through the configured channel, and wait for operator confirmation, recording the total drill duration

#### Scenario: Alert delivery fails
- **WHEN** the alert channel fails to deliver within a configurable timeout
- **THEN** the drill SHALL be marked as FAILED with the failure reason, and the result SHALL be written to `runtime/incidents/` as a dated drill note

#### Scenario: Operator does not confirm within timeout
- **WHEN** the operator does not confirm alert receipt within the drill timeout
- **THEN** the drill SHALL be marked as FAILED with reason `"OPERATOR_NO_RESPONSE"`, and the result SHALL be recorded

---

### Requirement: Drill results are persisted as dated incident notes

The system SHALL write drill results to `runtime/incidents/` as dated notes.

#### Scenario: Drill result note created
- **WHEN** a drill completes (success or failure)
- **THEN** a note SHALL be written to `runtime/incidents/YYYY-MM-DD-drill-<type>.md` with drill type, start/end time, result, and any failure details

---

### Requirement: Alert channel must pass drill before live capital

The system SHALL block live capital activation if no successful end-to-end alert drill has been recorded.

#### Scenario: No successful drill on record
- **WHEN** the go/no-go gate is evaluated and no successful alert drill result exists in `runtime/incidents/`
- **THEN** the gate SHALL return `NO_GO` with reason `"ALERT_CHANNEL_NOT_TESTED"`

#### Scenario: Successful drill exists
- **WHEN** the go/no-go gate is evaluated and at least one successful alert drill result exists
- **THEN** the alert channel criterion SHALL be marked as `PASS`
