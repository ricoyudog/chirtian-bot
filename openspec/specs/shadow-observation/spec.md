## ADDED Requirements

### Requirement: Shadow observation runner executes full pipeline in paper trading mode

The system SHALL provide a `ShadowObservationRunner` that orchestrates the full pipeline (detection → parse → sizing → execution gate → broker) using the existing Webull paper trading account. The runner SHALL respect the observation period constraints defined in the Phase 5 decision document.

#### Scenario: Observation period active with signal received
- **WHEN** the runner detects a new signal during an active observation period
- **THEN** it SHALL execute the full pipeline using `environment: uat` and `mode: shadow`, recording the result and metrics

#### Scenario: Observation period minimum duration not met
- **WHEN** 7 calendar days have passed but fewer than 10 signals have been processed
- **THEN** the runner SHALL auto-extend the observation period until at least 10 signals are processed, up to a maximum of 4 weeks

#### Scenario: Observation period maximum duration reached with insufficient signals
- **WHEN** 4 weeks have passed and fewer than 10 signals have been processed
- **THEN** the runner SHALL stop and produce a summary noting insufficient signal count for evaluation, flagging the signal source for review

#### Scenario: Observation period complete
- **WHEN** at least 7 calendar days AND at least 10 signals have been processed
- **THEN** the runner SHALL mark the observation period as complete and generate a shadow run summary

---

### Requirement: Shadow run summary is persisted as a dated note

The system SHALL produce a shadow run summary as a dated note file when the observation period completes.

#### Scenario: Summary generated after observation period
- **WHEN** the observation period completes
- **THEN** the runner SHALL write a summary file to `runtime/shadow_summaries/` with filename format `YYYY-MM-DD-shadow-run-summary.md` containing observation period dates, signal count, and aggregated metrics

#### Scenario: Summary includes go/no-go readiness assessment
- **WHEN** the shadow run summary is generated
- **THEN** it SHALL include a checklist of all go/no-go criteria from the decision document with pass/fail status for each item

---

### Requirement: Weekend signals are classified as deferred not stale

The system SHALL classify signals received during market closure (weekends, US market holidays) as deferred, not stale.

#### Scenario: Signal received on Saturday
- **WHEN** a signal is detected on a Saturday
- **THEN** the runner SHALL classify it as `DEFERRED` and schedule execution for the next trading day's pre-market

#### Scenario: Deferred signal executed on next trading day
- **WHEN** a deferred signal's scheduled execution time arrives
- **THEN** the runner SHALL execute the pipeline and record the deferral delay separately from pipeline latency

---

### Requirement: Observation period state is durable across restarts

The system SHALL persist observation period state so that progress is not lost on restart.

#### Scenario: Runner restarts mid-observation
- **WHEN** the runner process restarts during an active observation period
- **THEN** it SHALL resume from the persisted state, retaining start date, signal count, and all collected metrics
