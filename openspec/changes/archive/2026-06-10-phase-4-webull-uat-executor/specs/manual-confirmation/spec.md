## ADDED Requirements

### Requirement: State-machine driven confirmation flow
手动确认 SHALL 通过状态机驱动，与现有 WorkQueue 集成。当 ExecutionIntent.status 进入 `HUMAN_REVIEW_PENDING` 时，由 WorkQueue 管理 lease 和 timeout。

#### Scenario: Execution enters human review
- **WHEN** ExecutionIntent 通过所有 gate 检查且 RuntimeConfig.confirmation_mode = "confirm"
- **THEN** ExecutionIntent.status SHALL 变为 HUMAN_REVIEW_PENDING，进入 WorkQueue 等待 operator 操作

#### Scenario: Operator confirms
- **WHEN** operator 对 HUMAN_REVIEW_PENDING 的 ExecutionIntent 发出 confirm
- **THEN** ExecutionIntent.status SHALL 变为 ready（或直接进入 ORDER_PREVIEWED），继续执行流程

#### Scenario: Operator skips
- **WHEN** operator 对 HUMAN_REVIEW_PENDING 的 ExecutionIntent 发出 skip
- **THEN** ExecutionIntent.status SHALL 变为 CANCELLED，不执行任何 broker 调用

#### Scenario: Operator reduces quantity
- **WHEN** operator 对 HUMAN_REVIEW_PENDING 的 ExecutionIntent 发出 reduce_quantity(new_qty=5)
- **THEN** 系统 SHALL 验证 new_qty < 原始 quantity，更新 ExecutionIntent.quantity，记录 override（operator、timestamp、original quantity、new quantity），继续执行

### Requirement: Confirmation timeout
手动确认 SHALL 有 15 分钟 timeout。超时后 ExecutionIntent.status SHALL 变为 `EXPIRED_REVIEW`，不执行任何 broker 调用。

#### Scenario: Timeout expires
- **WHEN** HUMAN_REVIEW_PENDING 状态超过 15 分钟无 operator 操作
- **THEN** ExecutionIntent.status SHALL 变为 EXPIRED_REVIEW，系统 SHALL NOT 调用 broker

#### Scenario: Timeout resets on operator action
- **WHEN** operator 在 15 分钟内操作（但不是最终确认）
- **THEN** timeout SHALL NOT 重置（15 分钟从进入 HUMAN_REVIEW_PENDING 开始计算）

### Requirement: Operator action restrictions
Operator SHALL 只允许三个动作：`confirm`、`skip`、`reduce_quantity`。以下操作 SHALL NOT 允许：increase quantity、widen risk limit、switch prod、bypass reconcile。

#### Scenario: Increase quantity rejected
- **WHEN** operator 尝试 increase quantity
- **THEN** 系统 SHALL 拒绝该操作

#### Scenario: Reduce quantity must be less than original
- **WHEN** operator 发出 reduce_quantity(new_qty) 且 new_qty >= 原始 quantity
- **THEN** 系统 SHALL 拒绝该操作

### Requirement: Override audit trail
每次 operator override（reduce_quantity）SHALL 记录到 AuditLedger：operator、timestamp、original recommendation、changed fields、reason。

#### Scenario: Reduce quantity audit entry
- **WHEN** operator 执行 reduce_quantity
- **THEN** AuditLedger SHALL 包含一条 event_type="manual_override" 的记录，含 operator、timestamp、field="quantity"、original_value、new_value
