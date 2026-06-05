# Design: Phase 3 — Portfolio Sizing & Reconcile Gate

## Context

Phase 1 built the safety skeleton (config validation, SQLite work queue, JSONL audit ledger, idempotency, runtime guards). Phase 2 added the LLM-backed parser that converts Christian's post text into structured `ParsedInstruction[]` objects, validated against a 52-case gold test set.

Phase 3 bridges the gap between "Christian said buy 1% NVDA" and "place an order for 2 shares of NVDA at $180." This requires knowing the portfolio state (equity, positions, buying power, open orders), applying risk constraints (concentration caps, lot sizes), and verifying that local state matches broker reality before any sizing decision.

The core principle: **`quantity_pct` is a target risk position, not a direct order quantity.** The SizingEngine converts percentages to executable quantities. The Reconciler ensures the conversion is based on accurate data. If either fails, no order flows.

Reference: All design decisions (D1–D11) are documented in [[wiki/decisions/2026-05-21-phase-3-portfolio-sizing-reconcile]].

---

## Goals / Non-Goals

**Goals:**

- Portfolio snapshot model with positions, buying power, open orders
- AccountDataProvider protocol with FakeAccountProvider for testing
- BuyingPowerCalculator with conservative buffer and slippage
- SizingEngine with separate buy/sell paths, chain clamping, all reason codes
- Reconciler with tolerance checks (position exact, buying power ±0.1%, orders exact)
- Stop-the-world mechanism via RuntimeGuard extension
- Manual-only recovery from reconcile mismatch
- All sizing/skip/modify decisions written to portfolio ledger
- 8 required test scenarios passing with fake broker data

**Non-Goals:**

- Webull API integration (Phase 4)
- Real broker reconcile (Phase 4)
- Order placement / execution (Phase 4)
- Live polling / daemon main loop
- TradingAgents integration
- Option sizing (options parsed but not sized in Phase 3)
- FX conversion (MVP is US equities only)

---

## Unknowns & Investigation

### U1: Price source for sizing

**Unknown**: SizingEngine needs `estimated_price` for notional→quantity conversion. Where does this come from?

**Investigation**: Phase 3 uses fake broker data. The `AccountDataProvider` protocol includes `get_quote(symbol)` which returns a `Quote` with `price`, `ask`, `bid`, `timestamp`. `FakeAccountProvider` returns hardcoded quotes. Phase 4's `WebullAccountProvider` will fetch real-time quotes.

**Conclusion**: Price comes from `AccountDataProvider.get_quote()`. Stale quote detection (>15 min threshold per risk gates doc) is a sizing pre-check, not a separate module.

### U2: Open order conflict detection granularity

**Unknown**: Risk gates say "same account + symbol with open order → pause." What counts as a conflict?

**Investigation**: For sizing, any open order for the same symbol is a conflict — regardless of side (buy/sell). The reasoning: an open buy for NVDA means pending exposure that's not yet reflected in position. Sizing a new NVDA buy on top could double-expose. The safest approach is to pause and require review.

**Conclusion**: Same symbol + any open order → `SIZING_NEEDS_REVIEW` with reason `OPEN_ORDER_CONFLICT`. No fine-grained "same side only" logic in Phase 3.

---

## Decisions

### D1: Phase 3 boundary — no Webull API

Phase 3 defines the `AccountDataProvider` protocol and implements `FakeAccountProvider`. Real Webull integration is Phase 4. This keeps sizing logic pure and testable without broker credentials.

### D2: quantity_pct semantics — buy vs sell

- **Buy**: `target_notional = quantity_pct × portfolio_equity` (percentage of total equity)
- **Sell**: `target_quantity = quantity_pct × position.quantity` (percentage of current position)
- **ALL**: direct position quantity, no percentage calculation

### D3: Buy sizing algorithm

```
target_notional = quantity_pct × equity
→ chain clamp: buying_power, concentration_cap, max_notional
→ capped_notional = min(all limits)
→ raw_quantity = capped_notional / estimated_price
→ floor(lot_size) or SKIP_TOO_SMALL
```

### D4: Sell sizing algorithm

```
target_quantity = quantity_pct × position.quantity
→ floor(lot_size) or SKIP
→ clip to available if > position.quantity
→ SKIP_NO_POSITION if = 0
```

### D5: Chain clamping — record all reason codes

Multiple limits firing simultaneously all get recorded in `reason_codes`. Example: buying power AND concentration both clamp → both codes present. Audit value outweighs simplicity.

### D6: Reconcile tolerance

- Position quantity: ±0 (exact match) — integer shares only, no float drift
- Buying power: ±$1 or 0.1%, whichever is larger — covers real-time fluctuations
- Open orders: order_id set exact match — any extra/missing order is significant

### D7: Stop-the-world via Guard layer

Extend `RuntimeGuard` with `ReconcileStatus` flag (OK/MISMATCH/UNKNOWN) and `assert_reconcile_ok()` method. Called before sizing AND before execution. WorkQueue is NOT modified — reconcile blocks sizing/execution only, not parser.

### D8: Reconcile timing — startup + before each sizing

No periodic reconcile. Only at daemon startup (baseline) and before each sizing decision (real-time check).

### D9: Manual-only mismatch recovery

Every MISMATCH requires human intervention. After human clears + clean reconcile pass → OK. Subsequent passes auto-maintain OK. Next mismatch → human again. Matches runbook "Resume only after explicit clean reconcile and owner approval."

### D10: Reconcile output model

Two output destinations: `portfolio/ledger.jsonl` (append-only events) and `portfolio/reconciliations/<id>.json` (full diff reports for human review).

### D11: Implementation grouped into 6 task groups

Models → Config → Provider Protocol → Buying Power & Sizing → Reconciler → Tests & Fixtures. Linear dependency chain.

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Fake broker data doesn't match real Webull behavior | Provider protocol is minimal and well-defined; Phase 4 validates against real API |
| Price source is fake in Phase 3 | Price is injected via provider; production path just swaps the provider |
| Concentration cap calculation depends on accurate position values | Reconcile gate catches drift; sizing uses latest snapshot |
| Stop-the-world blocks all symbols on single-symbol mismatch | Intentional — conservative approach. Single mismatch = systemic concern |
| Lot size / min quantity data not available without broker | Hardcoded in `FakeAccountProvider`; Phase 4 fetches from Webull |
| Sell sizing doesn't account for open sell orders | Open order conflict check catches this before sizing |
| Reconcile tolerance too tight causes false positives | Buying power tolerance (±0.1%) covers normal fluctuation; position exact is safe for integer shares |

---

## Data Model

### PortfolioSnapshot

```python
class Position(BaseModel):
    symbol: str
    quantity: int                    # Whole shares
    avg_cost: float                  # USD
    market_value_usd: float          # Current market value
    side: Literal["long", "short"]   # Position side

class OpenOrder(BaseModel):
    order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: int
    order_type: str                  # MARKET, LIMIT, etc.
    limit_price: float | None
    status: str                      # pending, partial_fill, etc.

class Quote(BaseModel):
    symbol: str
    price: float                     # Last trade price
    ask: float | None
    bid: float | None
    timestamp: datetime              # For stale detection

class PortfolioSnapshot(BaseModel):
    account_id: str
    equity_usd: float                # Total portfolio value
    buying_power_usd: float          # Available buying power
    positions: list[Position]
    open_orders: list[OpenOrder]
    snapshot_timestamp: datetime
    source: Literal["fake", "webull"]  # Data provenance
```

### SizingDecision

```python
class SizingDecision(BaseModel):
    instruction_id: str
    symbol: str
    action: Literal["BUY", "SELL"]
    sizing_status: Literal[
        "EXECUTABLE",
        "MODIFY_SIZE",
        "SKIP_TOO_SMALL",
        "SKIP_INSUFFICIENT_BUYING_POWER",
        "SKIP_LOT_SIZE",
        "SKIP_NO_POSITION",
        "SIZING_NEEDS_REVIEW",
        "SKIP_STALE_QUOTE",
    ]
    basis: Literal["portfolio_equity"] = "portfolio_equity"
    portfolio_equity_usd: float
    available_buying_power_usd: float
    target_pct: float | None
    target_notional_usd: float | None      # Buy path
    capped_notional_usd: float | None      # Buy path, after clamps
    target_quantity: float | None          # Sell path
    estimated_price: float
    lot_size: int
    min_quantity: int
    order_quantity: int                     # Final executable quantity
    estimated_order_notional_usd: float
    unfilled_residual_usd: float
    reason_codes: list[str]                 # All triggered clamp/skip reasons
```

### ReconcileResult

```python
class ReconcileDifference(BaseModel):
    field: str                     # e.g., "position.AAPL.quantity"
    local_value: Any
    broker_value: Any
    tolerance: Any                 # The tolerance threshold
    exceeded: bool                 # Whether tolerance was exceeded

class ReconcileResult(BaseModel):
    reconcile_id: str              # "recon_{uuid}"
    timestamp: datetime
    status: Literal["ok", "mismatch"]
    local_snapshot_hash: str       # sha256 of local snapshot
    broker_snapshot_hash: str      # sha256 of broker snapshot
    differences: list[ReconcileDifference]
    action_taken: str              # "none" | "blocked_all_execution"
    requires_manual_clear: bool
```

### SizingConfig (extends existing config)

```python
class SizingConfig(BaseModel):
    sizing_basis: Literal["portfolio_equity"] = "portfolio_equity"
    buying_power_buffer: float = 0.98          # 2% safety margin
    price_slippage_buffer_pct: float = 0.5     # 0.5% slippage
    rounding_mode: Literal["floor"] = "floor"
    fractional_shares_enabled: bool = False
    min_residual_notional_usd: float = 25.0
    require_reconcile_before_sizing: bool = True
```

---

## API Contracts

Not applicable — no HTTP API surface changes. All components are internal Python modules invoked via function calls within the daemon process.

### AccountDataProvider Protocol

```python
class AccountDataProvider(Protocol):
    def get_snapshot(self, account_id: str) -> PortfolioSnapshot: ...
    def get_quote(self, symbol: str) -> Quote: ...
    def get_positions(self, account_id: str) -> list[Position]: ...
    def get_open_orders(self, account_id: str) -> list[OpenOrder]: ...
```

---

## Migration Plan

No migration needed — this is a new module. Phase 1 infrastructure (WorkQueue, AuditLedger, IdempotencyGuard) and Phase 2 output (ParsedInstruction) are consumed as-is.

One existing file is modified:
- `src/safety/runtime_guard.py` — extended with reconcile gate methods (backward compatible, existing behavior unchanged)
- `src/config/settings.py` — add `SizingConfig` alongside existing `RiskConfig`

---

## Open Questions

_None remaining — all resolved during explore discussion (D1–D11)._
