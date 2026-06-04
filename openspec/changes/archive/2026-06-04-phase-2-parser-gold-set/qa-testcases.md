# QA Test Cases: phase-2-parser-gold-set

Generated from gold set fixtures (52 cases) + atom skill coverage.

## Smoke Tests (qa-smoke)

Build/start gate — verifies the module is importable and tests can run.

| # | Scenario | Input / Action | Expected Output | Priority |
|---|----------|----------------|-----------------|----------|
| S1 | Module imports | `from src.analyzer.parser import InstructionParser` | Import succeeds, no errors | P1 |
| S2 | Layer 1 test suite runs | `pytest tests/ -m "not live" --tb=short` | All tests pass, exit code 0 | P1 |
| S3 | Gold set cases loadable | Load all 52 YAML fixtures via conftest | 52 cases parsed without error | P1 |
| S4 | No external dependency in Layer 1 | Run Layer 1 with network/CLI unavailable | All mock tests pass | P1 |

## Backend Tests (qa-backend)

Structured walkthrough of parser logic using gold set cases — one representative case per category.

| # | Scenario | Input / Action | Expected Output | Assigned Atom | Priority |
|---|----------|----------------|-----------------|---------------|----------|
| 1 | Clear buy (case 001) | `加倉tem 1%` | EXECUTABLE, action=BUY, symbol=TEM, qty=1.0% | qa-backend | P1 |
| 2 | Clear buy leveraged ETF (case 004) | `加倉tsll 2%（解釋：看好短期反彈）` | EXECUTABLE, symbol=TSLL, qty=2.0% | qa-backend | P1 |
| 3 | Clear buy multiple (case 007) | `買入tem 1% + sofi 1%` | EXECUTABLE, 2 instructions, seq 0/1 | qa-backend | P1 |
| 4 | Clear sell (case 008) | `賣出tsla（-1%）` | EXECUTABLE, action=SELL, symbol=TSLA | qa-backend | P1 |
| 5 | Sell all (case 011) | `賣出全部 smci（4.3%）` | EXECUTABLE, quantity_type=all, qty_pct=null | qa-backend | P1 |
| 6 | Cover short (case 012) | `cover short nvdl` | EXECUTABLE, action=COVER, symbol=NVDL | qa-backend | P1 |
| 7 | No-op — 今天沒有操作 (case 013) | `今天沒有操作` | SKIP_NOT_ACTIONABLE, no instructions | qa-backend | P1 |
| 8 | No-op — philosophy (case 014) | Market philosophy text | SKIP_NOT_ACTIONABLE | qa-backend | P2 |
| 9 | Future intent (case 017) | `準備下週找機會做空泡泡瑪特` | SKIP_NOT_ACTIONABLE, reason includes FUTURE_INTENT | qa-backend | P1 |
| 10 | Future intent — 等回調後 (case 020) | `等回調後加倉tem` | SKIP_NOT_ACTIONABLE, FUTURE_INTENT | qa-backend | P1 |
| 11 | Conditional (case 022) | `如果明天還保持弱勢會考慮削減nvdl` | SKIP_NOT_ACTIONABLE, reason includes CONDITIONAL | qa-backend | P1 |
| 12 | Summary (case 026) | `2026年5月15日美股港股` | SKIP_NOT_ACTIONABLE, reason includes HISTORICAL_SUMMARY | qa-backend | P1 |
| 13 | Mixed summary+forward (case 030) | `今天賣出了tsla，明天準備加倉nvda` | SKIP_NOT_ACTIONABLE, multiple reason codes | qa-backend | P1 |
| 14 | Ambiguous (case 034) | `繼續關注` | NEEDS_REVIEW | qa-backend | P1 |
| 15 | Multi-instruction inline (case 038) | `加倉aaoi 1%，加倉u 2%，加倉sofi 2%` | EXECUTABLE, 3 instructions, seq 0/1/2 | qa-backend | P1 |
| 16 | Multi-instruction numbered (case 039) | Numbered list with multiple buys | EXECUTABLE, correct sequence order | qa-backend | P1 |
| 17 | Option buy — long call (case 043) | `買入1% crwv call（26年7月17日到期，strike 150）` | EXECUTABLE, option_type=call, option_side=long | qa-backend | P1 |
| 18 | Option buy — long put (case 045) | `買入1% nvda put（26年7月18日到期，strike 120）` | EXECUTABLE, option_type=put, option_side=long | qa-backend | P1 |
| 19 | Option sell — short call (case 047) | `開始short 特斯拉 call，到期日7月18日，strike 380` | EXECUTABLE, option_side=short | qa-backend | P1 |
| 20 | Option cover (case 050) | `6月25日short 特斯拉 call 已回報+78%可以cover short` | EXECUTABLE, action=COVER, option fields populated | qa-backend | P1 |

## Backend — Error Handling & Edge Cases (qa-backend)

| # | Scenario | Input / Action | Expected Output | Assigned Atom | Priority |
|---|----------|----------------|-----------------|---------------|----------|
| 21 | LLM timeout | Mock LLM to raise LLMTimeoutError | NEEDS_REVIEW, no instructions | qa-backend | P1 |
| 22 | LLM invalid JSON | Mock LLM to return non-JSON | NEEDS_REVIEW, error captured | qa-backend | P1 |
| 23 | LLM schema mismatch | Mock LLM to return JSON not matching schema | NEEDS_REVIEW | qa-backend | P1 |
| 24 | LLM CLI not found | `claude` binary missing from PATH | LLMUnavailableError, NEEDS_REVIEW | qa-backend | P1 |
| 25 | instruction_id stability | Replay same post_id + text twice | Same instruction_id both times | qa-backend | P1 |
| 26 | idempotency_key determinism | Same input → same idempotency_key | Keys match exactly | qa-backend | P1 |
| 27 | Audit event on success | Parse EXECUTABLE post | Audit event written with status, reason codes, span | qa-backend | P1 |
| 28 | Audit event on skip | Parse SKIP_NOT_ACTIONABLE post | Audit event written with skip status | qa-backend | P1 |
| 29 | Audit event on error | Mock LLM error | Audit event written with NEEDS_REVIEW status | qa-backend | P2 |
| 30 | False-positive guard | Ambiguous text that could look like a trade | Must NOT produce EXECUTABLE | qa-backend | P1 |

## Exploratory Tests (qa-exploratory)

Time-boxed free-form session. 20 minutes allocated (HIGH risk).

| # | Scenario | Input / Action | Expected Output | Assigned Atom | Priority |
|---|----------|----------------|-----------------|---------------|----------|
| E1 | Mixed Chinese/English ticker formats | Posts with alternate ticker formats (e.g. `台積電`, `TSM`, full-width chars) | Correct symbol extraction or NEEDS_REVIEW | qa-exploratory | P2 |
| E2 | Edge case quantities | `加倉nvda 0%`, `加倉nvda 100%`, `加倉nvda 0.01%` | Reasonable handling, no crash | qa-exploratory | P2 |
| E3 | Very long multi-instruction posts | 5+ instructions in single post | All parsed, correct sequence numbers | qa-exploratory | P2 |
| E4 | Unicode edge cases in raw_text | Emoji, special chars, full-width punctuation in post text | No crash, parser handles gracefully | qa-exploratory | P3 |
| E5 | Context loader — missing wiki file | `christian-trading-language.md` not found | Graceful error, NEEDS_REVIEW on parse | qa-exploratory | P2 |
| E6 | Concurrent parse calls | Two parses with same post_id simultaneously | No race condition, idempotency holds | qa-exploratory | P3 |

## Summary

| Atom | Cases | Priority Breakdown |
|------|-------|-------------------|
| qa-smoke | 4 | P1: 4 |
| qa-backend | 30 | P1: 25, P2: 5 |
| qa-exploratory | 6 | P2: 4, P3: 2 |
| **Total** | **40** | **P1: 29, P2: 9, P3: 2** |
