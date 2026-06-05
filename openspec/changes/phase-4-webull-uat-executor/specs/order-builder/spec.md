## ADDED Requirements

### Requirement: OrderBuilder converts SizingDecision to Webull order JSON
系统 SHALL 提供 `OrderBuilder` class，将 `SizingDecision` 和 `ExecutionIntent` 转换为 Webull `place`/`preview` 所需的 order JSON。

Order JSON SHALL 包含以下字段：`symbol`、`side`（BUY/SELL）、`order_type`（LIMIT）、`limit_price`、`quantity`、`instrument_type`（EQUITY）、`market`（US）、`time_in_force`（DAY）、`entrust_type`（QTY）、`support_trading_session`（CORE）、`combo_type`（NORMAL）。

#### Scenario: Build LIMIT BUY order
- **WHEN** ExecutionIntent 的 side=BUY、order_type=LIMIT、limit_price=180.0、quantity=10
- **THEN** OrderBuilder SHALL 生成包含 `{"symbol": "...", "side": "BUY", "order_type": "LIMIT", "limit_price": 180.0, "quantity": 10, "instrument_type": "EQUITY", "market": "US", "time_in_force": "DAY", "entrust_type": "QTY", "support_trading_session": "CORE", "combo_type": "NORMAL"}` 的 JSON

#### Scenario: Build LIMIT SELL order
- **WHEN** ExecutionIntent 的 side=SELL
- **THEN** OrderBuilder SHALL 生成 side=SELL 的 order JSON，其余字段结构相同

### Requirement: OrderBuilder validates order parameters
OrderBuilder SHALL 在生成 order JSON 前验证所有参数的合法性。

#### Scenario: Quantity must be positive
- **WHEN** quantity ≤ 0
- **THEN** 系统 SHALL 抛出 `OrderBuildError`

#### Scenario: Limit price must be positive
- **WHEN** limit_price ≤ 0
- **THEN** 系统 SHALL 抛出 `OrderBuildError`

#### Scenario: Symbol must be non-empty
- **WHEN** symbol 为空字符串
- **THEN** 系统 SHALL 抛出 `OrderBuildError`

### Requirement: OrderBuilder generates request hash
OrderBuilder SHALL 为每个生成的 order JSON 计算 sha256 hash，供 ExecutionAttempt 记录。

#### Scenario: Request hash is deterministic
- **WHEN** 相同的 ExecutionIntent 被构建两次
- **THEN** 两次生成的 request_hash SHALL 相同
