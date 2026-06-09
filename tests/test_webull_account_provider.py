"""Tests for WebullAccountProvider — mock adapter, source distinction, error propagation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.executor.exceptions import BrokerAuthError, BrokerError, BrokerTimeoutError
from src.executor.webull_adapter import WebullCLIAdapter
from src.portfolio.models import OpenOrder, Position
from src.portfolio.provider import WebullAccountProvider

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_adapter() -> MagicMock:
    """Create a mock WebullCLIAdapter with default return values."""
    adapter = MagicMock(spec=WebullCLIAdapter)
    adapter.get_balance.return_value = {
        "equity": 50000.0,
        "buying_power": 10000.0,
    }
    adapter.get_positions.return_value = [
        {
            "symbol": "AAPL",
            "quantity": 10,
            "avg_cost": 150.0,
            "market_value": 1500.0,
        },
        {
            "symbol": "NVDA",
            "quantity": 5,
            "avg_cost": 170.0,
            "market_value_usd": 850.0,
        },
    ]
    adapter.get_open_orders.return_value = [
        {
            "order_id": "ORD001",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 10,
            "order_type": "LIMIT",
            "limit_price": 180.0,
            "status": "pending",
        },
    ]
    adapter.get_stock_snapshot.return_value = {
        "symbol": "AAPL",
        "price": 150.0,
        "ask": 150.5,
        "bid": 149.5,
    }
    return adapter


def _make_provider(adapter: MagicMock | None = None) -> WebullAccountProvider:
    return WebullAccountProvider(adapter or _mock_adapter())


# ===========================================================================
# get_snapshot
# ===========================================================================


class TestGetSnapshot:
    def test_returns_snapshot_with_webull_source(self):
        provider = _make_provider()
        snapshot = provider.get_snapshot("ACC001")
        assert snapshot.source == "webull"

    def test_maps_balance_fields(self):
        provider = _make_provider()
        snapshot = provider.get_snapshot("ACC001")
        assert snapshot.equity_usd == 50000.0
        assert snapshot.buying_power_usd == 10000.0

    def test_maps_positions(self):
        provider = _make_provider()
        snapshot = provider.get_snapshot("ACC001")
        assert len(snapshot.positions) == 2
        assert snapshot.positions[0].symbol == "AAPL"
        assert snapshot.positions[0].quantity == 10
        assert snapshot.positions[0].avg_cost == 150.0
        assert snapshot.positions[0].market_value_usd == 1500.0

    def test_maps_positions_with_market_value_usd_key(self):
        """Provider handles both 'market_value' and 'market_value_usd' keys."""
        adapter = _mock_adapter()
        adapter.get_positions.return_value = [
            {"symbol": "TSLA", "quantity": 3, "avg_cost": 200.0, "market_value_usd": 600.0},
        ]
        provider = _make_provider(adapter)
        snapshot = provider.get_snapshot("ACC001")
        assert snapshot.positions[0].market_value_usd == 600.0

    def test_maps_open_orders(self):
        provider = _make_provider()
        snapshot = provider.get_snapshot("ACC001")
        assert len(snapshot.open_orders) == 1
        order = snapshot.open_orders[0]
        assert order.order_id == "ORD001"
        assert order.symbol == "AAPL"
        assert order.side == "BUY"
        assert order.quantity == 10
        assert order.order_type == "LIMIT"
        assert order.limit_price == 180.0
        assert order.status == "pending"

    def test_passes_account_id(self):
        adapter = _mock_adapter()
        provider = _make_provider(adapter)
        provider.get_snapshot("MY_ACC")
        adapter.get_balance.assert_called_once_with("MY_ACC")
        adapter.get_positions.assert_called_once_with("MY_ACC")
        adapter.get_open_orders.assert_called_once_with("MY_ACC")

    def test_empty_positions_and_orders(self):
        adapter = _mock_adapter()
        adapter.get_positions.return_value = []
        adapter.get_open_orders.return_value = []
        provider = _make_provider(adapter)
        snapshot = provider.get_snapshot("ACC001")
        assert snapshot.positions == []
        assert snapshot.open_orders == []

    def test_snapshot_account_id_preserved(self):
        provider = _make_provider()
        snapshot = provider.get_snapshot("ACC_XYZ")
        assert snapshot.account_id == "ACC_XYZ"


# ===========================================================================
# get_quote
# ===========================================================================


class TestGetQuote:
    def test_returns_quote_with_symbol(self):
        provider = _make_provider()
        quote = provider.get_quote("AAPL")
        assert quote.symbol == "AAPL"
        assert quote.price == 150.0

    def test_maps_ask_and_bid(self):
        provider = _make_provider()
        quote = provider.get_quote("AAPL")
        assert quote.ask == 150.5
        assert quote.bid == 149.5

    def test_handles_missing_ask_bid(self):
        adapter = _mock_adapter()
        adapter.get_stock_snapshot.return_value = {
            "symbol": "AAPL",
            "price": 150.0,
        }
        provider = _make_provider(adapter)
        quote = provider.get_quote("AAPL")
        assert quote.ask is None
        assert quote.bid is None

    def test_handles_null_ask_bid(self):
        """API returns null values for ask/bid — should return None, not TypeError."""
        adapter = _mock_adapter()
        adapter.get_stock_snapshot.return_value = {
            "symbol": "AAPL",
            "price": 150.0,
            "ask": None,
            "bid": None,
        }
        provider = _make_provider(adapter)
        quote = provider.get_quote("AAPL")
        assert quote.price == 150.0
        assert quote.ask is None
        assert quote.bid is None

    def test_passes_symbol_to_adapter(self):
        adapter = _mock_adapter()
        provider = _make_provider(adapter)
        provider.get_quote("NVDA")
        adapter.get_stock_snapshot.assert_called_once_with("NVDA")


# ===========================================================================
# get_positions
# ===========================================================================


class TestGetPositions:
    def test_returns_position_models(self):
        provider = _make_provider()
        positions = provider.get_positions("ACC001")
        assert len(positions) == 2
        assert all(isinstance(p, Position) for p in positions)

    def test_maps_all_fields(self):
        provider = _make_provider()
        positions = provider.get_positions("ACC001")
        nvda = positions[1]
        assert nvda.symbol == "NVDA"
        assert nvda.quantity == 5
        assert nvda.avg_cost == 170.0
        assert nvda.market_value_usd == 850.0

    def test_empty_list(self):
        adapter = _mock_adapter()
        adapter.get_positions.return_value = []
        provider = _make_provider(adapter)
        assert provider.get_positions("ACC001") == []


# ===========================================================================
# get_open_orders
# ===========================================================================


class TestGetOpenOrders:
    def test_returns_open_order_models(self):
        provider = _make_provider()
        orders = provider.get_open_orders("ACC001")
        assert len(orders) == 1
        assert all(isinstance(o, OpenOrder) for o in orders)

    def test_maps_all_fields(self):
        provider = _make_provider()
        orders = provider.get_open_orders("ACC001")
        o = orders[0]
        assert o.order_id == "ORD001"
        assert o.symbol == "AAPL"
        assert o.side == "BUY"
        assert o.quantity == 10
        assert o.order_type == "LIMIT"
        assert o.limit_price == 180.0
        assert o.status == "pending"

    def test_handles_null_limit_price(self):
        adapter = _mock_adapter()
        adapter.get_open_orders.return_value = [
            {
                "order_id": "ORD002",
                "symbol": "TSLA",
                "side": "SELL",
                "quantity": 5,
                "order_type": "MARKET",
                "status": "pending",
            },
        ]
        provider = _make_provider(adapter)
        orders = provider.get_open_orders("ACC001")
        assert orders[0].limit_price is None
        assert orders[0].order_type == "MARKET"

    def test_empty_list(self):
        adapter = _mock_adapter()
        adapter.get_open_orders.return_value = []
        provider = _make_provider(adapter)
        assert provider.get_open_orders("ACC001") == []


# ===========================================================================
# Error propagation — no fallback to fake data
# ===========================================================================


class TestErrorPropagation:
    def test_timeout_propagates(self):
        adapter = _mock_adapter()
        adapter.get_balance.side_effect = BrokerTimeoutError("timeout")
        provider = _make_provider(adapter)
        with pytest.raises(BrokerTimeoutError, match="timeout"):
            provider.get_snapshot("ACC001")

    def test_auth_error_propagates(self):
        adapter = _mock_adapter()
        adapter.get_balance.side_effect = BrokerAuthError("unauthorized")
        provider = _make_provider(adapter)
        with pytest.raises(BrokerAuthError, match="unauthorized"):
            provider.get_snapshot("ACC001")

    def test_broker_error_propagates(self):
        adapter = _mock_adapter()
        adapter.get_positions.side_effect = BrokerError("CLI error")
        provider = _make_provider(adapter)
        with pytest.raises(BrokerError, match="CLI error"):
            provider.get_positions("ACC001")

    def test_quote_timeout_propagates(self):
        adapter = _mock_adapter()
        adapter.get_stock_snapshot.side_effect = BrokerTimeoutError("timeout")
        provider = _make_provider(adapter)
        with pytest.raises(BrokerTimeoutError):
            provider.get_quote("AAPL")

    def test_orders_auth_error_propagates(self):
        adapter = _mock_adapter()
        adapter.get_open_orders.side_effect = BrokerAuthError("auth failed")
        provider = _make_provider(adapter)
        with pytest.raises(BrokerAuthError, match="auth failed"):
            provider.get_open_orders("ACC001")

    def test_snapshot_partial_failure_no_fallback(self):
        """If positions call fails but balance succeeds, entire snapshot fails."""
        adapter = _mock_adapter()
        adapter.get_positions.side_effect = BrokerError("position error")
        provider = _make_provider(adapter)
        with pytest.raises(BrokerError, match="position error"):
            provider.get_snapshot("ACC001")
