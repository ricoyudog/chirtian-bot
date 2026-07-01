## ADDED Requirements

### Requirement: Dashboard serves run history via API

The system SHALL expose `GET /api/runs` returning a paginated list of run records from `runtime/runs.jsonl`.

#### Scenario: Request run list
- **WHEN** the dashboard receives `GET /api/runs?limit=20`
- **THEN** it SHALL return the 20 most recent run records with `run_id`, `started_at`, `outcome`, `signals_processed`, and `orders_placed`

### Requirement: Dashboard serves single run details

The system SHALL expose `GET /api/runs/{run_id}` returning full run details cross-referenced with `audit_ledger.jsonl`.

#### Scenario: Request specific run
- **WHEN** the dashboard receives `GET /api/runs/2026-07-05-001-a1b2c3d4`
- **THEN** it SHALL return the complete run record including all instruction outcomes and stage timings

### Requirement: Dashboard serves per-stage latency metrics

The system SHALL expose `GET /api/metrics` returning p50/p95/max latencies per pipeline stage.

#### Scenario: Request metrics
- **WHEN** the dashboard receives `GET /api/metrics`
- **THEN** it SHALL return per-stage latency breakdown for detect, parse, llm, ta, sizing, exec, and broker stages

### Requirement: Dashboard serves safety status

The system SHALL expose `GET /api/safety` returning RuntimeGuard status, reconcile status, and kill switch state.

#### Scenario: System is healthy
- **WHEN** RuntimeGuard is not stopped and `kill_switch.flag` does not exist
- **THEN** `GET /api/safety` SHALL return `{"kill_switch_active": false, "guard_status": "ok"}`

#### Scenario: Kill switch is active
- **WHEN** `runtime/kill_switch.flag` exists
- **THEN** `GET /api/safety` SHALL return `{"kill_switch_active": true, "guard_status": "stopped"}`

### Requirement: Dashboard serves real-time events via SSE

The system SHALL expose `GET /api/events/tail` as a Server-Sent Events stream tailing new lines from `audit_ledger.jsonl`.

#### Scenario: New audit event occurs
- **WHEN** a new line is appended to `audit_ledger.jsonl`
- **THEN** the SSE stream SHALL push the event to all connected clients within 1 second

### Requirement: Dashboard serves aggregated health status

The system SHALL expose `GET /api/health` returning combined health of all four components: daemon, dashboard, bot, and RuntimeGuard.

#### Scenario: All components healthy
- **WHEN** all four components report healthy status
- **THEN** `GET /api/health` SHALL return `{"dashboard": "ok", "daemon": {"status": "ok", "last_tick": "..."}, "bot": {"status": "ok", "last_heartbeat": "..."}, "safety": {"status": "ok"}}`

#### Scenario: Daemon stale
- **WHEN** `daemon_heartbeat.json` age exceeds 120 seconds
- **THEN** `GET /api/health` SHALL return `"daemon": {"status": "stale", "last_tick": "...", "stale_seconds": N}`

### Requirement: Dashboard serves Substack posts feed

The system SHALL expose `GET /api/posts` returning recent Christian posts with parsed signals cross-referenced to run history.

#### Scenario: Request posts
- **WHEN** the dashboard receives `GET /api/posts?limit=20`
- **THEN** it SHALL return posts from `processed_posts.json` with parsed status and linked `run_id` where available

### Requirement: Dashboard serves positions from local SQLite

The system SHALL expose `GET /api/positions` returning current holdings from `runtime/positions.db`.

#### Scenario: Request positions
- **WHEN** the dashboard receives `GET /api/positions`
- **THEN** it SHALL query the latest tick's rows from `position_snapshots` and return symbol, position_qty, market_value, unrealized_pnl, and pnl_pct

### Requirement: Dashboard POST /api/kill-switch accepts authenticated kill switch

The system SHALL accept `POST /api/kill-switch` only with a valid `X-Kill-Switch-Secret` header.

#### Scenario: Valid secret provided
- **WHEN** the request includes the correct `X-Kill-Switch-Secret`
- **THEN** the dashboard SHALL write `runtime/kill_switch.flag` and return `{"status": "kill_switch_activated"}`

#### Scenario: Invalid or missing secret
- **WHEN** the request does not include the correct `X-Kill-Switch-Secret`
- **THEN** the dashboard SHALL return HTTP 403

### Requirement: Dashboard is network-isolated

The system SHALL bind the dashboard to `127.0.0.1` and SHALL NOT expose its port to the host network.

#### Scenario: External access attempt
- **WHEN** a request originates from outside the Docker internal network
- **THEN** the request SHALL be rejected at the network layer
