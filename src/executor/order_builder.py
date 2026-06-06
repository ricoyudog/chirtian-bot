"""OrderBuilder — converts ExecutionIntent to Webull order JSON."""

from __future__ import annotations

import hashlib
import json

from src.executor.models import ExecutionIntent


class OrderBuildError(Exception):
    """Raised when order parameters fail validation."""


class OrderBuilder:
    """Builds Webull-compatible order JSON from an ExecutionIntent.

    MVP produces LIMIT orders for US equities only. The order JSON structure
    matches the ``webull-skill trading --action place --order-file`` schema.
    """

    def build_order_json(self, intent: ExecutionIntent) -> dict:
        """Convert an ExecutionIntent into a Webull order dict.

        Parameters
        ----------
        intent : ExecutionIntent
            The execution intent to convert.

        Returns
        -------
        dict
            Webull-compatible order JSON.

        Raises
        ------
        OrderBuildError
            If any parameter is invalid.
        """
        self._validate(intent)

        return {
            "symbol": intent.symbol,
            "side": intent.side,
            "order_type": intent.order_type,
            "limit_price": intent.limit_price,
            "quantity": intent.quantity,
            "instrument_type": "EQUITY",
            "market": "US",
            "time_in_force": "DAY",
            "entrust_type": "QTY",
            "support_trading_session": "CORE",
            "combo_type": "NORMAL",
        }

    @staticmethod
    def _validate(intent: ExecutionIntent) -> None:
        """Validate order parameters before building JSON."""
        if not intent.symbol or not intent.symbol.strip():
            raise OrderBuildError("symbol must be non-empty")
        if intent.quantity <= 0:
            raise OrderBuildError(f"quantity must be > 0, got {intent.quantity}")
        if intent.limit_price <= 0:
            raise OrderBuildError(f"limit_price must be > 0, got {intent.limit_price}")


def compute_request_hash(order_json: dict) -> str:
    """Compute a deterministic sha256 hash of the order JSON.

    Uses sorted keys for deterministic serialization regardless of
    dict insertion order.

    Parameters
    ----------
    order_json : dict
        The order JSON to hash.

    Returns
    -------
    str
        Hex-encoded sha256 digest (64 characters).
    """
    serialized = json.dumps(order_json, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()
