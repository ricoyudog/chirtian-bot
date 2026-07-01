## ADDED Requirements

### Requirement: Rollback drill covers order cancellation scenario

The system SHALL provide a rollback drill that cancels a placed paper order and verifies portfolio ledger consistency.

#### Scenario: Cancel a paper order
- **WHEN** the operator initiates the order rollback drill
- **THEN** the drill SHALL place a paper order, call `cancel_order()`, verify cancellation, write an `AuditEvent(type="ORDER_CANCELLED", reason="rollback_drill")`, and confirm `portfolio_ledger.jsonl` is consistent

### Requirement: Rollback drill covers config rollback scenario

The system SHALL provide a rollback drill that reverts `config.yaml` to a known-good state and restarts the daemon.

#### Scenario: Config rollback
- **WHEN** the operator initiates the config rollback drill
- **THEN** the drill SHALL backup current config, replace it with a known-good version, restart the daemon, and verify the daemon healthcheck passes

### Requirement: Rollback drill covers Docker rollback scenario

The system SHALL provide a rollback drill that performs `docker compose down && docker compose up` while preserving the `runtime/` volume.

#### Scenario: Docker compose rollback
- **WHEN** the operator initiates the Docker rollback drill
- **THEN** the drill SHALL execute `docker compose down`, verify `runtime/` volume is retained, execute `docker compose up`, and confirm all three services are healthy with run history preserved

### Requirement: All drill results are persisted to runtime/incidents/

The system SHALL write every rollback drill result as a dated markdown file in `runtime/incidents/`.

#### Scenario: Drill completes
- **WHEN** any rollback drill scenario completes
- **THEN** a file SHALL be written to `runtime/incidents/<date>-rollback-<scenario>.md` containing start time, end time, scenario description, result (PASS/FAIL), and any failure details
