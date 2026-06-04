"""Account data provider protocol and fake implementation for testing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from src.portfolio.models import (
    OpenOrder,
    PortfolioSnapshot,
    Position,
    Quote,
)


class AccountDataProvider(Protocol):
    """Protocol for fetching account data from a broker.

    Phase 3 uses FakeAccountProvider. Phase 4 implements WebullAccountProvider.
    """

    def get_snapshot(self, account_id: str) -> PortfolioSnapshot: ...
    def get_quote(self, symbol: str) -> Quote: ...
    def get_positions(self, account_id: str) -> list[Position]: ...
    def get_open_orders(self, account_id: str) -> list[OpenOrder]: ...


def _default_positions() -> list[Position]:
    return [
        Position(symbol="AAPL", quantity=10, avg_cost=150.0, market_value_usd=1500.0),
        Position(symbol="NVDA", quantity=5, avg_cost=170.0, market_value_usd=850.0),
        Position(symbol="TSLA", quantity=8, avg_cost=250.0, market_value_usd=2000.0),
        Position(symbol="MSFT", quantity=4, avg_cost=400.0, market_value_usd=1600.0),
        Position(symbol="AMZN", quantity=3, avg_cost=180.0, market_value_usd=540.0),
    ]


def _default_quotes() -> dict[str, Quote]:
    now = datetime.now(UTC).isoformat()
    return {
        "AAPL": Quote(symbol="AAPL", price=150.0, ask=150.5, bid=149.5, timestamp=now),
        "NVDA": Quote(symbol="NVDA", price=180.0, ask=180.5, bid=179.5, timestamp=now),
        "TSLA": Quote(symbol="TSLA", price=250.0, ask=250.5, bid=249.5, timestamp=now),
        "MSFT": Quote(symbol="MSFT", price=400.0, ask=400.5, bid=399.5, timestamp=now),
        "AMZN": Quote(symbol="AMZN", price=180.0, ask=180.5, bid=179.5, timestamp=now),
    }


class FakeAccountProvider:
    """Fake account data provider for testing.

    Pre-configured with sensible defaults. Override via constructor args
    or setter methods for specific test scenarios.
    """

    def __init__(
        self,
        *,
        equity_usd: float = 50000.0,
        buying_power_usd: float = 10000.0,
        positions: list[Position] | None = None,
        open_orders: list[OpenOrder] | None = None,
        quotes: dict[str, Quote] | None = None,
        account_id: str = "TEST001",
    ):
        self._account_id = account_id
        self._equity_usd = equity_usd
        self._buying_power_usd = buying_power_usd
        self._positions = positions if positions is not None else _default_positions()
        self._open_orders = open_orders if open_orders is not None else []
        self._quotes = quotes if quotes is not None else _default_quotes()

    # -- Protocol methods --

    def get_snapshot(self, account_id: str) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            account_id=account_id,
            equity_usd=self._equity_usd,
            buying_power_usd=self._buying_power_usd,
            positions=self._positions,
            open_orders=self._open_orders,
            source="fake",
        )

    def get_quote(self, symbol: str) -> Quote:
        symbol_upper = symbol.upper()
        if symbol_upper in self._quotes:
            return self._quotes[symbol_upper]
        raise ValueError(f"No quote available for symbol: {symbol}")

    def get_positions(self, account_id: str) -> list[Position]:
        return list(self._positions)

    def get_open_orders(self, account_id: str) -> list[OpenOrder]:
        return list(self._open_orders)

    # -- Override methods for test scenarios --

    def set_equity(self, value: float) -> None:
        self._equity_usd = value

    def set_buying_power(self, value: float) -> None:
        self._buying_power_usd = value

    def set_positions(self, positions: list[Position]) -> None:
        self._positions = positions

    def add_position(self, position: Position) -> None:
        self._positions.append(position)

    def remove_position(self, symbol: str) -> None:
        symbol_upper = symbol.upper()
        self._positions = [p for p in self._positions if p.symbol.upper() != symbol_upper]

    def set_open_orders(self, orders: list[OpenOrder]) -> None:
        self._open_orders = orders

    def add_open_order(self, order: OpenOrder) -> None:
        self._open_orders.append(order)

    def set_quote(self, symbol: str, quote: Quote) -> None:
        self._quotes[symbol.upper()] = quote
