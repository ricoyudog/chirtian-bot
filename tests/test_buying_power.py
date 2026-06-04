"""Tests for BuyingPowerCalculator."""

from src.config.settings import SizingConfig
from src.portfolio.buying_power import BuyingPowerCalculator
from src.portfolio.models import PortfolioSnapshot, Quote


def _snapshot(buying_power: float, equity: float = 50000.0) -> PortfolioSnapshot:
    return PortfolioSnapshot(account_id="TEST", equity_usd=equity, buying_power_usd=buying_power)


def _config(**overrides) -> SizingConfig:
    defaults = dict(buying_power_buffer=0.98, price_slippage_buffer_pct=0.5)
    defaults.update(overrides)
    return SizingConfig(**defaults)


class TestCalculateAvailable:
    def test_normal_buying_power_with_buffer(self):
        calc = BuyingPowerCalculator()
        snap = _snapshot(buying_power=10000.0)
        config = _config(buying_power_buffer=0.98)
        available = calc.calculate_available(snap, config)
        assert available == pytest.approx(9800.0)

    def test_zero_buying_power(self):
        calc = BuyingPowerCalculator()
        snap = _snapshot(buying_power=0.0)
        config = _config()
        assert calc.calculate_available(snap, config) == 0.0

    def test_small_buying_power(self):
        calc = BuyingPowerCalculator()
        snap = _snapshot(buying_power=50.0)
        config = _config(buying_power_buffer=0.98)
        available = calc.calculate_available(snap, config)
        assert available == pytest.approx(49.0)

    def test_custom_buffer(self):
        calc = BuyingPowerCalculator()
        snap = _snapshot(buying_power=10000.0)
        config = _config(buying_power_buffer=0.95)
        available = calc.calculate_available(snap, config)
        assert available == pytest.approx(9500.0)


class TestEffectivePrice:
    def test_slippage_buffer_applied(self):
        calc = BuyingPowerCalculator()
        quote = Quote(symbol="NVDA", price=180.0)
        config = _config(price_slippage_buffer_pct=0.5)
        ep = calc.effective_price(quote, config)
        assert ep == pytest.approx(180.9)  # 180 * 1.005

    def test_zero_slippage(self):
        calc = BuyingPowerCalculator()
        quote = Quote(symbol="NVDA", price=180.0)
        config = _config(price_slippage_buffer_pct=0.0)
        assert calc.effective_price(quote, config) == 180.0

    def test_large_slippage(self):
        calc = BuyingPowerCalculator()
        quote = Quote(symbol="NVDA", price=100.0)
        config = _config(price_slippage_buffer_pct=1.0)
        assert calc.effective_price(quote, config) == pytest.approx(101.0)


class TestMaxShares:
    def test_normal(self):
        calc = BuyingPowerCalculator()
        shares = calc.max_shares(available=9800.0, effective_price=180.9, lot_size=1)
        assert shares == 54  # floor(9800 / 180.9) = 54

    def test_insufficient_for_one_share(self):
        calc = BuyingPowerCalculator()
        shares = calc.max_shares(available=50.0, effective_price=180.9, lot_size=1)
        assert shares == 0

    def test_lot_size_100(self):
        calc = BuyingPowerCalculator()
        shares = calc.max_shares(available=9800.0, effective_price=10.0, lot_size=100)
        assert shares == 900  # floor(9800/10/100)*100 = 900

    def test_zero_price(self):
        calc = BuyingPowerCalculator()
        shares = calc.max_shares(available=9800.0, effective_price=0.0)
        assert shares == 0


import pytest  # noqa: E402 — needed at bottom to avoid ruff import ordering
