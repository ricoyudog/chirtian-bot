## ADDED Requirements

### Requirement: Docker Compose defines three services

The system SHALL be deployed via `docker-compose.yml` with three services: `daemon`, `dashboard`, and `bot`.

#### Scenario: docker compose up
- **WHEN** `docker compose up -d` is executed
- **THEN** all three services SHALL start and reach healthy status within 30 seconds

#### Scenario: Services share runtime volume
- **WHEN** the daemon writes to `runtime/runs.jsonl`
- **THEN** the dashboard SHALL be able to read the same file via the shared `runtime/` named volume

### Requirement: Daemon service has stop_grace_period of 120 seconds

The system SHALL configure the daemon Docker service with `stop_grace_period: 120s`.

#### Scenario: docker compose down while daemon is running
- **WHEN** `docker compose down` is executed
- **THEN** Docker SHALL wait up to 120 seconds for the daemon to complete tick-abort and clean shutdown before sending SIGKILL

### Requirement: Daemon service restarts automatically on crash

The system SHALL configure the daemon Docker service with `restart: unless-stopped`.

#### Scenario: Daemon process killed
- **WHEN** the daemon process is forcefully killed (SIGKILL)
- **THEN** Docker SHALL restart the daemon container within 10 seconds and it SHALL pass healthcheck within 30 seconds

### Requirement: Docker healthchecks verify all services

The system SHALL define healthchecks for each service.

#### Scenario: Daemon healthcheck
- **WHEN** the daemon healthcheck runs
- **THEN** it SHALL verify that `daemon_heartbeat.json` age ≤ 120 seconds

#### Scenario: Dashboard healthcheck
- **WHEN** the dashboard healthcheck runs
- **THEN** it SHALL verify that `GET http://localhost:8000/api/health` returns HTTP 200

#### Scenario: Bot healthcheck
- **WHEN** the bot healthcheck runs
- **THEN** it SHALL verify the bot process is alive and Telegram API is reachable

### Requirement: Docker Compose test configuration validates deployment

The system SHALL provide `docker-compose.test.yml` using `mode: offline_replay` with stubbed dependencies.

#### Scenario: CI validation
- **WHEN** `docker compose -f docker-compose.test.yml up --abort-on-container-exit` runs
- **THEN** all services SHALL start, pass healthchecks, and the kill switch mechanism SHALL be verified end-to-end

### Requirement: Complete dependency documentation is provided

The system SHALL include `.env.example` and `SETUP.md` documenting all required environment variables and manual setup steps.

#### Scenario: New operator follows SETUP.md
- **WHEN** a new operator follows the instructions in `SETUP.md`
- **THEN** they SHALL be able to configure Substack session, Webull auth, Claude auth, DeepSeek API key, and Telegram bot token, and successfully run `docker compose up`

### Requirement: Substack storage-state.json is bind-mounted from host

The system SHALL mount `storage-state.json` from the host filesystem as a read-only bind mount in the daemon container.

#### Scenario: Cookie update without container restart
- **WHEN** the operator updates `storage-state.json` on the host
- **THEN** the daemon container SHALL use the updated file on the next Substack poll without requiring a container restart

### Requirement: Claude CLI is available in Docker container

The system SHALL include the `claude` CLI binary in the Docker image.

#### Scenario: Operator runs manual parse
- **WHEN** the operator executes `docker compose exec daemon python -m src.pipeline run`
- **THEN** Claude CLI SHALL be available for the `InstructionParser`

### Requirement: JSONL files rotate monthly with 13-month retention

The system SHALL rotate JSONL files monthly and purge files older than 13 months.

#### Scenario: Month boundary
- **WHEN** a new calendar month begins
- **THEN** the daemon SHALL start writing to `runs-YYYY-MM.jsonl` and archive previous months

#### Scenario: Startup cleanup
- **WHEN** the daemon starts
- **THEN** it SHALL delete any `runs-*.jsonl` files older than 13 months

### Requirement: SQLite databases use housekeeping for data retention

The system SHALL purge old rows from SQLite databases using SQL DELETE statements.

#### Scenario: Daily positions purge
- **WHEN** the daemon writes a new position snapshot
- **THEN** it SHALL execute `DELETE FROM position_snapshots WHERE tick_at < date('now', '-30 days')`

### Requirement: Docker services have memory limits

The system SHALL configure memory limits for Docker services.

#### Scenario: Daemon memory constrained
- **WHEN** the daemon process allocates memory
- **THEN** it SHALL be limited to 1GB by Docker's `mem_limit`

#### Scenario: Dashboard memory constrained
- **WHEN** the dashboard process allocates memory
- **THEN** it SHALL be limited to 256MB by Docker's `mem_limit`
