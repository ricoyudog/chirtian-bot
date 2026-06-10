## Context

Christian Bot Phase 1–3 已完成安全骨架（RuntimeGuard、IdempotencyGuard、WorkQueue、AuditLedger）、指令解析（LLMClient + Parser + Gold Test Set）、Portfolio Sizing 与对账（SizingEngine、Reconciler、ReconcileGate、AccountDataProvider Protocol + FakeAccountProvider）。

Phase 4 是第一个接入真实 broker 的阶段。决策文档（`wiki/decisions/2026-05-21-phase-4-webull-uat-executor.md`）已锁定 5 个关键决策（D4-1 ~ D4-5）：
- D4-1: Transport = CLI-first（subprocess call `webull-skill`）
- D4-2: ExecutionIntent 放 `src/executor/models.py`，MVP 固定 LIMIT order
- D4-3: Audit 复用 `AuditLedger`，event_type="execution_attempt"
- D4-4: Manual Confirmation = 状态机驱动，WorkQueue 集成
- D4-5: 6 个 Task Group 分组

当前 `src/portfolio/provider.py` 定义了 `AccountDataProvider` Protocol 和 `FakeAccountProvider`。Phase 4 需要新增 `WebullAccountProvider` 和整个 `src/executor/` package。

## Goals / Non-Goals

**Goals:**
- 实现 `BrokerClient` Protocol 和 `WebullCLIAdapter`，通过 subprocess 调用 `webull-skill` CLI
- 实现 `OrderBuilder`，将 SizingDecision → ExecutionIntent → Webull order JSON
- 实现 `ExecutionGate`，包含环境 guard、幂等检查、ORDER_UNKNOWN 处理
- 实现状态机驱动的手动确认流程（15 min timeout）
- 实现 `WebullAccountProvider`，通过 Webull CLI 获取真实账户数据
- 所有 ExecutionAttempt 写入 AuditLedger
- UAT smoke checks 通过（account-list、balance、position、open-orders）
- Preview/place/cancel/status 完整流程在 UAT 测试

**Non-Goals:**
- Prod order / Prod auto execution
- Options / Short / HK market
- MARKET order type（MVP 固定 LIMIT）
- MCP adapter 或 Python SDK import（未来可扩展）
- External notification / alert channel（Phase 5）

## Unknowns & Investigation

1. **Webull UAT credential 是否可用？**
   - 调查：需确认 Webull Developer Account 是否已开通，API Key/Secret 是否已获取
   - 结论：Smoke test（Group 6）需要有效 credential；如果不可用，Group 1–5 可用 mock subprocess 测试，Group 6 标记为 blocked

2. **`webull-skill` CLI 是否已安装？**
   - 调查：需确认 `webull-skill` 命令是否在 PATH 中可用
   - 结论：如未安装，需先 `pip install -e .` 从已解压的 skill ZIP 安装

3. **Webull CLI 的 preview order 是否返回与 place 相同格式的 response？**
   - 调查：研究文档显示 preview 和 place 使用相同的 `--order-file` 参数，返回格式均为 OperationResult
   - 结论：WebullCLIAdapter 可用统一的 subprocess 调用模式处理 preview/place

4. **subprocess 长连接 session 管理**
   - 调查：每次 subprocess 调用是否有 SDK 初始化开销？webull-skill 的 config.py 使用 `.env` 加载 credential
   - 结论：CLI 模式每次调用独立初始化，开销可接受（UAT 非高频）；如未来需优化，切换至 MCP adapter

## Decisions

### 1. CLI-first adapter with Protocol isolation

**Decision**: 使用 subprocess 调用 `webull-skill` CLI 实现 `BrokerClient` Protocol。

**Rationale**: CLI 是最隔离、最易测试的方案。subprocess mock 简单直观，不引入 MCP runtime 依赖。Protocol-based 设计确保未来可无损切换。

**Alternatives considered**:
- MCP Server: 更原生 AI Agent 集成，但调试困难，增加 MVP 复杂度
- Python import: 效率最高但耦合度最深，SDK 版本升级直接影响业务代码

### 2. AuditLedger reuse with execution_attempt event type

**Decision**: 复用 `src/state/ledger.py` 的 `AuditLedger`，新增 `event_type="execution_attempt"`。

**Rationale**: AuditLedger 已有 correlation_id、event_type、data 结构。executor audit 是通用稽核的一种 event type，不需要独立存储。避免引入第三个 ledger。

### 3. State-machine driven manual confirmation via WorkQueue

**Decision**: 手动确认通过 `ExecutionIntent.status` 状态机驱动，WorkQueue 管理 lease 和 timeout。

**Rationale**: 复用 Phase 1 已构建的 WorkQueue 基础设施（enqueue/lease/ack/retry_after/dead_letter）。超时通过 WorkQueue 的 TTL 机制自然实现，不需要独立的 timer。

### 4. MVP fixed LIMIT order type

**Decision**: `ExecutionIntent.order_type` 固定为 LIMIT。

**Rationale**: `SizingDecision` 已包含 `estimated_price`，LIMIT order 可以精确控制成交价格。MARKET order 在 MVP 中风险更高（滑点不可控）。

### 5. WebullAccountProvider as separate class, not FakeAccountProvider extension

**Decision**: `WebullAccountProvider` 作为独立 class 实现 `AccountDataProvider` Protocol。

**Rationale**: FakeAccountProvider 用于测试，WebullAccountProvider 用于真实数据。两者职责不同，不应继承关系。通过 Protocol 实现多态，调用方不关心具体实现。

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Webull CLI subprocess 每次初始化开销 | UAT 非高频，开销可接受；如需优化，Phase 5 可切换 MCP |
| Webull API rate limit 或 UAT 环境不稳定 | 所有 broker 调用有 30s timeout；失败记录 AuditLedger |
| subprocess 输出格式变更导致解析失败 | 验证 OperationResult schema 版本；解析层有明确 error handling |
| 手动确认 15 min timeout 在非交易时段误触发 | MVP scope 只有 UAT，交易时段外不触发 |
| FakeAccountProvider 和 WebullAccountProvider 测试混淆 | 测试明确标记 `source="fake"` vs `source="webull"`；integration test 需 UAT credential |

## Data Model

### ExecutionIntent (new — `src/executor/models.py`)

```
execution_id: str          # auto-generated UUID
instruction_id: str        # from SizingDecision
idempotency_key: str       # sha256(instruction_id + side + str(quantity))
symbol: str                # e.g. "AAPL"
side: Literal["BUY", "SELL"]
quantity: int              # >= 1
order_type: Literal["LIMIT"]  # MVP fixed
limit_price: float         # > 0
environment: str           # from RuntimeConfig
status: Literal["ready", "previewed", "submitting", "acked", "unknown",
                "rejected", "filled", "cancelled", "human_review_pending",
                "expired_review"]
```

### ExecutionAttempt (new — `src/executor/models.py`)

```
attempt_id: str            # auto-generated UUID
execution_id: str          # FK to ExecutionIntent
attempt_no: int            # >= 1
operation: Literal["preview_order", "place_order", "get_order_status", "cancel_order"]
request_hash: str          # sha256 of request payload
broker_order_id: str | None
status: Literal["success", "timeout", "error", "unknown"]
response: dict
timestamp: str             # ISO-8601
```

### Existing models (no changes)

- `SizingDecision` (`src/portfolio/models.py`) — 输入端，不修改
- `AuditEvent` (`src/state/models.py`) — 复用，data payload 放 ExecutionAttempt 内容
- `PortfolioSnapshot` (`src/portfolio/models.py`) — source 字段已有 "webull" literal

## API Contracts

Not applicable — no API surface changes in this change. All interactions are internal (subprocess calls to `webull-skill` CLI).
