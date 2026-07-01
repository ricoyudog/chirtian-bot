## ADDED Requirements

### Requirement: RunRecorder generates a unique run_id for each pipeline execution

The system SHALL generate a unique, human-readable `run_id` for every pipeline execution in the format `{YYYY-MM-DD}-{seq}-{uuid[:8]}`.

#### Scenario: First run of the day
- **WHEN** the daemon starts a new pipeline execution at 2026-07-05 14:30 UTC
- **THEN** `RunRecorder` SHALL generate a run_id like `2026-07-05-001-a1b2c3d4` with seq=001

#### Scenario: Subsequent runs in same day
- **WHEN** a second pipeline execution starts on the same calendar date
- **THEN** the `run_id` SHALL increment seq to 002 while preserving the same date prefix

### Requirement: RunRecorder persists structured run records as append-only JSONL

The system SHALL write each run record to `runtime/runs.jsonl` as an append-only JSONL line.

#### Scenario: Successful pipeline run
- **WHEN** a pipeline execution completes all stages without errors
- **THEN** the run record SHALL contain: `run_id`, `started_at`, `ended_at`, `mode`, `environment`, `signals_processed`, `instructions` (array with per-instruction outcomes and `stage_timings`), `errors` (empty array), `outcome: "success"`

#### Scenario: Pipeline run with errors
- **WHEN** a pipeline execution encounters exceptions during processing
- **THEN** the run record SHALL contain: `outcome: "error"` and `errors` array with error summaries including `stage` and `message`

#### Scenario: Pipeline run aborted by SIGTERM
- **WHEN** a pipeline execution is interrupted by SIGTERM via tick-abort
- **THEN** the run record SHALL contain: `outcome: "aborted"` and `reason: "SIGTERM_ABORT"`

### Requirement: RunRecorder captures per-stage timing breakdown

The system SHALL record per-stage latency in `stage_timings` for each instruction processed.

#### Scenario: Multi-stage pipeline execution
- **WHEN** an instruction goes through detect → parse → llm → ta → sizing → exec → broker stages
- **THEN** `stage_timings` SHALL include `started_at` and `duration_ms` for each completed stage, and a `skipped` flag for stages that were bypassed
