## ADDED Requirements

### Requirement: WebullCLIAdapter implements BrokerClient
系统 SHALL 提供 `WebullCLIAdapter` class，通过 subprocess 调用 `webull-skill` CLI 实现 `BrokerClient` Protocol 的所有方法。

每个方法 SHALL 将参数转换为 `webull-skill` CLI 命令，执行 subprocess，解析 JSON stdout，返回 dict。subprocess 执行 SHALL 设置超时（默认 30 秒）。

#### Scenario: Preview order via CLI
- **WHEN** 调用 `preview_order(account_id="123", order_json={...})`
- **THEN** 系统 SHALL 执行 `webull-skill trading --action preview --account-id 123 --order-file <temp_file>`，返回解析后的 dict 结果

#### Scenario: Place order via CLI
- **WHEN** 调用 `place_order(account_id="123", order_json={...})`
- **THEN** 系统 SHALL 执行 `webull-skill trading --action place --account-id 123 --order-file <temp_file>`，返回包含 broker_order_id 的 dict

#### Scenario: CLI subprocess timeout
- **WHEN** subprocess 执行超过 30 秒
- **THEN** 系统 SHALL 终止 subprocess 并抛出 `BrokerTimeoutError`

### Requirement: Environment routing
WebullCLIAdapter SHALL 根据 `WEBULL_ENVIRONMENT` 环境变量路由到 UAT 或 prod endpoint。MVP 阶段 SHALL 固定为 `uat`。

#### Scenario: UAT environment routing
- **WHEN** WEBULL_ENVIRONMENT=uat
- **THEN** 所有 CLI 调用 SHALL 走 UAT endpoint（webull-skill 的 env_router 模块自动处理）

#### Scenario: Prod environment blocked at ExecutionGate level
- **WHEN** RuntimeConfig.environment 为 prod
- **THEN** WebullCLIAdapter 不 SHALL 被调用（由 ExecutionGate 在更上层拦截）

### Requirement: CLI output parsing
WebullCLIAdapter SHALL 解析 `webull-skill` 的 OperationResult JSON 格式（`{ok: bool, detail: str, payload: {...}}`）。

#### Scenario: Successful CLI response
- **WHEN** CLI 返回 `{"ok": true, "detail": "...", "payload": {...}}`
- **THEN** 系统 SHALL 返回 payload dict

#### Scenario: Failed CLI response
- **WHEN** CLI 返回 `{"ok": false, "detail": "error message"}`
- **THEN** 系统 SHALL 抛出 `BrokerError`，包含 detail 信息
