"""TradingAgents gateway models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TAResult:
    ticker: str
    rating: Optional[str] = None
    available: bool = False
    error: Optional[str] = None
    raw_decision: Optional[str] = None
