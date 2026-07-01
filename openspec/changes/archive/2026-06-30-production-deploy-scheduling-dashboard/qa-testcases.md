# QA Test Cases: production-deploy-scheduling-dashboard

| # | Scenario | Input / Action | Expected Output | Atom | Priority |
|---|----------|----------------|-----------------|------|----------|
| 1 | All new modules import cleanly | `import src.ops.daemon, ...` | No ImportError | qa-smoke | P1 |
| 2 | Full test suite passes | `pytest tests/` | All pass, exit 0 | qa-smoke | P1 |
| 3 | Dashboard app creates successfully | `create_app()` | FastAPI app instance | qa-smoke | P1 |
| 4 | Daemon CLI shows help | `python -m src.ops --help` | Usage text, exit 0 | qa-cli | P1 |
| 5 | Daemon refuses start with kill_switch.flag | Create flag, run() | Exits, guard activated | qa-backend | P1 |
| 6 | Daemon lock prevents dual-start | Acquire flock, run() | Lock error exit | qa-backend | P1 |
| 7 | Dashboard /api/health shape | GET /api/health | daemon/dashboard/bot/safety keys | qa-api | P1 |
| 8 | Dashboard /api/safety shape | GET /api/safety | kill_switch_active + guard_status | qa-api | P1 |
| 9 | Dashboard kill-switch 403 without secret | POST (no header) | HTTP 403 | qa-api | P1 |
| 10 | Dashboard /api/runs returns list | GET /api/runs | JSON array | qa-api | P1 |
