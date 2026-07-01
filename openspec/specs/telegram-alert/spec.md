## ADDED Requirements

### Requirement: Telegram bot sends failure alerts

The system SHALL send a Telegram message to the operator when any pipeline stage reports an error.

#### Scenario: Parser stage fails
- **WHEN** the parser throws `LLMTimeoutError` or `LLMOutputError`
- **THEN** the bot SHALL push a message containing the `run_id`, error summary, and affected stage

#### Scenario: Substack gateway returns 502
- **WHEN** the daemon circuit breaker triggers after 5 consecutive Substack polling failures
- **THEN** the bot SHALL push a message indicating circuit breaker activation and that `kill_switch.flag` has been written

### Requirement: Telegram bot accepts /stop command for kill switch

The system SHALL allow the operator to trigger a kill switch by sending `/stop` in the Telegram chat.

#### Scenario: Operator sends /stop
- **WHEN** the operator sends `/stop` to the bot
- **THEN** the bot SHALL write `runtime/kill_switch.flag` and reply with a confirmation message

#### Scenario: Kill switch takes effect within two ticks
- **WHEN** `kill_switch.flag` is written
- **THEN** the daemon SHALL detect the flag and invoke `RuntimeGuard.activate_stop()` within at most 2 tick cycles (≤ 120 seconds)

### Requirement: Telegram bot provides drill confirm_callback

The system SHALL use the Telegram bot as the `confirm_callback` for `AlertDrillRunner.run_drill()`, enabling operator-in-the-loop verification.

#### Scenario: Drill requests operator confirmation
- **WHEN** an alert drill runs with Telegram `confirm_callback` registered
- **THEN** the bot SHALL send a message asking the operator to confirm, and SHALL return the operator's confirmation timestamp to the drill runner

#### Scenario: Operator does not respond to drill
- **WHEN** the drill timeout expires without operator response
- **THEN** `confirm_callback` SHALL return `None` and the drill SHALL be marked FAILED

### Requirement: Telegram bot writes heartbeat for health monitoring

The system SHALL periodically write `runtime/bot_heartbeat.json` to enable dashboard health monitoring.

#### Scenario: Bot is alive
- **WHEN** the bot process is running and connected to Telegram API
- **THEN** `bot_heartbeat.json` SHALL be updated at least every 5 minutes

### Requirement: Parser cross-check 0/3 disagreement triggers Telegram alert

The system SHALL send a Telegram alert when all three DeepSeek V4 Flash models produce different parsing results.

#### Scenario: Three-way disagreement on symbol
- **WHEN** all three models return different symbols for the same post
- **THEN** the system SHALL set status to `NEEDS_REVIEW` and the bot SHALL push a message with the post excerpt and all three model outputs
