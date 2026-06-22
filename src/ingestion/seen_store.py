"""Processed-post seen-state — gates re-processing a Substack post."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ProcessedPostStore:
    """JSON-backed record of posts the bot has already handled.

    Distinct from the MCP server's ``checkpoints.json`` (gates fetch) and the
    ``ExecutionGate`` idempotency key (gates orders) — this gates *re-processing*
    a post so a re-poll does not re-parse / re-trade it.
    """

    def __init__(self, path: str | Path = "runtime/processed_posts.json"):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def is_seen(self, post_id: str) -> bool:
        """Return True if this post_id has already been processed."""
        return post_id in self._read()

    def mark_seen(
        self,
        post_id: str,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Record a post as processed, with optional metadata."""
        data = self._read()
        data[post_id] = {"ts": datetime.now(UTC).isoformat(), **(meta or {})}
        self._write(data)

    def _read(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text())
        except json.JSONDecodeError:
            return {}

    def _write(self, data: dict) -> None:
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
