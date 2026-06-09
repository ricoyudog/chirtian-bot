"""Smoke tests for Webull UAT executor — require real UAT credentials."""

import os

import pytest

from src.executor.order_builder import OrderBuilder
from src.executor.webull_adapter import WebullCLIAdapter

# Skip entire module when UAT credentials are not configured.
# Set WEBULL_UAT_ACCOUNT_ID to enable these tests.
_UAT_ACCOUNT_ID = os.environ.get("WEBULL_UAT_ACCOUNT_ID", "")

pytestmark = pytest.mark.skipif(
    not _UAT_ACCOUNT_ID,
    reason="WEBULL_UAT_ACCOUNT_ID not set — skipping UAT smoke tests",
)


@pytest.fixture
def adapter() -> WebullCLIAdapter:
    return WebullCLIAdapter()


@pytest.fixture
def account_id() -> str:
    return _UAT_ACCOUNT_ID


# ---------------------------------------------------------------------------
# 6.6 — account-list returns non-empty list
# ---------------------------------------------------------------------------


class TestAccountList:
    def test_returns_non_empty_list(self, adapter: WebullCLIAdapter):
        accounts = adapter.get_account_list()
        assert isinstance(accounts, list)
        assert len(accounts) > 0

    def test_account_entry_has_id(self, adapter: WebullCLIAdapter):
        accounts = adapter.get_account_list()
        for acct in accounts:
            assert "id" in acct or "account_id" in acct


# ---------------------------------------------------------------------------
# 6.7 — balance returns valid numeric values
# ---------------------------------------------------------------------------


class TestBalance:
    def test_returns_valid_balance(
        self, adapter: WebullCLIAdapter, account_id: str,
    ):
        balance = adapter.get_balance(account_id)
        assert isinstance(balance, dict)
        assert "equity" in balance or "total_assets" in balance
        # At least one numeric field should be present and non-negative
        equity = float(balance.get("equity", balance.get("total_assets", -1)))
        assert equity >= 0


# ---------------------------------------------------------------------------
# 6.8 — positions returns a list
# ---------------------------------------------------------------------------


class TestPositions:
    def test_returns_list(
        self, adapter: WebullCLIAdapter, account_id: str,
    ):
        positions = adapter.get_positions(account_id)
        assert isinstance(positions, list)


# ---------------------------------------------------------------------------
# 6.9 — open-orders returns a list
# ---------------------------------------------------------------------------


class TestOpenOrders:
    def test_returns_list(
        self, adapter: WebullCLIAdapter, account_id: str,
    ):
        orders = adapter.get_open_orders(account_id)
        assert isinstance(orders, list)


# ---------------------------------------------------------------------------
# 6.10 — preview → cancel (no actual place) complete flow
# ---------------------------------------------------------------------------


class TestPreviewCancelFlow:
    def test_preview_then_cancel(
        self, adapter: WebullCLIAdapter, account_id: str,
    ):
        builder = OrderBuilder()
        from src.executor.models import ExecutionIntent

        intent = ExecutionIntent(
            instruction_id="smoke_test_001",
            idempotency_key="smoke_key_preview_cancel",
            symbol="AAPL",
            side="BUY",
            quantity=1,
            limit_price=200.0,
            environment="uat",
        )
        order_json = builder.build_order_json(intent)

        # Preview should succeed
        preview = adapter.preview_order(account_id, order_json)
        assert isinstance(preview, dict)

        # If preview returns an order_id, cancel it to clean up
        order_id = preview.get("order_id")
        if order_id:
            cancel_result = adapter.cancel_order(account_id, order_id)
            assert isinstance(cancel_result, dict)
