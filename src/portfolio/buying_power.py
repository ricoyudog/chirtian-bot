"""Conservative buying power calculator with safety margins."""

from src.config.settings import SizingConfig
from src.portfolio.models import PortfolioSnapshot, Quote


class BuyingPowerCalculator:
    """Calculate conservative available buying power.

    Applies a buffer to raw buying power and a slippage buffer to
    estimated price, ensuring the sizing engine never over-commits.
    """

    def calculate_available(
        self,
        snapshot: PortfolioSnapshot,
        config: SizingConfig,
    ) -> float:
        """Return the maximum spendable amount after safety margins.

        available = buying_power × buying_power_buffer
        """
        return snapshot.buying_power_usd * config.buying_power_buffer

    def effective_price(
        self,
        quote: Quote,
        config: SizingConfig,
    ) -> float:
        """Return the price with slippage buffer applied.

        effective_price = quote.price × (1 + slippage_buffer / 100)
        """
        slippage_factor = 1 + config.price_slippage_buffer_pct / 100
        return quote.price * slippage_factor

    def max_shares(
        self,
        available: float,
        effective_price: float,
        lot_size: int = 1,
    ) -> int:
        """Return the maximum whole-lot shares affordable.

        floor(available / effective_price / lot_size) × lot_size
        """
        if effective_price <= 0:
            return 0
        return int(available / effective_price / lot_size) * lot_size
