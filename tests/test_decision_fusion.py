"""Tests for decision fusion logic."""

import pytest

from src.analyzer.decision_fusion import (
    TAResult,
    FusionDecision,
    fuse,
    FUSION_APPROVE,
    FUSION_MODIFY,
    FUSION_REJECT,
    FUSION_NEEDS_REVIEW,
)


def _ta(rating=None, available=True, error=None):
    return TAResult(ticker="TEST", rating=rating, available=available, error=error)


class TestTAFailClosed:
    def test_ta_unavailable_needs_review(self):
        result = fuse("BUY", "AAPL", "i1", 1.0, _ta(available=False, error="timeout"))
        assert result.fusion_status == FUSION_NEEDS_REVIEW
        assert result.reason == "TA_UNAVAILABLE"
        assert result.ta_available is False

    def test_ta_error_needs_review(self):
        result = fuse("SELL", "TSLA", "i2", 2.0, _ta(available=False, error="crash"))
        assert result.fusion_status == FUSION_NEEDS_REVIEW
        assert result.ta_available is False

    def test_ta_unknown_rating_needs_review(self):
        result = fuse("BUY", "AAPL", "i3", 1.0, _ta(rating="Unknown", available=True))
        assert result.fusion_status == FUSION_NEEDS_REVIEW
        assert result.reason.startswith("TA_UNKNOWN_RATING")


class TestBuyAction:
    def test_buy_ta_buy_approves(self):
        for rating in ["Buy", "Overweight"]:
            result = fuse("BUY", "AAPL", "i1", 1.0, _ta(rating=rating))
            assert result.fusion_status == FUSION_APPROVE, f"Expected APPROVE for {rating}"
            assert result.suggested_quantity_pct == 1.0

    def test_buy_ta_hold_modifies(self):
        result = fuse("BUY", "AAPL", "i1", 1.0, _ta(rating="Hold"))
        assert result.fusion_status == FUSION_MODIFY
        assert result.suggested_quantity_pct == 0.5
        assert result.original_quantity_pct == 1.0

    def test_buy_ta_sell_rejects(self):
        for rating in ["Underweight", "Sell"]:
            result = fuse("BUY", "AAPL", "i1", 1.0, _ta(rating=rating), reject_on_opposition=True)
            assert result.fusion_status == FUSION_REJECT, f"Expected REJECT for {rating}"

    def test_buy_ta_sell_needs_review_by_default(self):
        result = fuse("BUY", "AAPL", "i1", 1.0, _ta(rating="Sell"))
        assert result.fusion_status == FUSION_NEEDS_REVIEW


class TestSellAction:
    def test_sell_ta_sell_approves(self):
        for rating in ["Underweight", "Sell"]:
            result = fuse("SELL", "TSLA", "i1", 1.0, _ta(rating=rating))
            assert result.fusion_status == FUSION_APPROVE, f"Expected APPROVE for {rating}"

    def test_sell_ta_hold_approves(self):
        result = fuse("SELL", "TSLA", "i1", 1.0, _ta(rating="Hold"))
        assert result.fusion_status == FUSION_APPROVE

    def test_sell_ta_buy_modifies(self):
        for rating in ["Buy", "Overweight"]:
            result = fuse("SELL", "TSLA", "i1", 1.0, _ta(rating=rating))
            assert result.fusion_status == FUSION_MODIFY, f"Expected MODIFY for {rating}"
            assert result.suggested_quantity_pct == 0.5


class TestQuantityModification:
    def test_modify_halves_quantity(self):
        result = fuse("BUY", "AAPL", "i1", 2.0, _ta(rating="Hold"))
        assert result.suggested_quantity_pct == 1.0
        assert result.original_quantity_pct == 2.0

    def test_approve_keeps_original_quantity(self):
        result = fuse("BUY", "AAPL", "i1", 3.0, _ta(rating="Buy"))
        assert result.suggested_quantity_pct == 3.0


class TestRejectOnOpposition:
    def test_default_reject_becomes_needs_review(self):
        result = fuse("BUY", "AAPL", "i1", 1.0, _ta(rating="Sell"), reject_on_opposition=False)
        assert result.fusion_status == FUSION_NEEDS_REVIEW

    def test_reject_on_opposition_true(self):
        result = fuse("BUY", "AAPL", "i1", 1.0, _ta(rating="Sell"), reject_on_opposition=True)
        assert result.fusion_status == FUSION_REJECT


class TestUnhandledAction:
    def test_unknown_action_needs_review(self):
        result = fuse("SHORT", "AAPL", "i1", 1.0, _ta(rating="Buy"))
        assert result.fusion_status == FUSION_NEEDS_REVIEW
        assert result.reason == "UNHANDLED_ACTION"
