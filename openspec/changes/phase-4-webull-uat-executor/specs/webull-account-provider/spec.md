## ADDED Requirements

### Requirement: WebullAccountProvider implements AccountDataProvider
系统 SHALL 提供 `WebullAccountProvider` class，通过 WebullCLIAdapter 实现 `AccountDataProvider` Protocol 的所有方法（`get_snapshot`、`get_quote`、`get_positions`、`get_open_orders`）。

#### Scenario: Get snapshot from Webull
- **WHEN** 调用 `get_snapshot(account_id="123")`
- **THEN** 系统 SHALL 通过 WebullCLIAdapter 调用 balance + positions + open orders，聚合为 `PortfolioSnapshot`，source="webull"

#### Scenario: Get quote from Webull
- **WHEN** 调用 `get_quote(symbol="AAPL")`
- **THEN** 系统 SHALL 通过 WebullCLIAdapter 调用 stock-snapshot，返回 `Quote` model

### Requirement: Snapshot source distinction
WebullAccountProvider 返回的 PortfolioSnapshot SHALL 设置 `source="webull"`，与 FakeAccountProvider 的 `source="fake"` 区分。

#### Scenario: Source field is webull
- **WHEN** WebullAccountProvider.get_snapshot() 被调用
- **THEN** 返回的 PortfolioSnapshot.source SHALL 为 "webull"

### Requirement: Graceful degradation on broker unavailable
当 Webull CLI 不可用或返回错误时，WebullAccountProvider SHALL NOT 返回 FakeAccountProvider 的数据。

#### Scenario: Broker timeout raises error
- **WHEN** Webull CLI 调用超时
- **THEN** 系统 SHALL 抛出 `BrokerTimeoutError`，不回退到 fake data

#### Scenario: Auth failure raises error
- **WHEN** Webull CLI 返回认证错误
- **THEN** 系统 SHALL 抛出 `BrokerAuthError`，不回退到 fake data
