"""Decision fusion — combine Christian instruction with TradingAgents rating."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.analyzer.ta_models import TAResult

BULLISH_RATINGS = frozenset({"Buy", "Overweight"})
NEUTRAL_RATING = frozenset({"Hold"})
BEARISH_RATINGS = frozenset({"Underweight", "Sell"})
VALID_RATINGS = BULLISH_RATINGS | NEUTRAL_RATING | BEARISH_RATINGS

FUSION_APPROVE = "APPROVE"
FUSION_MODIFY = "MODIFY"
FUSION_REJECT = "REJECT"
FUSION_NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass
class FusionDecision:
    instruction_id: str
    symbol: str
    christian_action: str
    fusion_status: str
    ta_rating: Optional[str] = None
    ta_available: bool = False
    reason: str = ""
    suggested_quantity_pct: Optional[float] = None
    original_quantity_pct: Optional[float] = None

    MODIFY_FACTOR = 0.5


def fuse(
    christian_action: str,
    symbol: str,
    instruction_id: str,
    quantity_pct: float,
    ta_result: TAResult,
    reject_on_opposition: bool = False,
) -> FusionDecision:
    """Fuse Christian instruction with TradingAgents rating.

    Fail-closed: TA unavailable always results in NEEDS_REVIEW.
    """
    if not ta_result.available:
        return FusionDecision(
            instruction_id=instruction_id,
            symbol=symbol,
            christian_action=christian_action,
            fusion_status=FUSION_NEEDS_REVIEW,
            ta_rating=None,
            ta_available=False,
            reason="TA_UNAVAILABLE",
            suggested_quantity_pct=None,
            original_quantity_pct=quantity_pct,
        )

    rating = ta_result.rating

    if rating not in VALID_RATINGS:
        return FusionDecision(
            instruction_id=instruction_id,
            symbol=symbol,
            christian_action=christian_action,
            fusion_status=FUSION_NEEDS_REVIEW,
            ta_rating=rating,
            ta_available=True,
            reason=f"TA_UNKNOWN_RATING:{rating}",
            suggested_quantity_pct=None,
            original_quantity_pct=quantity_pct,
        )

    if christian_action == "BUY":
        if rating in BULLISH_RATINGS:
            return _approve(instruction_id, symbol, "BUY", rating, quantity_pct)
        if rating in NEUTRAL_RATING:
            return _modify(instruction_id, symbol, "BUY", rating, quantity_pct, "TA_HOLD_REDUCE")
        if rating in BEARISH_RATINGS:
            return _reject(
                instruction_id, symbol, "BUY", rating, "TA_OPPOSES_BUY", reject_on_opposition,
            )

    elif christian_action == "SELL":
        if rating in BEARISH_RATINGS:
            return _approve(instruction_id, symbol, "SELL", rating, quantity_pct)
        if rating in NEUTRAL_RATING:
            return _approve(instruction_id, symbol, "SELL", rating, quantity_pct)
        if rating in BULLISH_RATINGS:
            return _modify(instruction_id, symbol, "SELL", rating, quantity_pct, "TA_BULLISH_HOLD")

    return FusionDecision(
        instruction_id=instruction_id,
        symbol=symbol,
        christian_action=christian_action,
        fusion_status=FUSION_NEEDS_REVIEW,
        ta_rating=rating,
        ta_available=True,
        reason="UNHANDLED_ACTION",
        suggested_quantity_pct=None,
        original_quantity_pct=quantity_pct,
    )


def _approve(instruction_id, symbol, action, rating, quantity_pct):
    return FusionDecision(
        instruction_id=instruction_id,
        symbol=symbol,
        christian_action=action,
        fusion_status=FUSION_APPROVE,
        ta_rating=rating,
        ta_available=True,
        reason="AGREEMENT",
        suggested_quantity_pct=quantity_pct,
        original_quantity_pct=quantity_pct,
    )


def _modify(instruction_id, symbol, action, rating, quantity_pct, reason):
    return FusionDecision(
        instruction_id=instruction_id,
        symbol=symbol,
        christian_action=action,
        fusion_status=FUSION_MODIFY,
        ta_rating=rating,
        ta_available=True,
        reason=reason,
        suggested_quantity_pct=quantity_pct * FusionDecision.MODIFY_FACTOR,
        original_quantity_pct=quantity_pct,
    )


def _reject(instruction_id, symbol, action, rating, reason, reject_on_opposition):
    status = FUSION_REJECT if reject_on_opposition else FUSION_NEEDS_REVIEW
    return FusionDecision(
        instruction_id=instruction_id,
        symbol=symbol,
        christian_action=action,
        fusion_status=status,
        ta_rating=rating,
        ta_available=True,
        reason=reason,
        suggested_quantity_pct=None,
        original_quantity_pct=None,
    )
