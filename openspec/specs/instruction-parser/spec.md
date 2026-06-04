## ADDED Requirements

### Requirement: Parser produces structured ParseResult from post text

The system SHALL implement an `InstructionParser` that accepts post text and a post_id, and returns a `ParseResult` containing a status classification, a list of `ParsedInstruction` objects, reason codes, and the raw text.

#### Scenario: Clear buy instruction
- **WHEN** parser receives post text "今天加倉 nvda 1%"
- **THEN** it SHALL return `ParseResult` with `status: "EXECUTABLE"` and one `ParsedInstruction` with `action: "BUY"`, `symbol: "NVDA"`, `quantity_pct: 1.0`, `quantity_type: "pct"`

#### Scenario: Clear sell all instruction
- **WHEN** parser receives post text "賣出全部 etsy"
- **THEN** it SHALL return `ParseResult` with `status: "EXECUTABLE"` and one `ParsedInstruction` with `action: "SELL"`, `symbol: "ETSY"`, `quantity_type: "all"`, `quantity_pct: null`

#### Scenario: No-op post
- **WHEN** parser receives post text "今天沒有操作"
- **THEN** it SHALL return `ParseResult` with `status: "SKIP_NOT_ACTIONABLE"`, empty instructions, and reason code `"NO_ACTION"`

#### Scenario: Future intent
- **WHEN** parser receives post text containing "準備下週找機會做空泡泡瑪特"
- **THEN** it SHALL return `ParseResult` with `status: "SKIP_NOT_ACTIONABLE"` and reason code `"FUTURE_INTENT"`

#### Scenario: Conditional sentence
- **WHEN** parser receives post text containing "如果明天還保持弱勢，會考慮削減nvdl"
- **THEN** it SHALL return `ParseResult` with `status: "SKIP_NOT_ACTIONABLE"` and reason code `"CONDITIONAL"`

#### Scenario: Historical summary
- **WHEN** parser receives a monthly/weekly summary post
- **THEN** it SHALL return `ParseResult` with `status: "SKIP_NOT_ACTIONABLE"` and reason code `"HISTORICAL_SUMMARY"`

#### Scenario: Mixed summary with forward-looking intent
- **WHEN** parser receives a post mixing historical actions, forward plans, and conditional triggers
- **THEN** it SHALL return `ParseResult` with `status: "SKIP_NOT_ACTIONABLE"` with multiple reason codes including `"HISTORICAL_SUMMARY"`, `"FUTURE_INTENT"`, or `"CONDITIONAL"`

#### Scenario: Ambiguous low-confidence text
- **WHEN** parser cannot determine whether text is an executable instruction
- **THEN** it SHALL return `ParseResult` with `status: "NEEDS_REVIEW"` and reason code `"LOW_CONFIDENCE"`

---

### Requirement: ParsedInstruction contains stable deterministic identifiers

Every `ParsedInstruction` SHALL contain an `instruction_id` and `idempotency_key` that are deterministic and stable across replays of the same input.

#### Scenario: instruction_id generation
- **WHEN** a ParsedInstruction is created for post_id "substack:20260601:test" with sequence 0
- **THEN** `instruction_id` SHALL be `"instr:substack:20260601:test:0"`

#### Scenario: instruction_id stability on replay
- **WHEN** the same post text and post_id are parsed twice
- **THEN** both parses SHALL produce identical `instruction_id` values for corresponding instructions

#### Scenario: idempotency_key uses Phase 1 algorithm
- **WHEN** a ParsedInstruction is created
- **THEN** `idempotency_key` SHALL be generated using `generate_idempotency_key(post_id, sequence, action, symbol, quantity_pct)` from Phase 1

#### Scenario: idempotency_key stability on replay
- **WHEN** the same post text and post_id are parsed twice
- **THEN** both parses SHALL produce identical `idempotency_key` values for corresponding instructions

---

### Requirement: Multi-instruction posts produce ordered instructions

When a post contains multiple trading instructions, the parser SHALL produce instructions in left-to-right textual order with 0-indexed sequence numbers.

#### Scenario: Inline multi-instruction
- **WHEN** parser receives "加倉aaoi 1%，加倉u 2%，加倉sofi 2%"
- **THEN** it SHALL produce 3 instructions with sequence 0 (AAOI 1%), sequence 1 (U 2%), sequence 2 (SOFI 2%)

#### Scenario: Numbered list multi-instruction
- **WHEN** parser receives numbered list "1. 加倉smci 1%\n2. 加倉nbis 1%"
- **THEN** it SHALL produce 2 instructions with sequence 0 (SMCI 1%), sequence 1 (NBIS 1%)

#### Scenario: Shared-quantity multi-instruction
- **WHEN** parser receives "買入ionq，rgti，qbts各1%"
- **THEN** it SHALL produce 3 instructions each with quantity_pct 1.0, in textual order: IONQ (seq 0), RGTI (seq 1), QBTS (seq 2)

---

### Requirement: Parser handles option instructions

The parser SHALL recognize and parse option trading instructions into structured ParsedInstructions with option-specific fields. Option instructions are `EXECUTABLE` at the parser level but SHALL NOT be forwarded to the executor in MVP.

#### Scenario: Long call option
- **WHEN** parser receives "買入1% crwv call（26年7月17日到期，strike 150）"
- **THEN** it SHALL return a ParsedInstruction with `action: "option_place"`, `symbol: "CRWV"`, `option_type: "call"`, `option_side: "long"`, `strike: 150.0`, `expiry: "2026-07-17"`, `quantity_pct: 1.0`

#### Scenario: Short call option
- **WHEN** parser receives "開始short 特斯拉 call，到期日7月18日，strike 380"
- **THEN** it SHALL return a ParsedInstruction with `action: "option_place"`, `option_type: "call"`, `option_side: "short"`, `strike: 380.0`

#### Scenario: Short put option
- **WHEN** parser receives "開始short 英偉達put，到期日2025年5月16日，strike 100（short put是做多）"
- **THEN** it SHALL return a ParsedInstruction with `action: "option_place"`, `option_type: "put"`, `option_side: "short"`, `strike: 100.0`

#### Scenario: Long put option with ticker format
- **WHEN** parser receives "買入0.3%的EWY 260417 120P"
- **THEN** it SHALL return a ParsedInstruction with `action: "option_place"`, `symbol: "EWY"`, `option_type: "put"`, `option_side: "long"`, `strike: 120.0`, `expiry: "2026-04-17"`

---

### Requirement: quantity_type distinguishes percentage from all-position

The parser SHALL output a `quantity_type` field on every ParsedInstruction: `"pct"` for percentage-based instructions and `"all"` for full-position instructions.

#### Scenario: Percentage-based quantity
- **WHEN** parser receives "加倉 nvda 1%"
- **THEN** `quantity_type` SHALL be `"pct"` and `quantity_pct` SHALL be `1.0`

#### Scenario: Sell all position
- **WHEN** parser receives "賣出全部 etsy"
- **THEN** `quantity_type` SHALL be `"all"` and `quantity_pct` SHALL be `null`

#### Scenario: Sell all with historical percentage annotation
- **WHEN** parser receives "賣出全部 smci（4.3%）"
- **THEN** `quantity_type` SHALL be `"all"` and `quantity_pct` SHALL be `null` (bracketed percentage is informational, not an instruction)

#### Scenario: Cover short all
- **WHEN** parser receives "cover short 全部 htz"
- **THEN** `quantity_type` SHALL be `"all"` and `quantity_pct` SHALL be `null`

---

### Requirement: Parser uses classification routing not confidence threshold

The parser SHALL use LLM-output status classification (`EXECUTABLE`, `SKIP_NOT_ACTIONABLE`, `NEEDS_REVIEW`) for routing decisions. Confidence values SHALL be recorded in audit logs only and SHALL NOT be used as routing thresholds.

#### Scenario: Classification drives routing
- **WHEN** LLM returns a classification of `"NEEDS_REVIEW"`
- **THEN** the ParseResult status SHALL be `"NEEDS_REVIEW"` regardless of the confidence value

#### Scenario: Confidence recorded in audit
- **WHEN** any parse completes
- **THEN** the confidence value from LLM output SHALL be included in the audit event but not used for routing

---

### Requirement: Parser writes audit events for every parse decision

Every parse call SHALL write an audit event to the AuditLedger containing the post_id, parse status, reason codes, confidence, raw text span, and instruction count.

#### Scenario: Successful parse audit
- **WHEN** a parse produces EXECUTABLE instructions
- **THEN** an audit event SHALL be written with event_type `"instructions_parsed"`, status, all reason codes, confidence, parse_span, and instruction count

#### Scenario: Failed parse audit
- **WHEN** a parse results in NEEDS_REVIEW or SKIP_NOT_ACTIONABLE
- **THEN** an audit event SHALL be written with event_type `"parse_completed"`, status, and all reason codes

#### Scenario: LLM failure audit
- **WHEN** the LLM client raises an exception
- **THEN** an audit event SHALL be written with event_type `"parse_error"`, status `"NEEDS_REVIEW"`, and the error reason
