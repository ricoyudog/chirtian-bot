---
type: decision
created: 2026-05-21
updated: 2026-05-21
tags: [decision, auto-trading, llm, claude, cli, parser]
status: accepted
---

# LLM 執行方式 — 優先使用 Claude CLI

## 決策

Christian Bot 的 MVP LLM 使用方式以 **Claude CLI** 作為主要入口，而不是直接從應用程式先接 Anthropic SDK。

本機已確認 `claude` CLI 可用；實作上仍要包成 `LLMClient` adapter，避免未來被 CLI 綁死。

## 使用範圍

Claude CLI 主要用於：
- Christian instruction parser
- parser reasoning / confidence / reason codes
- optional review summary for human operator

Claude CLI 不可直接用於：
- broker mutating operation
- 下單確認
- 繞過 deterministic risk gate
- 保存或輸出 secrets

## Adapter 契約

建議 interface：

```python
class LLMClient:
    def complete_json(self, *, prompt: str, schema: dict, timeout_seconds: int) -> dict:
        ...
```

MVP 實作：

```text
ClaudeCliClient -> subprocess.run(["claude", "-p", ...]) -> parse JSON -> validate schema
```

未來實作可包括：
- Anthropic SDK direct client
- OpenAI-compatible client
- local/offline mock client for tests

## CLI 呼叫原則

Parser 呼叫：
- 使用 non-interactive print mode（`claude -p`）
- prefer `--bare` for minimal ambient context
- parser prompts 盡量 disable tools
- request structured JSON output and validate against schema
- set timeout at subprocess layer
- capture raw output path in audit metadata, but do not log secrets
- fail closed to `NEEDS_REVIEW`

範例形式：

```bash
claude -p \
  --bare \
  --tools "" \
  --output-format json \
  --json-schema '<schema>' \
  --max-budget-usd 0.05 \
  '<parser prompt>'
```

實作時可調整具體 flags，但契約不變：structured output、no tools、timeout、schema validation、fail closed。

## 為什麼優先使用 Claude CLI

- 符合 operator 偏好與本地工作流。
- MVP 簡單：一開始不需要在 app code 內處理 SDK credential plumbing。
- 可使用 Claude Code 既有 auth/session environment。
- 透過 adapter 保留未來改 direct API 的空間。

## 風險與緩解

| 風險 | 緩解 |
|---|---|
| CLI output changes | schema validation + adapter tests |
| CLI unavailable / auth expired | `NEEDS_REVIEW`, no auto order |
| Latency/cost variability | subprocess timeout + budget flag + audit metrics |
| Hidden ambient context | use `--bare` and explicit prompt context |
| Side effects through tools | disable tools for parser calls |
| Production reliability | keep SDK-compatible interface for future swap |

## 驗收標準

- `ClaudeCliClient` 需要有 mocked subprocess output 的 unit tests。
- Invalid JSON/schema/timeout 必須回傳 closed failure，不可回傳 partial instruction。
- Parser prompts 不得包含 API secrets 或 broker credentials。
- Audit event 需記錄 model/adapter name、timeout、schema version、reason codes。

## 相關文件

- [[wiki/decisions/2026-05-21-phase-2-parser-gold-set]]
- [[wiki/architecture/auto-trading-pipeline-High-level]]
- [[memory/MEMORY]]
