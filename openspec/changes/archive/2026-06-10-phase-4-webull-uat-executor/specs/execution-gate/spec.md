## ADDED Requirements

### Requirement: Environment guard
ExecutionGate SHALL 在任何 broker 调用前检查 `RuntimeConfig.environment`。当 environment 不为 `uat` 时 SHALL 阻止执行。

#### Scenario: UAT environment allows execution
- **WHEN** RuntimeConfig.environment = "uat" 且 confirmation_mode = "confirm"
- **THEN** ExecutionGate SHALL 允许执行继续

#### Scenario: Prod environment blocks execution
- **WHEN** RuntimeConfig.environment = "prod"
- **THEN** ExecutionGate SHALL 抛出 `EnvironmentBlockedError`，不调用任何 broker 方法

### Requirement: Idempotency guard at execution level
ExecutionGate SHALL 确保同一个 `idempotency_key` 最多调用一次 `place_order`。

#### Scenario: First execution proceeds
- **WHEN** idempotency_key 未曾在 AuditLedger 中以 event_type="execution_attempt" 且 operation="place_order" 出现
- **THEN** ExecutionGate SHALL 允许 place_order

#### Scenario: Duplicate execution blocked
- **WHEN** idempotency_key 已在 AuditLedger 中有成功的 place_order 记录
- **THEN** ExecutionGate SHALL 抛出 `DuplicateExecutionError`，不调用 broker

### Requirement: ORDER_UNKNOWN state handling
当 `place_order` 返回 timeout 或 unknown 状态时，ExecutionIntent.status SHALL 变为 `ORDER_UNKNOWN`。

#### Scenario: Timeout enters ORDER_UNKNOWN
- **WHEN** place_order 超时或返回 ack unknown
- **THEN** ExecutionIntent.status SHALL 变为 ORDER_UNKNOWN，系统 SHALL NOT 再次调用 place_order

#### Scenario: ORDER_UNKNOWN only allows status check
- **WHEN** ExecutionIntent.status 为 ORDER_UNKNOWN
- **THEN** 下一步 SHALL 只允许 get_order_status / open orders / reconcile 操作，绝不可 retry place_order

### Requirement: Audit ledger integration
ExecutionGate SHALL 将每次 ExecutionAttempt 写入 AuditLedger（event_type="execution_attempt"）。

#### Scenario: Successful place_order recorded
- **WHEN** place_order 成功返回
- **THEN** 系统 SHALL 写入 AuditLedger 一条 event_type="execution_attempt" 的记录，包含 request_hash、broker_order_id、response

#### Scenario: Failed attempt also recorded
- **WHEN** place_order 失败或超时
- **THEN** 系统 SHALL 写入 AuditLedger 一条记录，status 为 timeout 或 error
