---
type: memory
created: 2026-05-17
---

# MEMORY — Hard Constraints

> AI agent must obey these every session. Never expires.

## Project Identity
- **Name**: Christian Bot
- **Purpose**: AI 交易助手專案，探索整合 Webull OpenAPI 進行自動化行情查詢與交易
- **Stack**: Python 3.10+, Webull OpenAPI Python SDK, MCP protocol, OpenSpec GitFlow

## Hard Constraints
- AK/SK 永遠不暴露（只透過 .env，不進 logs/output）
- 下單操作預設沙盒（WEBULL_ENVIRONMENT=uat）
- 所有 mutating 操作需使用者確認
- 風控上限：notional / quantity / symbol whitelist

## Preferences
- 偏好 MCP Server 整合方式（原生 AI Agent 支援）
- 使用 OpenSpec GitFlow 管理開發流程
- 研究文件放 wiki/research/，決策放 wiki/decisions/
