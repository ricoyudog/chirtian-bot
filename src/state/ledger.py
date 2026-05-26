"""Append-only JSONL audit ledger."""

import json
from pathlib import Path
from typing import Optional

from src.state.models import AuditEvent


class AuditLedger:
    def __init__(self, ledger_path: str | Path):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: AuditEvent) -> None:
        line = json.dumps({
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "config_hash": event.config_hash,
            "source": event.source,
            "data": event.data,
            "correlation_id": event.correlation_id,
        })
        with open(self.ledger_path, "a") as f:
            f.write(line + "\n")

    def query(
        self,
        event_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        since: Optional[str] = None,
    ) -> list[AuditEvent]:
        results = []
        for event in self._read_all():
            if event_type and event.event_type != event_type:
                continue
            if correlation_id and event.correlation_id != correlation_id:
                continue
            if since and event.timestamp < since:
                continue
            results.append(event)
        return results

    def verify_integrity(self) -> bool:
        try:
            with open(self.ledger_path) as f:
                for line in f:
                    json.loads(line)
            return True
        except (json.JSONDecodeError, FileNotFoundError):
            return False

    def _read_all(self) -> list[AuditEvent]:
        events = []
        try:
            with open(self.ledger_path) as f:
                for line in f:
                    obj = json.loads(line)
                    events.append(AuditEvent(
                        event_id=obj["event_id"],
                        timestamp=obj["timestamp"],
                        event_type=obj["event_type"],
                        config_hash=obj["config_hash"],
                        source=obj["source"],
                        data=obj["data"],
                        correlation_id=obj.get("correlation_id"),
                    ))
        except FileNotFoundError:
            pass
        return events
