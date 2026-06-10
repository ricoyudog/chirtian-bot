## Why

Phase 1–3 建立了安全骨架、指令解析、portfolio sizing 与对账基础设施，但尚未接入任何真实 broker。系统目前只能用 `FakeAccountProvider` 产生模拟数据，所有 sizing 和 reconcile 结果无法验证真实性。Phase 4 是第一个接触真实金融系统的阶段 — 在 UAT 环境中实现 Webull executor，将已通过全部安全 gate 的 `SizingDecision` 转化为可审计的 UAT order flow。

## What Changes

- 新增 `src/executor/` package，包含 executor 数据模型、`BrokerClient` Protocol、order builder、execution gate、手动确认流程
- 新增 `WebullCLIAdapter`，通过 subprocess 调用 `webull-skill` CLI 实现 `BrokerClient` Protocol
- 新增 `WebullAccountProvider`，通过 Webull CLI 实现 `AccountDataProvider` Protocol，取代 `FakeAccountProvider`
- 新增 `ExecutionIntent` 和 `ExecutionAttempt` Pydantic models，衔接 `SizingDecision` 到 broker order
- 新增 manual confirmation 流程：状态机驱动的 `HUMAN_REVIEW_PENDING` → confirm/skip/reduce_quantity → `EXPIRED_REVIEW` timeout
- 复用 `AuditLedger`，新增 `event_type="execution_attempt"` 记录 broker request hash 与 response
- 新增 `ORDER_UNKNOWN` 处理：timeout/ack unknown 后只允许查单和对账，绝不盲目 retry `place_order`

## Capabilities

### New Capabilities
- `executor-models`: ExecutionIntent、ExecutionAttempt Pydantic 数据模型及 BrokerClient Protocol 定义
- `webull-cli-adapter`: WebullCLIAdapter — subprocess 调用 webull-skill CLI，实现 BrokerClient 接口
- `order-builder`: OrderBuilder — 将 SizingDecision 转换为 Webull order JSON
- `execution-gate`: ExecutionGate — 环境 guard、幂等检查、ORDER_UNKNOWN 状态处理
- `manual-confirmation`: 状态机驱动的手动确认流程（WorkQueue 集成，15 min timeout）
- `webull-account-provider`: WebullAccountProvider — 实现 AccountDataProvider，通过 Webull CLI 获取真实账户数据

### Modified Capabilities
（无 — Phase 4 不修改已有 spec 的 REQUIREMENTS，只新增 capability）

## Impact

- **新 package**: `src/executor/`（models.py, broker_client.py, webull_adapter.py, order_builder.py, execution_gate.py, confirmation.py）
- **新依赖**: `webull-skill` CLI（需安装 webull-openapi-skills 并完成 auth）
- **配置变更**: `config.yaml` 需新增 `webull.app_key`、`webull.app_secret`、`webull.account_id`（UAT）
- **既有代码影响**: `src/portfolio/provider.py` 新增 `WebullAccountProvider` class（不影响 `FakeAccountProvider`）
- **测试**: 新增 `tests/test_executor_*.py` 系列测试，包含 smoke check（需 UAT credential）
- **外部依赖**: Webull OpenAPI Skill（已研究，见 `wiki/research/webull-openapi-skill.md`）

## GitHub Issue

Parent: https://github.com/ricoyudog/chirtian-bot/issues/22
