# QA Test Cases — Phase 3 Portfolio Sizing & Reconcile Gate

## Risk Assessment
- Overall: HIGH
- Factors: Critical (money/trading), New, Complex (state machine), Changed (RuntimeGuard)
- Recommended depth: THOROUGH

## Change Classification
- Type: Backend (pure Python library)
- Atom sequence: qa-smoke → qa-backend → qa-exploratory

## Test Case Sheet

### Smoke Tests (qa-smoke)

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| S1 | All modules importable | `from src.portfolio.models import *` etc. | No ImportError | P1 |
| S2 | Full test suite passes | `pytest tests/ -q` | 628+ passed, 0 failed | P1 |
| S3 | Ruff lint clean | `ruff check src/portfolio/ src/safety/` | All checks passed | P1 |

### Backend Tests (qa-backend)

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| B1 | Buy 1% with sufficient buying power | equity=50000, buying_power=10000, pct=1, price=180 | EXECUTABLE, qty=2, notional≈500 | P1 |
| B2 | Buy blocked by buying power | equity=50000, buying_power=50, pct=1, price=180 | SKIP_INSUFFICIENT_BUYING_POWER or clipped | P1 |
| B3 | Buy blocked by concentration cap | existing NVDA exposure 9.8%, add more | MODIFY_SIZE + CLAMPED_CONCENTRATION | P1 |
| B4 | Sell 50% of position | position qty=50, pct=50 | EXECUTABLE, qty=25 | P1 |
| B5 | Sell more than held | position qty=10, pct=200 | EXECUTABLE, qty=10 (clipped) | P1 |
| B6 | Reconcile exact match | identical snapshots | status=ok, differences=[] | P1 |
| B7 | Reconcile position mismatch | local qty=100, broker qty=90 | status=mismatch, difference recorded | P1 |
| B8 | Reconcile buying power within tolerance | delta=$0.50 (< $1) | status=ok | P1 |
| B9 | Reconcile buying power exceeds tolerance | delta=$2000 | status=mismatch | P1 |
| B10 | Stop-the-world activation | mismatch detected | guard.is_stopped=True, assert_reconcile_ok raises | P1 |
| B11 | Manual-only recovery | mismatch → OK reconcile without manual_clear | guard stays MISMATCH | P1 |
| B12 | Full recovery path | mismatch → manual_clear → OK reconcile | guard reaches OK, sizing unblocked | P1 |
| B13 | Ledger audit trail | Full buy cycle | reconcile_ok + sizing_decision events with correlation_id | P1 |
| B14 | Ledger audit trail (mismatch) | Mismatch + clear + reconcile + size | 4 events: mismatch, manual_clear, ok, sizing_decision | P1 |

### Exploratory Tests (qa-exploratory)

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| E1 | Zero equity edge case | equity=0, buying_power=0 | No division by zero, graceful handling | P1 |
| E2 | Negative delta buying power (broker > local) | local=10000, broker=12000 | status=ok if within tolerance, mismatch if not | P2 |
| E3 | Empty positions on both sides | positions=[] on local and broker | status=ok | P2 |
| E4 | Stale quote rejection | quote timestamp 30 min old | SKIP_STALE_QUOTE | P1 |
| E5 | Open order conflict | same symbol has pending order | SIZING_NEEDS_REVIEW + OPEN_ORDER_CONFLICT | P1 |
