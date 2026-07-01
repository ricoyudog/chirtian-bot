## ADDED Requirements

### Requirement: Daemon polls at 60-second intervals

The system SHALL execute `poll_once()` every 60 seconds when the daemon is running.

#### Scenario: Normal tick with no new posts
- **WHEN** `poll_once()` returns an empty signal list
- **THEN** the daemon SHALL write a heartbeat and proceed to the next tick without error

#### Scenario: Normal tick with new signals
- **WHEN** `poll_once()` returns one or more detected signals
- **THEN** the daemon SHALL invoke the pipeline for each signal, record the run via `RunRecorder`, and write a heartbeat

### Requirement: Daemon prevents concurrent instances via reentrancy lock

The system SHALL use a file-based lock (`runtime/daemon.lock`) to prevent multiple daemon instances from running simultaneously.

#### Scenario: Second daemon attempts to start
- **WHEN** a second daemon process is launched while one is already running
- **THEN** the second process SHALL exit immediately with a clear error message indicating the lock is held

#### Scenario: Lock is released on clean shutdown
- **WHEN** the daemon receives SIGTERM and completes its current tick
- **THEN** the lock file SHALL be released before the process exits

### Requirement: Daemon writes heartbeat for health monitoring

The system SHALL write `runtime/daemon_heartbeat.json` on every tick containing `{"last_tick": "ISO8601", "pid": int, "status": "ok"}`.

#### Scenario: Healthy daemon
- **WHEN** the daemon completes a tick successfully
- **THEN** `daemon_heartbeat.json` SHALL be updated with the current timestamp

#### Scenario: Heartbeat staleness is detectible
- **WHEN** the `daemon_heartbeat.json` `last_tick` is more than 120 seconds old
- **THEN** any health-checking component (Docker healthcheck, dashboard `/api/health`) SHALL report the daemon as stale

### Requirement: Daemon implements circuit breaker for consecutive failures

The system SHALL count consecutive tick failures and trigger a circuit break at N=5.

#### Scenario: Five consecutive tick failures
- **WHEN** the daemon experiences 5 consecutive poll or pipeline failures
- **THEN** the daemon SHALL write `runtime/kill_switch.flag`, send a Telegram alert, and exit

#### Scenario: Successful tick resets counter
- **WHEN** the daemon has 4 consecutive failures followed by a successful tick
- **THEN** the `consecutive_failures` counter SHALL reset to 0

### Requirement: Daemon supports graceful shutdown with tick-abort

The system SHALL respond to SIGTERM by setting a `threading.Event` that pipeline stages check, and SHALL abort long-running stages gracefully.

#### Scenario: SIGTERM during TA analysis
- **WHEN** the daemon receives SIGTERM while a TA subprocess is running
- **THEN** the daemon SHALL send SIGTERM to the TA subprocess, record the instruction as `TA_UNAVAILABLE` (not an error), write the run record with `reason: "SIGTERM_ABORT"`, release the lock, and exit

#### Scenario: Total shutdown time
- **WHEN** the daemon receives SIGTERM
- **THEN** the total time from signal to exit SHALL be ≤ 15 seconds

### Requirement: Daemon reads kill switch flag on startup

The system SHALL check for `runtime/kill_switch.flag` at startup and refuse to run if present.

#### Scenario: Kill switch flag exists at startup
- **WHEN** the daemon starts and `runtime/kill_switch.flag` exists
- **THEN** the daemon SHALL log the reason, invoke `RuntimeGuard.activate_stop()`, and exit without processing any ticks

### Requirement: TA analysis runs in parallel for multiple symbols

The system SHALL execute TA analysis for multiple instructions concurrently using `ThreadPoolExecutor`.

#### Scenario: One post with three symbols
- **WHEN** a Christian post contains three executable instructions (NVDA, AMD, MSFT)
- **THEN** all three TA analyses SHALL be submitted concurrently, and the total TA phase SHALL take approximately the duration of the slowest single analysis

#### Scenario: Sizing and ordering remain serial
- **WHEN** TA analyses for multiple symbols complete
- **THEN** the sizing and order placement for each symbol SHALL execute sequentially to preserve portfolio snapshot consistency
