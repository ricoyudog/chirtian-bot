"""Alert drill runner — simulates end-to-end kill switch scenarios."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Optional

from src.state.ledger import AuditLedger
from src.state.models import AuditEvent

INCIDENTS_DIR = "runtime/incidents"
DRILL_TIMEOUT_SECONDS = 300  # 5 minutes


@dataclass
class DrillResult:
    drill_type: str
    started_at: str
    ended_at: str
    duration_seconds: float
    result: str  # PASS | FAILED
    failure_reason: Optional[str] = None
    alert_channel: str = "console"
    operator_confirmation: Optional[str] = None


class AlertDrillRunner:
    """Simulates end-to-end kill switch scenarios for alert channel verification."""

    def __init__(
        self,
        ledger: AuditLedger,
        incidents_dir: str = INCIDENTS_DIR,
        timeout_seconds: float = DRILL_TIMEOUT_SECONDS,
    ):
        self._ledger = ledger
        self._incidents_dir = Path(incidents_dir)
        self._timeout_seconds = timeout_seconds

    def run_drill(
        self,
        drill_type: str = "kill_switch",
        confirm_callback: Optional[Callable[[], str]] = None,
    ) -> DrillResult:
        """Execute an alert drill.

        Args:
            drill_type: Type of drill (e.g., "kill_switch").
            confirm_callback: Callable that returns operator confirmation timestamp.
                              If None, drill auto-passes (for testing).

        Returns:
            DrillResult with pass/fail status.
        """
        started_at = datetime.now(UTC).isoformat()
        start_time = time.monotonic()

        # Step 1: Simulate anomaly detection
        self._record_drill_event(drill_type, "anomaly_detected", started_at)

        # Step 2: Trigger kill switch
        self._record_drill_event(drill_type, "kill_switch_triggered", started_at)

        # Step 3: Send alert via console + audit ledger
        alert_sent_at = datetime.now(UTC).isoformat()
        self._record_drill_event(drill_type, "alert_sent", alert_sent_at)
        print(f"[SHADOW DRILL] Alert: Kill switch drill triggered at {alert_sent_at}")

        # Step 4: Wait for operator confirmation
        operator_confirmation = None
        failure_reason = None

        if confirm_callback is not None:
            try:
                deadline = time.monotonic() + self._timeout_seconds
                operator_confirmation = confirm_callback()
                if time.monotonic() > deadline:
                    failure_reason = "OPERATOR_NO_RESPONSE"
                    operator_confirmation = None
            except Exception as exc:
                failure_reason = f"CONFIRM_CALLBACK_ERROR: {exc}"
        else:
            # Auto-pass for testing without callback
            operator_confirmation = datetime.now(UTC).isoformat()

        ended_at = datetime.now(UTC).isoformat()
        duration = time.monotonic() - start_time

        result = "PASS" if failure_reason is None else "FAILED"

        drill_result = DrillResult(
            drill_type=drill_type,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration,
            result=result,
            failure_reason=failure_reason,
            alert_channel="console",
            operator_confirmation=operator_confirmation,
        )

        # Persist drill result
        self._write_drill_note(drill_result)
        self._record_drill_event(drill_type, f"drill_{result.lower()}", ended_at)

        return drill_result

    def check_drill_passed(self) -> bool:
        """Check if at least one successful drill has been recorded."""
        incidents_path = self._incidents_dir
        if not incidents_path.exists():
            return False

        for note_file in sorted(incidents_path.glob("*.md")):
            content = note_file.read_text()
            if "Result: PASS" in content:
                return True
        return False

    def _record_drill_event(self, drill_type: str, event_name: str, timestamp: str) -> None:
        event = AuditEvent(
            event_type=f"shadow_drill.{drill_type}.{event_name}",
            source="shadow_drill",
            data={
                "drill_type": drill_type,
                "event": event_name,
                "timestamp": timestamp,
            },
        )
        self._ledger.append(event)

    def _write_drill_note(self, result: DrillResult) -> None:
        """Write drill result as a dated incident note."""
        self._incidents_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        filename = f"{date_str}-drill-{result.drill_type}.md"
        filepath = self._incidents_dir / filename

        lines = [
            f"# Kill Switch Drill — {date_str}",
            "",
            f"- Type: {result.drill_type}",
            f"- Started: {result.started_at}",
            f"- Ended: {result.ended_at}",
            f"- Duration: {result.duration_seconds:.1f} seconds",
            f"- Result: {result.result}",
        ]

        if result.failure_reason:
            lines.append(f"- Failure Reason: {result.failure_reason}")
        else:
            lines.append("- Failure Reason: (none)")

        lines.append(f"- Alert Channel: {result.alert_channel}")

        if result.operator_confirmation:
            lines.append(f"- Operator Confirmation: {result.operator_confirmation}")
        else:
            lines.append("- Operator Confirmation: no response")

        filepath.write_text("\n".join(lines) + "\n")
