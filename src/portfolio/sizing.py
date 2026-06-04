"""SizingEngine — convert quantity_pct to executable order_quantity."""

from __future__ import annotations

from datetime import UTC, datetime

from src.analyzer.parser_schema import ParsedInstruction
from src.config.settings import RiskConfig, SizingConfig
from src.portfolio.buying_power import BuyingPowerCalculator
from src.portfolio.ledger import PortfolioLedger
from src.portfolio.models import (
    PortfolioSnapshot,
    Quote,
    SizingDecision,
)

# Reason code constants
SKIP_TOO_SMALL = "SKIP_TOO_SMALL"
SKIP_INSUFFICIENT_BUYING_POWER = "SKIP_INSUFFICIENT_BUYING_POWER"
SKIP_LOT_SIZE = "SKIP_LOT_SIZE"
SKIP_NO_POSITION = "SKIP_NO_POSITION"
SKIP_STALE_QUOTE = "SKIP_STALE_QUOTE"
OPEN_ORDER_CONFLICT = "OPEN_ORDER_CONFLICT"
CLAMPED_BUYING_POWER = "CLAMPED_BUYING_POWER"
CLAMPED_CONCENTRATION = "CLAMPED_CONCENTRATION"
CLAMPED_MAX_NOTIONAL = "CLAMPED_MAX_NOTIONAL"
ROUNDED_DOWN_TO_LOT_SIZE = "ROUNDED_DOWN_TO_LOT_SIZE"

# Stale quote threshold (minutes)
STALE_QUOTE_MINUTES = 15


class SizingEngine:
    """Convert quantity_pct to executable order_quantity.

    Buy path (D3): target_notional → chain clamp → floor → EXECUTABLE or SKIP
    Sell path (D4): target_quantity → floor → clip → EXECUTABLE or SKIP
    """

    def __init__(
        self,
        risk_config: RiskConfig,
        sizing_config: SizingConfig,
        ledger: PortfolioLedger | None = None,
    ):
        self._risk = risk_config
        self._sizing = sizing_config
        self._ledger = ledger
        self._bp_calc = BuyingPowerCalculator()

    def size(
        self,
        instruction: ParsedInstruction,
        snapshot: PortfolioSnapshot,
        quote: Quote,
        lot_size: int = 1,
        min_quantity: int = 1,
    ) -> SizingDecision:
        """Size an instruction into an executable SizingDecision.

        This is the main entry point. It dispatches to buy or sell path
        based on the instruction action.
        """
        # Pre-checks common to both paths
        stale_reason = self._check_stale_quote(quote)
        if stale_reason:
            return self._make_skip(
                instruction, snapshot, quote, stale_reason, lot_size, min_quantity
            )

        conflict_reason = self._check_open_order_conflict(instruction, snapshot)
        if conflict_reason:
            return self._make_review(
                instruction, snapshot, quote, conflict_reason, lot_size, min_quantity
            )

        if instruction.action in ("BUY", "SHORT"):
            decision = self._size_buy(instruction, snapshot, quote, lot_size, min_quantity)
        else:
            decision = self._size_sell(instruction, snapshot, quote, lot_size, min_quantity)

        # Write to ledger
        if self._ledger is not None:
            self._ledger.append(
                "sizing_decision",
                {
                    "instruction_id": decision.instruction_id,
                    "symbol": decision.symbol,
                    "action": decision.action,
                    "sizing_status": decision.sizing_status,
                    "order_quantity": decision.order_quantity,
                    "reason_codes": decision.reason_codes,
                },
                correlation_id=decision.instruction_id,
            )

        return decision

    # ------------------------------------------------------------------
    # Buy path (D3)
    # ------------------------------------------------------------------

    def _size_buy(
        self,
        instruction: ParsedInstruction,
        snapshot: PortfolioSnapshot,
        quote: Quote,
        lot_size: int,
        min_quantity: int,
    ) -> SizingDecision:
        pct = instruction.quantity_pct if instruction.quantity_pct is not None else 0.0
        target_notional = pct / 100 * snapshot.equity_usd
        effective_price = self._bp_calc.effective_price(quote, self._sizing)

        # Chain clamp (D5 — record ALL reason codes)
        reason_codes: list[str] = []
        capped = target_notional

        # Clamp 1: buying power
        available = self._bp_calc.calculate_available(snapshot, self._sizing)
        if capped > available:
            capped = available
            reason_codes.append(CLAMPED_BUYING_POWER)

        # Clamp 2: concentration cap
        concentration_remaining = self._concentration_remaining(instruction.symbol, snapshot)
        if capped > concentration_remaining:
            capped = concentration_remaining
            reason_codes.append(CLAMPED_CONCENTRATION)

        # Clamp 3: max notional
        if capped > self._risk.max_notional_usd:
            capped = self._risk.max_notional_usd
            reason_codes.append(CLAMPED_MAX_NOTIONAL)

        # Floor to lot size
        raw_qty = 0.0
        if effective_price > 0 and capped > 0:
            raw_qty = capped / effective_price
            order_quantity = max(0, int(raw_qty / lot_size) * lot_size)
        else:
            order_quantity = 0

        if order_quantity > 0 and order_quantity < raw_qty:
            reason_codes.append(ROUNDED_DOWN_TO_LOT_SIZE)

        # Skip if too small
        sizing_status = "EXECUTABLE"
        if order_quantity < min_quantity:
            if capped < target_notional:
                sizing_status = "SKIP_INSUFFICIENT_BUYING_POWER"
            elif lot_size > 1 and raw_qty < lot_size:
                sizing_status = "SKIP_LOT_SIZE"
            else:
                sizing_status = "SKIP_TOO_SMALL"
            reason_codes.append(sizing_status)
            order_quantity = 0
        elif capped < target_notional:
            sizing_status = "MODIFY_SIZE"

        order_notional = order_quantity * effective_price
        residual = max(0, capped - order_notional)

        return SizingDecision(
            instruction_id=instruction.instruction_id,
            symbol=instruction.symbol,
            action="BUY",
            sizing_status=sizing_status,
            portfolio_equity_usd=snapshot.equity_usd,
            available_buying_power_usd=available,
            target_pct=pct,
            target_notional_usd=target_notional,
            capped_notional_usd=capped,
            estimated_price=effective_price,
            lot_size=lot_size,
            min_quantity=min_quantity,
            order_quantity=order_quantity,
            estimated_order_notional_usd=order_notional,
            unfilled_residual_usd=residual,
            reason_codes=reason_codes,
        )

    # ------------------------------------------------------------------
    # Sell path (D4)
    # ------------------------------------------------------------------

    def _size_sell(
        self,
        instruction: ParsedInstruction,
        snapshot: PortfolioSnapshot,
        quote: Quote,
        lot_size: int,
        min_quantity: int,
    ) -> SizingDecision:
        effective_price = self._bp_calc.effective_price(quote, self._sizing)
        available = self._bp_calc.calculate_available(snapshot, self._sizing)

        # Find position
        position = snapshot.get_position(instruction.symbol)
        if position is None or position.quantity == 0:
            return SizingDecision(
                instruction_id=instruction.instruction_id,
                symbol=instruction.symbol,
                action="SELL",
                sizing_status="SKIP_NO_POSITION",
                portfolio_equity_usd=snapshot.equity_usd,
                available_buying_power_usd=available,
                estimated_price=effective_price,
                lot_size=lot_size,
                min_quantity=min_quantity,
                order_quantity=0,
                estimated_order_notional_usd=0,
                unfilled_residual_usd=0,
                reason_codes=[SKIP_NO_POSITION],
            )

        # Calculate target quantity
        if instruction.quantity_type == "all":
            target_quantity = float(position.quantity)
        else:
            pct = instruction.quantity_pct if instruction.quantity_pct is not None else 0.0
            target_quantity = pct / 100 * position.quantity

        # Floor to lot size
        reason_codes: list[str] = []
        order_quantity = max(0, int(target_quantity / lot_size) * lot_size)

        # Clip to available position
        if order_quantity > position.quantity:
            order_quantity = position.quantity

        if order_quantity < target_quantity:
            reason_codes.append(ROUNDED_DOWN_TO_LOT_SIZE)

        # Skip if too small
        sizing_status = "EXECUTABLE"
        if order_quantity < min_quantity:
            sizing_status = "SKIP_TOO_SMALL"
            reason_codes.append(sizing_status)
            order_quantity = 0

        order_notional = order_quantity * effective_price

        return SizingDecision(
            instruction_id=instruction.instruction_id,
            symbol=instruction.symbol,
            action="SELL",
            sizing_status=sizing_status,
            portfolio_equity_usd=snapshot.equity_usd,
            available_buying_power_usd=available,
            target_pct=instruction.quantity_pct,
            target_quantity=target_quantity,
            estimated_price=effective_price,
            lot_size=lot_size,
            min_quantity=min_quantity,
            order_quantity=order_quantity,
            estimated_order_notional_usd=order_notional,
            unfilled_residual_usd=0,
            reason_codes=reason_codes,
        )

    # ------------------------------------------------------------------
    # Pre-checks
    # ------------------------------------------------------------------

    def _check_stale_quote(self, quote: Quote) -> str | None:
        """Return reason code if quote is stale, else None."""
        try:
            quote_time = datetime.fromisoformat(quote.timestamp)
            now = datetime.now(UTC)
            age_minutes = (now - quote_time).total_seconds() / 60
            if age_minutes > STALE_QUOTE_MINUTES:
                return SKIP_STALE_QUOTE
        except (ValueError, TypeError):
            return SKIP_STALE_QUOTE
        return None

    def _check_open_order_conflict(
        self, instruction: ParsedInstruction, snapshot: PortfolioSnapshot
    ) -> str | None:
        """Return reason code if same symbol has open order, else None."""
        if snapshot.has_open_order(instruction.symbol):
            return OPEN_ORDER_CONFLICT
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _concentration_remaining(self, symbol: str, snapshot: PortfolioSnapshot) -> float:
        """How much more notional can we add to this symbol."""
        current_exposure = 0.0
        for pos in snapshot.positions:
            if pos.symbol.upper() == symbol.upper():
                current_exposure += pos.market_value_usd

        if snapshot.equity_usd == 0:
            return 0.0

        current_pct = current_exposure / snapshot.equity_usd * 100
        remaining_pct = max(0, self._risk.max_concentration_pct - current_pct)
        return remaining_pct / 100 * snapshot.equity_usd

    def _make_skip(
        self,
        instruction: ParsedInstruction,
        snapshot: PortfolioSnapshot,
        quote: Quote,
        reason: str,
        lot_size: int,
        min_quantity: int,
    ) -> SizingDecision:
        effective_price = self._bp_calc.effective_price(quote, self._sizing)
        return SizingDecision(
            instruction_id=instruction.instruction_id,
            symbol=instruction.symbol,
            action="BUY" if instruction.action in ("BUY", "SHORT") else "SELL",
            sizing_status="SKIP_STALE_QUOTE",
            portfolio_equity_usd=snapshot.equity_usd,
            available_buying_power_usd=snapshot.buying_power_usd,
            target_pct=instruction.quantity_pct,
            estimated_price=effective_price,
            lot_size=lot_size,
            min_quantity=min_quantity,
            order_quantity=0,
            estimated_order_notional_usd=0,
            unfilled_residual_usd=0,
            reason_codes=[reason],
        )

    def _make_review(
        self,
        instruction: ParsedInstruction,
        snapshot: PortfolioSnapshot,
        quote: Quote,
        reason: str,
        lot_size: int,
        min_quantity: int,
    ) -> SizingDecision:
        effective_price = self._bp_calc.effective_price(quote, self._sizing)
        return SizingDecision(
            instruction_id=instruction.instruction_id,
            symbol=instruction.symbol,
            action="BUY" if instruction.action in ("BUY", "SHORT") else "SELL",
            sizing_status="SIZING_NEEDS_REVIEW",
            portfolio_equity_usd=snapshot.equity_usd,
            available_buying_power_usd=snapshot.buying_power_usd,
            target_pct=instruction.quantity_pct,
            estimated_price=effective_price,
            lot_size=lot_size,
            min_quantity=min_quantity,
            order_quantity=0,
            estimated_order_notional_usd=0,
            unfilled_residual_usd=0,
            reason_codes=[reason],
        )
