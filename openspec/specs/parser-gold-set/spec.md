## ADDED Requirements

### Requirement: Gold set uses per-case YAML fixtures

The gold test set SHALL be stored as individual YAML files in `tests/gold_set/cases/`, one file per test case, with filenames following the pattern `NNN_category.yaml`.

#### Scenario: Case file structure
- **WHEN** a gold set case file is loaded
- **THEN** it SHALL contain fields: `case_id`, `category`, `post_id`, `raw_text`, `expected_status`, `expected_instructions` (list), `expected_reason_codes` (list)

#### Scenario: Executable case with expected instruction
- **WHEN** a case has `expected_status: "EXECUTABLE"`
- **THEN** `expected_instructions` SHALL contain at least one instruction with fields `sequence`, `action`, `symbol`, and optionally `quantity_pct`, `quantity_type`, `option_type`, `option_side`, `strike`, `expiry`, `confidence_min`

#### Scenario: Non-executable case with empty instructions
- **WHEN** a case has `expected_status: "SKIP_NOT_ACTIONABLE"` or `"NEEDS_REVIEW"`
- **THEN** `expected_instructions` SHALL be an empty list and `expected_reason_codes` SHALL be non-empty

---

### Requirement: Gold set covers 12 case types with minimum 40 cases

The gold test set SHALL cover all 12 case types: clear_buy, clear_sell, no_op, future_intent, conditional, summary, mixed_summary_forward, low_confidence_ambiguous, multi_instruction, option_buy, option_sell, option_cover.

#### Scenario: Case type coverage
- **WHEN** the gold set is validated
- **THEN** there SHALL be at least 1 case for each of the 12 categories

#### Scenario: Minimum case count
- **WHEN** the gold set is validated
- **THEN** there SHALL be at least 40 total cases across all categories

---

### Requirement: Layer 1 unit tests mock LLM and are deterministic

Layer 1 tests SHALL mock the LLMClient to return fixed JSON responses, testing only parser logic: ID generation, schema validation, status routing, reason codes, quantity_type handling, option fields, and multi-instruction sequencing. These tests SHALL run in CI and be 100% deterministic.

#### Scenario: Mock LLM returns fixed response
- **WHEN** a Layer 1 test runs
- **THEN** it SHALL use a mock LLMClient that returns a predetermined JSON response per case

#### Scenario: Instruction ID verification
- **WHEN** a Layer 1 test processes a case
- **THEN** it SHALL verify that generated `instruction_id` matches the expected `instr:{post_id}:{sequence}` format

#### Scenario: Idempotency key stability
- **WHEN** a Layer 1 test processes the same case twice
- **THEN** it SHALL verify that `idempotency_key` is identical both times

#### Scenario: Schema validation
- **WHEN** mock LLM returns invalid JSON or schema-mismatched data
- **THEN** Layer 1 test SHALL verify parser returns `status: "NEEDS_REVIEW"`

#### Scenario: No external dependency
- **WHEN** Layer 1 tests run
- **THEN** no external process (Claude CLI, network) SHALL be required

---

### Requirement: Layer 2 integration tests call real Claude CLI with tolerance

Layer 2 tests SHALL call the real Claude CLI via ClaudeCliClient with the same gold set cases, verifying classification and core fields with defined tolerances. These tests SHALL NOT run in CI and SHALL be used for model drift detection.

#### Scenario: Status classification must match exactly
- **WHEN** a Layer 2 test processes a case
- **THEN** the returned `status` SHALL exactly match the case's `expected_status`

#### Scenario: Action and symbol must match exactly
- **WHEN** a Layer 2 test processes an EXECUTABLE case
- **THEN** `action` and `symbol` SHALL exactly match expected values

#### Scenario: Quantity tolerance
- **WHEN** a Layer 2 test compares `quantity_pct`
- **THEN** the value SHALL be within ±0.1 of the expected value

#### Scenario: Reason codes superset allowed
- **WHEN** a Layer 2 test compares reason codes
- **THEN** the result SHALL contain all expected reason codes but MAY include additional codes

#### Scenario: Confidence logged but not verified
- **WHEN** a Layer 2 test runs
- **THEN** confidence SHALL be recorded in test output but SHALL NOT cause test failure

#### Scenario: Parse span logged but not verified
- **WHEN** a Layer 2 test runs
- **THEN** parse_span SHALL be recorded in test output but SHALL NOT cause test failure
