---
type: decision
created: 2026-05-21
updated: 2026-05-21
tags: [decision, auto-trading, phase-2, parser, gold-set, llm]
status: proposed
---

# 第 2 階段 — Parser 黃金測試集先於自動化

## 決策

Parser 先用黃金測試集鎖定 Christian 語言理解邊界，再接 live polling 或 executor。

第 2 階段的主要交付不是「能解析一篇文」，而是「能穩定拒絕不該交易的文字」。

## Parser 範圍

Parser 只抽取已發生且明確的交易操作：
- buy / sell
- short / cover later phase only unless explicitly enabled
- no-op
- skip conditions and future intent

Parser 不負責：
- portfolio sizing
- TA confirmation
- risk approval
- broker order construction

## 黃金測試集要求

第一批黃金測試集建議 30–50 cases：

| Case 類型 | 目的 |
|---|---|
| 明確買入 | 正確抽取 symbol/action/quantity_pct |
| 明確賣出 | 正確抽取 sell/close intent |
| no-op | 不產生 executable instruction |
| 未來預期 | `準備/打算/下週` 不可交易 |
| 條件句 | `如果/逢低/跌穿才` 不可自動交易 |
| 月度/週度總結 | 不把歷史回顧當新指令 |
| 低信心 ambiguous | 進 `NEEDS_REVIEW` |
| 多指令同帖 | sequence stable；idempotency key stable |

## LLM 執行方式

LLM runtime 使用 [[wiki/decisions/2026-05-21-llm-claude-cli-first]] 作為主決策。

Parser 需要：
- schema-validated JSON output
- deterministic prompt template
- timeout handling
- stderr/stdout capture into audit-safe logs
- no secrets in prompt/log output

## TradingAgents fallback 邊界

第 2 階段也必須在實作前移除現有架構文件中的 TA timeout ambiguity：

- TradingAgents timeout/error/unavailable 可以產生 human-readable review summary。
- 它不可以產生 auto `APPROVE`。
- 除非之後有人手 override 並寫 audit，否則最終 machine state 必須是 `NEEDS_REVIEW`。
- 任何使用 parser result + basic risk 的 fallback 都只能是 advisory，不是 execution gate。

這保持 [[wiki/architecture/auto-trading-risk-gates]] 的權威性：TA unavailable 不可 fail open。

## 失敗策略

| 失敗 | 狀態 |
|---|---|
| Claude CLI unavailable | `NEEDS_REVIEW` |
| JSON schema invalid | `NEEDS_REVIEW` |
| Low confidence | `NEEDS_REVIEW` |
| Multiple possible interpretations | `NEEDS_REVIEW` |
| Future/conditional language | `SKIP_NOT_ACTIONABLE` or `NEEDS_REVIEW` |

任何 parser failure 都不可變成 auto approval。

## 驗收標準

- Gold set replay 必須產生 stable `instruction_id` / `idempotency_key`。
- False-positive executable trade = P0 bug。
- Unit tests 必須覆蓋 no-op、future intent、conditional sentence、summary text。
- Parser result 必須寫 audit event，包含 raw span、confidence、reason codes。

## 相關文件

- [[wiki/architecture/auto-trading-pipeline-High-level]]
- [[wiki/architecture/auto-trading-risk-gates]]
- [[wiki/architecture/auto-trading-state-machine]]
