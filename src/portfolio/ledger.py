"""Append-only portfolio event ledger (JSONL)."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class PortfolioLedger:
    """Append-only JSONL ledger for portfolio events.

    Records sizing decisions, reconcile results, and portfolio state changes.
    Each line is a self-contained JSON object.
    """

    def __init__(self, ledger_path: str | Path):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        event_type: str,
        data: dict[str, Any],
        correlation_id: str | None = None,
    ) -> None:
        """Append a single event line to the ledger."""
        entry = {
            "ts": _utc_now_iso(),
            "type": event_type,
            "data": data,
        }
        if correlation_id is not None:
            entry["correlation_id"] = correlation_id
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def query(
        self,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Read back filtered events from the ledger."""
        results = []
        for entry in self._read_all():
            if event_type and entry.get("type") != event_type:
                continue
            if since and entry.get("ts", "") < since:
                continue
            if correlation_id and entry.get("correlation_id") != correlation_id:
                continue
            results.append(entry)
        return results

    def verify_integrity(self) -> bool:
        """Check that every line in the ledger is valid JSON."""
        try:
            with open(self.ledger_path) as f:
                for line in f:
                    json.loads(line)
            return True
        except (json.JSONDecodeError, FileNotFoundError):
            return False

    # ------------------------------------------------------------------
    # Baseline snapshot (reconcile bootstrap)
    # ------------------------------------------------------------------

    _BASELINE_TYPE = "baseline_snapshot"

    def has_baseline(self) -> bool:
        """Return True if at least one baseline snapshot has been recorded."""
        return bool(self.query(event_type=self._BASELINE_TYPE))

    def record_baseline(self, snapshot: Any) -> None:
        """Record a portfolio snapshot as the local baseline.

        Used by the orchestrator to bootstrap / refresh the local view of
        account state that subsequent reconciles compare against.
        """
        self.append(
            self._BASELINE_TYPE,
            {
                "account_id": snapshot.account_id,
                "snapshot": snapshot.model_dump(mode="json"),
            },
            correlation_id=snapshot.account_id,
        )

    def get_baseline(self) -> Optional[Any]:
        """Return the most recently recorded baseline snapshot, or None."""
        events = self.query(event_type=self._BASELINE_TYPE)
        if not events:
            return None
        from src.portfolio.models import PortfolioSnapshot

        return PortfolioSnapshot.model_validate(events[-1]["data"]["snapshot"])

    def _read_all(self) -> list[dict[str, Any]]:
        entries = []
        try:
            with open(self.ledger_path) as f:
                for line in f:
                    entries.append(json.loads(line))
        except FileNotFoundError:
            pass
        return entries
