"""Idempotency key generation and dedup guard."""

import hashlib
import json

from src.state.queue import DuplicateKeyError, WorkQueue


def generate_idempotency_key(
    post_id: str,
    sequence: int,
    action: str,
    symbol: str,
    quantity_pct: float,
) -> str:
    canonical = json.dumps(
        {
            "post_id": post_id,
            "sequence": sequence,
            "action": action.upper(),
            "symbol": symbol.upper(),
            "quantity_pct": round(quantity_pct, 10),
        },
        sort_keys=True,
    )
    return "idem:" + hashlib.sha256(canonical.encode()).hexdigest()[:16]


class IdempotencyGuard:
    """Wraps WorkQueue with explicit duplicate-check semantics."""

    def __init__(self, queue: WorkQueue):
        self.queue = queue

    def check_and_enqueue(
        self, job_type: str, post_id: str, sequence: int,
        action: str, symbol: str, quantity_pct: float, payload: dict,
    ) -> str:
        key = generate_idempotency_key(post_id, sequence, action, symbol, quantity_pct)
        try:
            return self.queue.enqueue(job_type, key, payload)
        except DuplicateKeyError:
            raise DuplicateKeyError(
                f"Duplicate instruction blocked: "
                f"post_id={post_id}, seq={sequence}, action={action}, "
                f"symbol={symbol}, qty_pct={quantity_pct}"
            )
