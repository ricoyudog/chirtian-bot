"""FastAPI read-only observation dashboard for the Christian bot.

Reads only local runtime files (JSONL + SQLite + heartbeat JSON). Never calls
the broker API. Bind to 127.0.0.1 only — see design Decision #11.
"""

from __future__ import annotations

from src.dashboard.app import create_app

__all__ = ["create_app"]
