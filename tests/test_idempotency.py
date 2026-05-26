"""Tests for idempotency key generation and dedup guard."""

import pytest

from src.safety.idempotency import IdempotencyGuard, generate_idempotency_key
from src.state.queue import DuplicateKeyError, WorkQueue


class TestGenerateIdempotencyKey:
    def test_same_inputs_same_key(self):
        k1 = generate_idempotency_key("post-1", 1, "BUY", "AAPL", 0.25)
        k2 = generate_idempotency_key("post-1", 1, "BUY", "AAPL", 0.25)
        assert k1 == k2
        assert k1.startswith("idem:")

    def test_different_inputs_different_keys(self):
        k1 = generate_idempotency_key("post-1", 1, "BUY", "AAPL", 0.25)
        k2 = generate_idempotency_key("post-1", 2, "BUY", "AAPL", 0.25)
        assert k1 != k2

    def test_case_normalization(self):
        k1 = generate_idempotency_key("post-1", 1, "buy", "aapl", 0.25)
        k2 = generate_idempotency_key("post-1", 1, "BUY", "AAPL", 0.25)
        assert k1 == k2

    def test_float_precision(self):
        k1 = generate_idempotency_key("post-1", 1, "BUY", "AAPL", 0.1)
        k2 = generate_idempotency_key("post-1", 1, "BUY", "AAPL", 0.10000000000)
        assert k1 == k2

    def test_different_precision_still_matches(self):
        k1 = generate_idempotency_key("post-1", 1, "BUY", "AAPL", 0.10000000001)
        k2 = generate_idempotency_key("post-1", 1, "BUY", "AAPL", 0.1)
        assert k1 == k2  # rounded to 10 decimal places


class TestIdempotencyGuard:
    def test_duplicate_key_blocked(self, tmp_db):
        q = WorkQueue(tmp_db)
        guard = IdempotencyGuard(q)

        guard.check_and_enqueue(
            "trade", "post-1", 1, "BUY", "AAPL", 0.25, {"order": "market"}
        )

        with pytest.raises(DuplicateKeyError, match="Duplicate instruction blocked"):
            guard.check_and_enqueue(
                "trade", "post-1", 1, "BUY", "AAPL", 0.25, {"order": "limit"}
            )

    def test_different_instruction_enqueued(self, tmp_db):
        q = WorkQueue(tmp_db)
        guard = IdempotencyGuard(q)

        id1 = guard.check_and_enqueue(
            "trade", "post-1", 1, "BUY", "AAPL", 0.25, {"x": 1}
        )
        id2 = guard.check_and_enqueue(
            "trade", "post-1", 2, "SELL", "TSLA", 0.5, {"x": 2}
        )
        assert id1 != id2
