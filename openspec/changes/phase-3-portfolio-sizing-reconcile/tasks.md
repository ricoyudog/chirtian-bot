# Tasks: Phase 3 — Portfolio Sizing & Reconcile Gate

## 1. Portfolio Data Models

- [x] 1.1 Create `src/portfolio/__init__.py`
- [x] 1.2 Implement `src/portfolio/models.py` — Pydantic models:
  - [x] 1.2.1 `Position(symbol, quantity, avg_cost, market_value_usd, side)`
  - [x] 1.2.2 `OpenOrder(order_id, symbol, side, quantity, order_type, limit_price, status)`
  - [x] 1.2.3 `Quote(symbol, price, ask, bid, timestamp)`
  - [x] 1.2.4 `PortfolioSnapshot(account_id, equity_usd, buying_power_usd, positions, open_orders, snapshot_timestamp, source)`
  - [x] 1.2.5 `SizingDecision` — full output model with sizing_status, target/capped notional, order_quantity, reason_codes
  - [x] 1.2.6 `ReconcileDifference(field, local_value, broker_value, tolerance, exceeded)`
  - [x] 1.2.7 `ReconcileResult(reconcile_id, timestamp, status, differences, action_taken, requires_manual_clear)`
- [x] 1.3 Implement `src/portfolio/ledger.py` — `PortfolioLedger` append-only writer:
  - [x] 1.3.1 `append(event_type, data)` — write JSONL line to `portfolio/ledger.jsonl`
  - [x] 1.3.2 `query(event_type, since)` — read back filtered events
- [x] 1.4 Write `tests/test_portfolio_models.py` — cover: model validation, invalid data rejection, Position/Snapshot construction

**Estimated**: ~2 hours

---

## 2. Config & Provider Protocol

- [x] 2.1 Add `SizingConfig` to `src/config/settings.py` — sizing_basis, buying_power_buffer (0.98), price_slippage_buffer_pct (0.5), rounding_mode ("floor"), fractional_shares_enabled (false), min_residual_notional_usd (25), require_reconcile_before_sizing (true)
- [x] 2.2 Update `config.yaml` with `portfolio:` section matching architecture doc
- [x] 2.3 Implement `src/portfolio/provider.py` — `AccountDataProvider` protocol:
  - [x] 2.3.1 `get_snapshot(account_id) -> PortfolioSnapshot`
  - [x] 2.3.2 `get_quote(symbol) -> Quote`
  - [x] 2.3.3 `get_positions(account_id) -> list[Position]`
  - [x] 2.3.4 `get_open_orders(account_id) -> list[OpenOrder]`
- [x] 2.4 Implement `FakeAccountProvider` in `src/portfolio/provider.py`:
  - [x] 2.4.1 Accept pre-configured snapshots, quotes via constructor
  - [x] 2.4.2 Support override methods for test scenarios (e.g., `set_buying_power()`, `add_position()`)
  - [x] 2.4.3 Default test data: equity $50,000, buying_power $10,000, a few positions
- [x] 2.5 Write `tests/test_provider.py` — cover: FakeAccountProvider construction, get_snapshot, get_quote, position/order/quote overrides

**Estimated**: ~2 hours

---

## 3. Buying Power Calculator

- [x] 3.1 Implement `src/portfolio/buying_power.py` — `BuyingPowerCalculator`:
  - [x] 3.1.1 `calculate_available(snapshot, config) -> float` — apply buffer and slippage
  - [x] 3.1.2 `available = buying_power × buying_power_buffer`
  - [x] 3.1.3 `effective_price = quote_price × (1 + price_slippage_buffer_pct / 100)`
  - [x] 3.1.4 Return max spendable amount after all safety margins
- [x] 3.2 Write `tests/test_buying_power.py` — cover:
  - [x] 3.2.1 Normal buying power with buffer
  - [x] 3.2.2 Zero buying power → 0 available
  - [x] 3.2.3 Slippage buffer applied correctly
  - [x] 3.2.4 Very small buying power rounds down to 0

**Estimated**: ~1 hour

---

## 4. Sizing Engine

- [x] 4.1 Implement `src/portfolio/sizing.py` — `SizingEngine`:
  - [x] 4.1.1 `size(instruction, snapshot, quote, config) -> SizingDecision` — main entry point
  - [x] 4.1.2 Buy path (D3):
    - [x] 4.1.2.1 `target_notional = quantity_pct × equity`
    - [x] 4.1.2.2 Chain clamp: buying_power, concentration_cap, max_notional (D5 — record ALL reason codes)
    - [x] 4.1.2.3 `raw_quantity = capped_notional / estimated_price`
    - [x] 4.1.2.4 `floor(raw_quantity / lot_size) × lot_size`
    - [x] 4.1.2.5 `qty < min_quantity → SKIP_TOO_SMALL`
  - [x] 4.1.3 Sell path (D4):
    - [x] 4.1.3.1 `target_quantity = quantity_pct × position.quantity`
    - [x] 4.1.3.2 `floor(target_quantity / lot_size) × lot_size`
    - [x] 4.1.3.3 Clip to `position.quantity` if exceeded
    - [x] 4.1.3.4 `qty = 0 → SKIP_NO_POSITION`
  - [x] 4.1.4 Concentration cap calculation:
    - [x] 4.1.4.1 `current_exposure = position.market_value_usd / equity × 100`
    - [x] 4.1.4.2 `remaining_pct = max_concentration_pct - current_exposure`
    - [x] 4.1.4.3 `remaining_notional = remaining_pct / 100 × equity`
  - [x] 4.1.5 Open order conflict check:
    - [x] 4.1.5.1 Same symbol + any open order → `SIZING_NEEDS_REVIEW` + `OPEN_ORDER_CONFLICT`
  - [x] 4.1.6 Stale quote check:
    - [x] 4.1.6.1 Quote age > 15 min → `SKIP_STALE_QUOTE`
  - [x] 4.1.7 Write sizing decision to PortfolioLedger
- [x] 4.2 Write `tests/test_sizing.py` — cover all 8 required scenarios:
  - [x] 4.2.1 1% < 1 share → `SKIP_TOO_SMALL`
  - [x] 4.2.2 Buying power insufficient → clip or `SKIP_INSUFFICIENT_BUYING_POWER`
  - [x] 4.2.3 Lot size restriction → floor to lot or `SKIP_LOT_SIZE`
  - [x] 4.2.4 Concentration cap hit → clip + `MODIFY_SIZE` + `CLAMPED_CONCENTRATION` reason code
  - [x] 4.2.5 Sell more than position → clip to available
  - [x] 4.2.6 Open order conflict → `SIZING_NEEDS_REVIEW`
  - [x] 4.2.7 Stale quote → `SKIP_STALE_QUOTE`
  - [x] 4.2.8 Normal buy → `EXECUTABLE` with correct quantity and residual
  - [x] 4.2.9 Normal sell → `EXECUTABLE` with correct quantity
  - [x] 4.2.10 Sell with quantity_type "all" → sell full position
  - [x] 4.2.11 Multiple clamp reasons recorded simultaneously
  - [x] 4.2.12 Zero position sell → `SKIP_NO_POSITION`
  - [x] 4.2.13 Ledger event written for each sizing decision

**Estimated**: ~4 hours

---

## 5. Reconciler & Stop-the-World

- [x] 5.1 Extend `src/safety/runtime_guard.py`:
  - [x] 5.1.1 Add `ReconcileStatus` enum (OK, MISMATCH, UNKNOWN)
  - [x] 5.1.2 Add `_reconcile_status` field to `RuntimeGuard.__init__`
  - [x] 5.1.3 Add `assert_reconcile_ok()` — raises `ReconcileBlockedError` if not OK
  - [x] 5.1.4 Add `activate_stop(reason)` and `deactivate_stop()` methods
  - [x] 5.1.5 Add `is_stopped` property
  - [x] 5.1.6 Extend `assert_mutation_allowed()` to also check reconcile status
- [x] 5.2 Implement `src/portfolio/reconcile.py` — `Reconciler`:
  - [x] 5.2.1 `reconcile(local_snapshot, broker_snapshot, config) -> ReconcileResult`
  - [x] 5.2.2 Position comparison — exact match tolerance (D6)
  - [x] 5.2.3 Buying power comparison — ±$1 or 0.1% tolerance (D6)
  - [x] 5.2.4 Open order comparison — order_id set exact match (D6)
  - [x] 5.2.5 Generate `reconcile_id` (`recon_{uuid}`)
  - [x] 5.2.6 Compute snapshot hashes for comparison
- [x] 5.3 Implement `ReconcileGate` in `src/portfolio/reconcile.py`:
  - [x] 5.3.1 `check_and_gate(reconcile_result, guard, ledger) -> None`
  - [x] 5.3.2 Mismatch → `guard.activate_stop(reason)` + write to ledger + write diff report to `portfolio/reconciliations/`
  - [x] 5.3.3 OK + was stopped → requires manual clear (does NOT auto-deactivate)
  - [x] 5.3.4 `manual_clear(guard)` — operator-triggered deactivation
- [x] 5.4 Write `tests/test_reconcile.py` — cover:
  - [x] 5.4.1 Exact match → `status: "ok"`, no differences
  - [x] 5.4.2 Position quantity mismatch → `status: "mismatch"`, difference recorded
  - [x] 5.4.3 Buying power within tolerance → `status: "ok"`
  - [x] 5.4.4 Buying power exceeds tolerance → `status: "mismatch"`
  - [x] 5.4.5 Missing position in broker → `status: "mismatch"`
  - [x] 5.4.6 Extra open order in broker → `status: "mismatch"`
  - [x] 5.4.7 ReconcileGate activates stop on mismatch
  - [x] 5.4.8 `assert_reconcile_ok()` raises after mismatch
  - [x] 5.4.9 `assert_reconcile_ok()` passes when OK
  - [x] 5.4.10 Mismatch → ledger event written
  - [x] 5.4.11 Mismatch → diff report file written
  - [x] 5.4.12 Manual clear restores OK status
  - [x] 5.4.13 Auto-recovery does NOT happen after mismatch (even on next OK reconcile)

**Estimated**: ~3.5 hours

---

## 6. Test Fixtures & Integration

- [ ] 6.1 Create `tests/portfolio_fixtures/` directory with reusable fake snapshots:
  - [ ] 6.1.1 `small_account.yaml` — equity $5,000, buying_power $2,000, 1-2 positions
  - [ ] 6.1.2 `medium_account.yaml` — equity $50,000, buying_power $10,000, 5 positions
  - [ ] 6.1.3 `no_positions.yaml` — equity $50,000, buying_power $50,000, empty positions
  - [ ] 6.1.4 `concentrated_account.yaml` — equity $50,000, one position at 9.8%
  - [ ] 6.1.5 `low_buying_power.yaml` — equity $50,000, buying_power $50, insufficient for 1% orders
- [ ] 6.2 Create `tests/portfolio_fixtures/quotes/` — fake quotes:
  - [ ] 6.2.1 `nvda.yaml` — price $180, normal quote
  - [ ] 6.2.2 `tsla.yaml` — price $250, normal quote
  - [ ] 6.2.3 `expensive.yaml` — price $500 (for too-small scenario)
  - [ ] 6.2.4 `stale.yaml` — price $180, timestamp 30 min ago
- [ ] 6.3 Write `tests/test_portfolio_integration.py` — end-to-end sizing + reconcile:
  - [ ] 6.3.1 Happy path: snapshot → reconcile OK → size buy → EXECUTABLE
  - [ ] 6.3.2 Happy path: snapshot → reconcile OK → size sell → EXECUTABLE
  - [ ] 6.3.3 Reconcile mismatch → sizing blocked → manual clear → sizing works
  - [ ] 6.3.4 Full ledger trail for a sizing + reconcile cycle
- [ ] 6.4 Run full test suite (`pytest tests/ -m "not live"`) and verify all pass
- [ ] 6.5 Verify all Phase 1 and Phase 2 tests still pass alongside new tests
- [ ] 6.6 Run `ruff check` and `ruff format` on all new files

**Estimated**: ~2 hours

---

## Summary

| Group | Name | Estimated | Dependencies |
|-------|------|-----------|--------------|
| 1 | Portfolio Data Models | ~2h | Phase 2 complete |
| 2 | Config & Provider Protocol | ~2h | Group 1 |
| 3 | Buying Power Calculator | ~1h | Groups 1, 2 |
| 4 | Sizing Engine | ~4h | Groups 1–3 |
| 5 | Reconciler & Stop-the-World | ~3.5h | Groups 1, 2 |
| 6 | Test Fixtures & Integration | ~2h | Groups 1–5 |

**Total estimated**: ~14.5 hours
