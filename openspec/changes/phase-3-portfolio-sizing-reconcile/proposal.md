# Proposal: Phase 3 — Portfolio Sizing & Reconcile Gate

## Why

Phase 2 讓系統能解析 Christian 的交易語言，輸出結構化的 `ParsedInstruction`。但 Christian 的 `quantity_pct`（例如 1%）是目標風險/倉位，不是直接下單數量。在 executor/place-order 之前，系統必須：

1. **知道現在帳戶有什麼**（持倉、可用購買力、掛單）
2. **把百分比換算成具體股數**（考慮購買力、集中度上限、最小交易單位）
3. **確認本地認知與券商一致**（reconcile gate）

沒有這三步，executor 就是在盲下單。Phase 3 的核心交付不是「能算出股數」，而是 **「算不出來時絕對不下單」**。

## What Changes

1. **Portfolio data models** — `PortfolioSnapshot`, `Position`, `SizingDecision`, `ReconcileResult` 等 Pydantic models，定義 portfolio 層的所有資料結構。
2. **AccountDataProvider protocol** — broker 抽象層，Phase 3 用 `FakeAccountProvider` 測試，Phase 4 接 `WebullAccountProvider`。
3. **BuyingPowerCalculator** — 保守計算可用購買力，含 buffer 和 slippage。
4. **SizingEngine** — 將 `quantity_pct` 轉為 `order_quantity`，處理買入/賣出兩條路徑，鏈式 clamp 記錄所有 reason codes。
5. **Reconciler** — 比對本地 snapshot vs broker 資料，mismatch 時觸發 stop-the-world。
6. **ReconcileGate** — 擴展 `RuntimeGuard`，MISMATCH 時阻斷所有 sizing 和 execution。

## Capabilities

### New Capabilities

- `portfolio-models`: Portfolio snapshot, position, sizing decision, reconcile result data models
- `account-provider`: AccountDataProvider protocol + FakeAccountProvider for testing
- `buying-power`: Conservative buying power calculator with buffer/slippage
- `sizing-engine`: quantity_pct → order_quantity conversion with buy/sell paths, chain clamping, lot size checks
- `reconciler`: Local vs broker reconciliation with tolerance checks and stop-the-world gate

### Modified Capabilities

- `runtime-guard`: Extended with reconcile status flag and `assert_reconcile_ok()` method

## Impact

- **New code**: `src/portfolio/` module (models.py, provider.py, buying_power.py, sizing.py, reconcile.py, ledger.py)
- **Modified code**: `src/safety/runtime_guard.py` (add reconcile gate), `src/config/settings.py` (add SizingConfig)
- **New tests**: `tests/test_sizing.py`, `tests/test_reconcile.py`, `tests/test_buying_power.py`, `tests/portfolio_fixtures/`
- **Existing dependency**: Uses Phase 1's `WorkQueue`, `AuditLedger`, `IdempotencyGuard` — no modification needed
- **Existing dependency**: Uses Phase 2's `ParsedInstruction` as sizing input — read-only
- **New config**: `SizingConfig` in config.yaml with sizing_basis, buying_power_buffer, slippage, fractional_shares settings

## Acceptance Criteria

- Sizing output 必須包含 target_notional、capped_notional、estimated_price、quantity、reason_codes
- Reconcile mismatch 必須阻止所有新的 executable orders
- Executor-facing object 只能包含具體 quantity，不可保留 unresolved percentage
- Tests 必須可用 fake broker/account snapshots 執行，不依賴 Webull credentials
- 所有 8 個必要測試情境通過（too small, buying power, lot size, concentration, sell more than position, open order conflict, stale quote, reconcile mismatch）
- 每個 sizing/skip/modify decision 寫 portfolio ledger
- Reconcile mismatch 觸發 stop-the-world，需要人工清除
- 買入路徑使用 equity-based notional，賣出路徑使用 position-based quantity

## GitHub Issue

Parent issue: https://github.com/ricoyudog/chirtian-bot/issues/15

## References

- [[wiki/decisions/2026-05-21-phase-3-portfolio-sizing-reconcile]]
- [[wiki/decisions/2026-05-21-auto-trading-completion-phases]]
- [[wiki/architecture/auto-trading-pipeline-High-level]] (Module 2c)
- [[wiki/architecture/auto-trading-state-machine]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/operations/auto-trading-runbook]]
- [[wiki/research/stop-the-world-mechanism-analysis]]
- Phase 2 archive: `openspec/changes/archive/2026-06-04-phase-2-parser-gold-set/`
