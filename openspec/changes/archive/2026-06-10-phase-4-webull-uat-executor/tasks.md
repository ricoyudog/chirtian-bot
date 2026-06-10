<!-- Task Groups (## headings) are checkpoint units. Each group becomes a child GitHub issue. Apply executes one group at a time. -->

## 1. Executor Data Models & Protocol

- [x] 1.1 创建 `src/executor/__init__.py` package
- [x] 1.2 在 `src/executor/models.py` 实现 `ExecutionIntent` Pydantic model（execution_id, instruction_id, idempotency_key, symbol, side, quantity, order_type=LIMIT, limit_price, environment, status）
- [x] 1.3 在 `src/executor/models.py` 实现 `ExecutionAttempt` Pydantic model（attempt_id, execution_id, attempt_no, operation, request_hash, broker_order_id, status, response, timestamp）
- [x] 1.4 在 `src/executor/broker_client.py` 定义 `BrokerClient` Protocol（preview_order, place_order, get_order_status, cancel_order, get_account_list, get_balance, get_positions, get_open_orders）
- [x] 1.5 实现 `build_execution_intent(sizing_decision, config)` 工厂函数，从 SizingDecision 映射到 ExecutionIntent
- [x] 1.6 编写 `tests/test_executor_models.py`：验证 ExecutionIntent 构建、字段映射、非 EXECUTABLE 跳过、idempotency_key 确定性

## 2. Webull CLI Adapter

- [x] 2.1 在 `src/executor/webull_adapter.py` 实现 `WebullCLIAdapter` class，实现 `BrokerClient` Protocol
- [x] 2.2 实现 subprocess wrapper：`_run_cli(action, args)` 方法，超时 30 秒，解析 OperationResult JSON
- [x] 2.3 实现 `preview_order` / `place_order`：生成临时 order JSON 文件，调用 `webull-skill trading --action preview/place`
- [x] 2.4 实现 `get_order_status` / `cancel_order`：调用 `webull-skill trading --action detail/cancel`
- [x] 2.5 实现 `get_account_list` / `get_balance` / `get_positions` / `get_open_orders`：调用对应 CLI 命令
- [x] 2.6 定义 `BrokerTimeoutError` / `BrokerError` / `BrokerAuthError` 异常类
- [x] 2.7 编写 `tests/test_webull_adapter.py`：用 mock subprocess 测试所有方法，测试 timeout、错误响应、成功响应解析

## 3. Order Builder & Execution Gate

- [x] 3.1 在 `src/executor/order_builder.py` 实现 `OrderBuilder` class
- [x] 3.2 实现 `build_order_json(execution_intent)` → dict（symbol, side, order_type=LIMIT, limit_price, quantity, instrument_type=EQUITY, market=US, time_in_force=DAY, entrust_type=QTY, support_trading_session=CORE, combo_type=NORMAL）
- [x] 3.3 实现 `compute_request_hash(order_json)` → sha256 hex string
- [x] 3.4 添加参数验证：quantity > 0、limit_price > 0、symbol non-empty
- [x] 3.5 在 `src/executor/execution_gate.py` 实现 `ExecutionGate` class
- [x] 3.6 实现 environment guard：environment != "uat" → raise EnvironmentBlockedError
- [x] 3.7 实现 execution-level idempotency guard：查询 AuditLedger 是否已有同 idempotency_key 的 place_order 记录
- [x] 3.8 实现 ORDER_UNKNOWN 状态转换：place_order timeout/unknown → status=ORDER_UNKNOWN，后续只允许 get_order_status/reconcile
- [x] 3.9 实现 AuditLedger 集成：每次 ExecutionAttempt 写入 event_type="execution_attempt"
- [x] 3.10 编写 `tests/test_order_builder.py`：验证 order JSON 生成、request hash 确定性、参数验证
- [x] 3.11 编写 `tests/test_execution_gate.py`：验证环境 guard、幂等 guard、ORDER_UNKNOWN 流转、audit 写入

## 4. Manual Confirmation Flow

- [x] 4.1 在 `src/executor/confirmation.py` 实现 `ConfirmationManager` class
- [x] 4.2 实现 `enter_review(execution_intent, work_queue)`：将 ExecutionIntent status 设为 HUMAN_REVIEW_PENDING，enqueue 到 WorkQueue with TTL=15min
- [x] 4.3 实现 `confirm(execution_id)` → status 变为 ready，继续执行
- [x] 4.4 实现 `skip(execution_id)` → status 变为 CANCELLED，不调用 broker
- [x] 4.5 实现 `reduce_quantity(execution_id, new_qty, operator)` → 验证 new_qty < original，更新 quantity，写入 AuditLedger（event_type="manual_override"）
- [x] 4.6 实现 timeout 处理：WorkQueue lease 过期 → status 变为 EXPIRED_REVIEW
- [x] 4.7 编写 `tests/test_confirmation.py`：验证 confirm/skip/reduce_quantity/timeout 四条路径，验证 reduce 拒绝 increase，验证 audit trail
- [x] 4.8 Fix `enter_review()`：移除非确定性 `lease()` 调用，改用内部 `_deadlines` dict 存储 deadline（entered_at + 15min）
- [x] 4.9 Fix `check_timeouts()`：比较存储的 deadline 而非 WorkQueue lease expiry，移除对 `job.lease_expires_at` 的依赖
- [x] 4.10 Fix `reduce_quantity()`：添加显式 `new_qty >= 1` 验证，防止 `model_copy` 绕过 Pydantic `ge=1` 约束
- [x] 4.11 Fix lint：移除 unused import、排序 imports、拆分长行、重命名 `test_reduce_rejects_zero_quantity` → 验证正确拒绝零数量

## 5. WebullAccountProvider

- [x] 5.1 在 `src/portfolio/provider.py` 新增 `WebullAccountProvider` class，实现 `AccountDataProvider` Protocol
- [x] 5.2 实现 `get_snapshot(account_id)`：调用 balance + positions + open_orders → 组装 PortfolioSnapshot(source="webull")
- [x] 5.3 实现 `get_quote(symbol)`：调用 stock-snapshot → 转换为 Quote model
- [x] 5.4 实现 `get_positions(account_id)`：调用 positions CLI → 转换为 list[Position]
- [x] 5.5 实现 `get_open_orders(account_id)`：调用 open orders CLI → 转换为 list[OpenOrder]
- [x] 5.6 错误处理：CLI timeout/auth failure 直接抛出 BrokerTimeoutError/BrokerAuthError，不回退 fake data
- [x] 5.7 编写 `tests/test_webull_account_provider.py`：用 mock WebullCLIAdapter 测试所有方法，验证 source="webull"，验证错误不回退
- [x] 5.8 Fix `get_quote()` null guard：`"ask" in raw` → `raw.get("ask") is not None`，防止 API 返回 `{"ask": null}` 时 `float(None)` TypeError
- [x] 5.9 添加测试：验证 `get_quote()` 在 ask/bid 为 null 时返回 `None` 而非抛出异常

## 6. Integration Tests & Smoke Checks

- [x] 6.1 编写 `tests/test_executor_integration.py`：端到端 SizingDecision → ExecutionIntent → OrderBuilder → preview → confirm → place flow（mock broker）
- [x] 6.2 编写 idempotency double-place guard 测试：同一 idempotency_key 第二次 place_order 必须 blocked
- [x] 6.3 编写 ORDER_UNKNOWN integration 测试：place_order timeout → get_order_status → reconcile
- [x] 6.4 编写 manual confirmation timeout integration 测试：15 min timeout → EXPIRED_REVIEW
- [x] 6.5 编写 UAT smoke test fixture：`tests/smoke/test_webull_uat_smoke.py`（需 UAT credential，标记 @pytest.mark.skipif）
- [x] 6.6 Smoke test: account-list 返回非空列表
- [x] 6.7 Smoke test: balance 返回有效数值
- [x] 6.8 Smoke test: positions 返回 list
- [x] 6.9 Smoke test: open-orders 返回 list
- [x] 6.10 Smoke test: preview order → cancel（不实际 place）完整流程
- [x] 6.11 运行全量测试 `pytest`，确认无回归
