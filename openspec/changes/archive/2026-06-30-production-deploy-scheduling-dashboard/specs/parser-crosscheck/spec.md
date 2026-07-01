## ADDED Requirements

### Requirement: CrossCheckParser runs three parallel extractions

The system SHALL invoke three independent DeepSeek V4 Flash instances concurrently via `ThreadPoolExecutor` for each Christian post.

#### Scenario: Single post extraction
- **WHEN** a Christian post text is submitted to `CrossCheckParser.parse()`
- **THEN** three separate subprocess calls to DeepSeek V4 Flash SHALL be launched concurrently, and the total latency SHALL approximate the slowest single call

#### Scenario: One model call times out
- **WHEN** one of the three DeepSeek Flash calls exceeds the timeout
- **THEN** that model's result SHALL be excluded from voting, and the cross-check SHALL proceed with the remaining two models

### Requirement: CrossCheckParser uses 2/3 majority voting

The system SHALL accept a parsing result only when at least 2 of 3 models agree on symbol and action.

#### Scenario: Two models agree on NVDA BUY
- **WHEN** Model A returns `{symbol: "NVDA", action: "BUY"}`, Model B returns `{symbol: "NVDA", action: "BUY"}`, Model C returns `{symbol: "NVDA", action: "BUY"}`
- **THEN** the cross-check SHALL return `ParseResult(status="EXECUTABLE", instructions=[{symbol: "NVDA", action: "BUY"}])`

#### Scenario: Two models disagree on symbol
- **WHEN** Model A returns `{symbol: "NVDA"}`, Model B returns `{symbol: "NVDA"}`, Model C returns `{symbol: "AMD"}`
- **THEN** the cross-check SHALL accept the majority (NVDA) and discard Model C's result

#### Scenario: All three models disagree
- **WHEN** all three models return different symbols
- **THEN** the cross-check SHALL return `ParseResult(status="NEEDS_REVIEW", reason_codes=["CROSSCHECK_NO_CONSENSUS"])` and SHALL trigger a Telegram alert to the operator

### Requirement: CrossCheckParser records voting trail

The system SHALL write each model's raw output and the final decision to `runtime/parser_votes.jsonl`.

#### Scenario: Any cross-check execution
- **WHEN** the `CrossCheckParser` completes a parse
- **THEN** one JSONL line SHALL be appended containing: `run_id`, `post_id`, `model_votes` (array of three entries with model_id, symbol, action, quantity, confidence), `final_decision` (accepted result or NEEDS_REVIEW), and `strategy` ("majority_2of3" or "no_consensus")

### Requirement: Existing InstructionParser is preserved as manual path

The system SHALL keep `InstructionParser` (Claude/GLM-5.2) unchanged for manual `cmd_parse` operations.

#### Scenario: Operator uses cmd_parse
- **WHEN** the operator runs `python -m src.pipeline run --mode parse`
- **THEN** `InstructionParser` SHALL be used (Claude CLI subprocess), NOT `CrossCheckParser`

#### Scenario: Daemon uses cross-check
- **WHEN** the daemon processes a polled post
- **THEN** `CrossCheckParser` SHALL be used (3 × DeepSeek V4 Flash), NOT `InstructionParser`

### Requirement: CrossCheckParser output is compatible with existing pipeline

The system SHALL ensure that `CrossCheckParser` produces a `ParseResult` identical in structure to `InstructionParser`, so downstream stages (orchestrator, TA fusion, sizing) require no changes.

#### Scenario: Pipeline receives cross-check result
- **WHEN** the daemon passes a `ParseResult` from `CrossCheckParser` to `TradingPipeline.process_parse_result()`
- **THEN** the orchestrator SHALL process it identically to a result from `InstructionParser`
