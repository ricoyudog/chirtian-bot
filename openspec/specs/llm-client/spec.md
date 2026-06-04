## ADDED Requirements

### Requirement: LLMClient protocol defines async-safe JSON completion interface

The system SHALL define an `LLMClient` protocol with a `complete_json` method that accepts a prompt string, a JSON schema dict, and a timeout in seconds, and returns a validated dict.

#### Scenario: Successful JSON completion
- **WHEN** `complete_json` is called with a valid prompt and schema
- **THEN** the method SHALL return a dict that conforms to the provided JSON schema

#### Scenario: Timeout during LLM call
- **WHEN** the LLM call exceeds the specified timeout seconds
- **THEN** the method SHALL raise `LLMTimeoutError` with the timeout value and elapsed time

#### Scenario: LLM returns invalid JSON
- **WHEN** the LLM subprocess returns output that is not valid JSON
- **THEN** the method SHALL raise `LLMOutputError` with the raw output captured

#### Scenario: LLM returns JSON that fails schema validation
- **WHEN** the LLM returns valid JSON but it does not conform to the provided schema
- **THEN** the method SHALL raise `LLMSchemaError` with validation error details

---

### Requirement: ClaudeCliClient wraps Claude CLI subprocess

The system SHALL implement `ClaudeCliClient` that calls `claude -p --bare --output-format json` via `subprocess.run` with `--max-budget-usd` and `--tools ""` flags.

#### Scenario: Claude CLI invocation with correct flags
- **WHEN** `complete_json` is called
- **THEN** the subprocess SHALL be invoked with flags `--bare --output-format json --tools "" --max-budget-usd 0.05`

#### Scenario: Claude CLI not found in PATH
- **WHEN** `claude` binary is not available in PATH
- **THEN** the method SHALL raise `LLMUnavailableError`

#### Scenario: Claude CLI returns non-zero exit code
- **WHEN** the subprocess exits with a non-zero return code
- **THEN** the method SHALL raise `LLMOutputError` with stderr captured

#### Scenario: Stderr captured for audit
- **WHEN** any LLM call completes (success or failure)
- **THEN** stderr output SHALL be captured and available for audit logging, with no secrets in the output

---

### Requirement: All LLM failures fail closed to NEEDS_REVIEW

The system SHALL ensure that every failure mode of the LLM client (timeout, unavailable, invalid output, schema mismatch) results in a `NEEDS_REVIEW` status at the parser level. No failure SHALL produce an auto-approved executable instruction.

#### Scenario: Any LLM error during parsing
- **WHEN** any exception is raised by the LLMClient during a parse call
- **THEN** the parser SHALL return a `ParseResult` with `status: "NEEDS_REVIEW"` and a reason code indicating the failure type

#### Scenario: No auto-approval on failure
- **WHEN** the LLM client fails for any reason
- **THEN** the parser SHALL NOT produce any `ParsedInstruction` with `status: "EXECUTABLE"`
