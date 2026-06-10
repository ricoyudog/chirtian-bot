## ADDED Requirements

### Requirement: ExecutionIntent data model
系统 SHALL 定义 `ExecutionIntent` Pydantic model 作为 executor 阶段的核心数据结构，承接 `SizingDecision` 输出并携带 broker 下单所需的全部信息。

字段 SHALL 包含：`execution_id`（自动生成）、`instruction_id`（来自 SizingDecision）、`idempotency_key`（sha256 of instruction_id + side + str(quantity)）、`symbol`、`side`（BUY/SELL）、`quantity`（int，≥1）、`order_type`（MVP 固定 LIMIT）、`limit_price`（float，>0）、`environment`（来自 RuntimeConfig）、`status`（初始为 ready）。

#### Scenario: Build ExecutionIntent from SizingDecision
- **WHEN** SizingDecision 的 sizing_status 为 EXECUTABLE 且 order_quantity ≥ 1
- **THEN** 系统 SHALL 构建一个 ExecutionIntent，instruction_id、symbol、side、quantity、limit_price 分别从 SizingDecision 对应字段映射，order_type 固定为 LIMIT

#### Scenario: Skip non-executable SizingDecision
- **WHEN** SizingDecision 的 sizing_status 不是 EXECUTABLE（如 SKIP_TOO_SMALL、SKIP_INSUFFICIENT_BUYING_POWER）
- **THEN** 系统 SHALL NOT 创建 ExecutionIntent

### Requirement: ExecutionAttempt data model
系统 SHALL 定义 `ExecutionAttempt` Pydantic model，记录每次与 broker 交互的详细信息。

字段 SHALL 包含：`attempt_id`（自动生成）、`execution_id`（关联 ExecutionIntent）、`attempt_no`（int，≥1）、`operation`（preview_order / place_order / get_order_status / cancel_order）、`request_hash`（sha256 of request payload）、`broker_order_id`（nullable str）、`status`（success / timeout / error / unknown）、`response`（dict）、`timestamp`。

#### Scenario: Record place_order attempt
- **WHEN** executor 向 broker 发送 place_order 请求
- **THEN** 系统 SHALL 创建 ExecutionAttempt，operation 为 place_order，request_hash 为请求 payload 的 sha256，status 根据实际响应设定

#### Scenario: Record timeout attempt
- **WHEN** broker 请求超时
- **THEN** 系统 SHALL 创建 ExecutionAttempt，status 为 timeout，response 包含超时信息

### Requirement: BrokerClient Protocol
系统 SHALL 定义 `BrokerClient` Protocol（typing.Protocol），抽象所有 broker 交互。

Protocol SHALL 声明以下方法：`preview_order(account_id, order_json)` → dict、`place_order(account_id, order_json)` → dict、`get_order_status(account_id, order_id)` → dict、`cancel_order(account_id, order_id)` → dict、`get_account_list()` → list[dict]、`get_balance(account_id)` → dict、`get_positions(account_id)` → list[dict]、`get_open_orders(account_id)` → list[dict]。

#### Scenario: BrokerClient Protocol is implementable
- **WHEN** 一个 class 实现了 BrokerClient Protocol 的所有方法签名
- **THEN** 该 class SHALL 可以被当作 BrokerClient 使用（structural subtyping）

#### Scenario: Business logic does not depend on specific transport
- **WHEN** executor 调用 BrokerClient 的方法
- **THEN** 调用方 SHALL NOT 知道底层是 CLI、MCP 还是 Python import 实现
