---
type: wiki
generated: 2026-05-17
tags: [lint, meta]
---

# Lint Report — 2026-05-17

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Error | 1 |
| ⚠️ Warning | 1 |
| ℹ️ Info | 0 |
| ✅ Pass | 9 |

**Overall**: FAIL — 1 error category (broken wikilinks in webull-api index)

## Findings

### 🔴 Errors

**Check #3 — Broken wikilinks (49 broken links, all in one file)**

All 49 broken wikilinks originate from `wiki/webull-api/_index.md`. The links use paths like `webull-api/guides/...` but since the file is already inside `wiki/webull-api/`, these resolve to `wiki/webull-api/webull-api/guides/...` (double-nested). This is a systemic path-prefix issue from the original documentation import.

Root cause: Links should use either `guides/...` (file-relative) or `wiki/webull-api/guides/...` (vault-root).

Two sub-issues within these 49 links:
1. **37 links** point to files that exist but with wrong path resolution (guides + api-reference/trading + api-reference/auth). Fix: correct the link prefix.
2. **12 links** point to files that do not exist at all:
   - `webull-api/api-reference/market-data/non-display/*` (6 links) — no `non-display/` directory exists; files are under `display-solution/` instead
   - `webull-api/api-reference/market-data/streaming/*` (2 links) — no `streaming/` directory exists
   - `webull-api/api-reference/trading/order-query/order-history` (1 link)
   - `webull-api/api-reference/trading/order-query/order-detail` (1 link)
   - `webull-api/api-reference/trading/trade-events/subscribe-trade-events` (1 link)
   - `webull-api/api-reference/broker/_broker-index` (1 link)

**Suggested fix**: Re-generate `wiki/webull-api/_index.md` with correct wikilink paths. Use file-relative paths (e.g. `[[guides/getting-started/welcome]]`) since `_index.md` is already in the `wiki/webull-api/` directory. For the 12 genuinely missing files, either create stubs or remove the links.

### ⚠️ Warnings

**Check #6 — Orphan wiki pages (63 orphans)**

63 wiki pages have zero incoming wikilinks from any file in `memory/` or `wiki/`. These break down as:
- **~35 webull-api reference pages** (broker/*, funding/*, journals/*, events/*, etc.) — linked only from `_index.md` which has broken links, so they appear orphaned
- **~28 other webull-api pages** — genuinely unlinked (display-solution pages, some api-reference pages)

The core wiki structure pages (architecture, patterns, decisions, sessions, questions) are all properly linked and are NOT orphaned.

**Suggested fix**: Fix the broken wikilinks in `_index.md` first (Error above). This will resolve most orphans. Remaining genuinely unlinked pages should get links from the relevant `_index.md` or from `wiki/index.md`.

### ℹ️ Info

None.

## Checks Passed

- ✅ Check #1: Session-bridge freshness — updated today (0 days old, threshold: 30)
- ✅ Check #2: Hot.md freshness — updated today (0 days old, threshold: 14)
- ✅ Check #4: Pitfalls source link validation — no active entries (placeholder state)
- ✅ Check #5: Implicit-contracts consistency — placeholder state (no contracts to validate)
- ✅ Check #7: Extraction completeness — no completed changes to validate
- ✅ Check #8: Session Memory Protocol — found in AGENTS.md
- ✅ Check #9: Hot.md size cap — 96 words (cap: 600)
- ✅ Check #10: Index.md size cap — 27 lines (cap: 80)
- ✅ Check #11: Pitfalls active entry count — 0 entries (cap: 20)

## Suggested Actions

1. **🔴 Fix broken wikilinks in `wiki/webull-api/_index.md`** — Rebuild the index with correct paths. This is the highest priority as it blocks proper navigation of the entire webull-api docs section. Replace `webull-api/...` with either `guides/...`/`api-reference/...` (file-relative) or `wiki/webull-api/...` (vault-root).

2. **🔴 Verify or create 12 missing target files** — The `non-display/`, `streaming/`, `order-history`, `order-detail`, `subscribe-trade-events`, and `_broker-index` targets don't exist at any path. Either create stubs or remove references.

3. **⚠️ Re-check orphans after fixing `_index.md`** — Most of the 63 orphans should gain incoming links once `_index.md` links are corrected. Run lint again after fix to identify any remaining genuine orphans.
