"""Tests for AccountDataProvider protocol and FakeAccountProvider."""

from datetime import UTC, datetime, timedelta

import pytest

from src.portfolio.models import OpenOrder, Position, Quote
from src.portfolio.provider import FakeAccountProvider


class TestFakeAccountProviderConstruction:
    def test_default_construction(self):
        provider = FakeAccountProvider()
        snap = provider.get_snapshot("TEST001")
        assert snap.equity_usd == 50000.0
        assert snap.buying_power_usd == 10000.0
        assert len(snap.positions) == 5
        assert len(snap.open_orders) == 0
        assert snap.source == "fake"

    def test_custom_construction(self):
        provider = FakeAccountProvider(
            equity_usd=5000.0,
            buying_power_usd=2000.0,
            positions=[Position(symbol="AAPL", quantity=1, avg_cost=150.0, market_value_usd=150.0)],
            account_id="CUSTOM",
        )
        snap = provider.get_snapshot("CUSTOM")
        assert snap.equity_usd == 5000.0
        assert snap.buying_power_usd == 2000.0
        assert len(snap.positions) == 1

    def test_empty_positions(self):
        provider = FakeAccountProvider(positions=[], buying_power_usd=50000.0)
        snap = provider.get_snapshot("TEST001")
        assert snap.positions == []


class TestFakeAccountProviderGetQuote:
    def test_get_existing_quote(self):
        provider = FakeAccountProvider()
        q = provider.get_quote("NVDA")
        assert q.symbol == "NVDA"
        assert q.price == 180.0

    def test_get_quote_case_insensitive(self):
        provider = FakeAccountProvider()
        q = provider.get_quote("nvda")
        assert q.symbol == "NVDA"

    def test_get_missing_quote_raises(self):
        provider = FakeAccountProvider()
        with pytest.raises(ValueError, match="No quote available"):
            provider.get_quote("UNKNOWN")


class TestFakeAccountProviderOverrides:
    def test_set_equity(self):
        provider = FakeAccountProvider()
        provider.set_equity(100000.0)
        assert provider.get_snapshot("TEST001").equity_usd == 100000.0

    def test_set_buying_power(self):
        provider = FakeAccountProvider()
        provider.set_buying_power(50.0)
        assert provider.get_snapshot("TEST001").buying_power_usd == 50.0

    def test_add_position(self):
        provider = FakeAccountProvider()
        provider.add_position(
            Position(symbol="META", quantity=2, avg_cost=500.0, market_value_usd=1000.0)
        )
        positions = provider.get_positions("TEST001")
        assert any(p.symbol == "META" for p in positions)

    def test_remove_position(self):
        provider = FakeAccountProvider()
        provider.remove_position("AAPL")
        positions = provider.get_positions("TEST001")
        assert not any(p.symbol == "AAPL" for p in positions)

    def test_set_positions(self):
        provider = FakeAccountProvider()
        new_positions = [
            Position(symbol="GOOG", quantity=1, avg_cost=140.0, market_value_usd=140.0)
        ]
        provider.set_positions(new_positions)
        assert len(provider.get_positions("TEST001")) == 1

    def test_add_open_order(self):
        provider = FakeAccountProvider()
        provider.add_open_order(OpenOrder(order_id="ord_1", symbol="AAPL", side="BUY", quantity=2))
        orders = provider.get_open_orders("TEST001")
        assert len(orders) == 1
        assert orders[0].symbol == "AAPL"

    def test_set_open_orders(self):
        provider = FakeAccountProvider()
        provider.set_open_orders(
            [OpenOrder(order_id="ord_1", symbol="NVDA", side="BUY", quantity=3)]
        )
        snap = provider.get_snapshot("TEST001")
        assert snap.has_open_order("NVDA")

    def test_set_quote(self):
        provider = FakeAccountProvider()
        stale_ts = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
        provider.set_quote(
            "AAPL", Quote(symbol="AAPL", price=155.0, ask=155.5, bid=154.5, timestamp=stale_ts)
        )
        q = provider.get_quote("AAPL")
        assert q.price == 155.0


class TestFakeAccountProviderGetSnapshotReturnsFresh:
    def test_snapshot_reflects_latest_overrides(self):
        provider = FakeAccountProvider()
        provider.set_buying_power(500.0)
        provider.add_open_order(OpenOrder(order_id="ord_1", symbol="TSLA", side="SELL", quantity=1))
        snap = provider.get_snapshot("TEST001")
        assert snap.buying_power_usd == 500.0
        assert snap.has_open_order("TSLA")
