"""Telegram bot — long-poll loop, push alerts, drill confirm_callback, heartbeat.

Implements the M3 requirements from
``openspec/changes/production-deploy-scheduling-dashboard``.

Design decision (change design.md #6): the bot is a stdlib-only polling
loop, NOT ``python-telegram-bot``. It does exactly three things plus
heartbeat:

1. Pipeline failure alerts (push_pipeline_error / push_circuit_breaker /
   push_crosscheck_disagreement).
2. ``/stop`` command → writes ``runtime/kill_switch.flag``.
3. Drill ``confirm_callback`` — blocking, returns the operator reply
   timestamp or ``None`` on timeout.
4. Heartbeat → ``runtime/bot_heartbeat.json`` every N minutes.

The polling loop runs in a daemon thread; push methods are non-blocking
best-effort. ``confirm_callback`` is intentionally blocking because the
drill runner needs to wait for the operator.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.notify.telegram import TelegramNotifier

_logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 300  # 5 minutes (spec: ≤ 5 min)
DEFAULT_LONG_POLL_TIMEOUT_SECONDS = 30
DEFAULT_CONFIRM_TIMEOUT_SECONDS = 300
_KILL_SWITCH_FILENAME = "kill_switch.flag"
_BOT_HEARTBEAT_FILENAME = "bot_heartbeat.json"
_STOP_REPLY = "Kill switch engaged. Daemon will stop within 2 ticks."
_DRILL_PROMPT = (
    "\U0001F514 Drill Confirmation Required\n"
    "Please reply to confirm alert receipt."
)


class TelegramBot:
    """Stdlib-only Telegram bot.

    Use :meth:`start` to spawn the polling loop in a daemon thread,
    :meth:`stop` to request shutdown. The various ``push_*`` methods are
    safe to call from any thread.
    """

    def __init__(
        self,
        *,
        bot_token: str,
        chat_id: str,
        runs_dir: str | Path = "runtime",
        heartbeat_interval_seconds: int = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    ) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._runs_dir = Path(runs_dir)
        self._heartbeat_interval = heartbeat_interval_seconds
        self._notifier = TelegramNotifier(
            bot_token=bot_token, chat_id=chat_id, runs_dir=runs_dir
        )

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._offset = 0  # getUpdates offset (next update_id to acknowledge)
        self._last_heartbeat = 0.0

    # ==================================================================
    # Lifecycle
    # ==================================================================

    def start(self) -> None:
        """Start the polling loop in a daemon thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop, name="telegram-bot", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Request the polling loop to stop. Returns immediately."""
        self._stop_event.set()

    # ==================================================================
    # Push alerts (non-blocking, best-effort)
    # ==================================================================

    def push_pipeline_error(self, run_id: str, error_summary: str, stage: str) -> None:
        """Push a pipeline-stage error alert. Best-effort."""
        self._notifier.send_pipeline_error(run_id, error_summary, stage)

    def push_circuit_breaker(self) -> None:
        """Push the circuit-breaker activation alert. Best-effort."""
        self._notifier.send_circuit_breaker_alert()

    def push_crosscheck_disagreement(
        self, post_excerpt: str, model_outputs: list[str]
    ) -> None:
        """Push the parser cross-check 0/3 disagreement alert. Best-effort."""
        self._notifier.send_crosscheck_disagreement(post_excerpt, model_outputs)

    # ==================================================================
    # /stop command handler
    # ==================================================================

    def handle_stop_command(self) -> None:
        """Write kill_switch.flag and reply with the confirmation message.

        Idempotent: writing the flag when it already exists is a no-op.
        """
        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            (self._runs_dir / _KILL_SWITCH_FILENAME).touch()
        except OSError as exc:
            _logger.error("failed to write kill_switch.flag: %s", exc)
        self._notifier.send_message(_STOP_REPLY)

    # ==================================================================
    # Drill confirm_callback (BLOCKING by design)
    # ==================================================================

    def confirm_callback(
        self, timeout_seconds: int = DEFAULT_CONFIRM_TIMEOUT_SECONDS
    ) -> str | None:
        """Send the drill confirmation prompt and block until operator replies.

        Returns the ISO-8601 confirmation timestamp on reply, ``None`` on
        timeout. Blocking because :func:`src.shadow.drill.run_drill` waits
        for the operator-in-the-loop handshake.
        """
        if not self._notifier.send_message(_DRILL_PROMPT):
            _logger.error("drill prompt send failed; aborting confirm_callback")
            return None

        deadline = time.monotonic() + timeout_seconds
        # Mark the prompt's message boundary: any text update from the chat
        # after this point (excluding /commands) is treated as confirmation.
        # ponytail: a real bot would track a reply-to message id; long-poll
        # offset filtering is sufficient for single-operator drill flow.
        local_offset = self._offset
        while time.monotonic() < deadline:
            if self._stop_event.is_set():
                return None
            remaining = deadline - time.monotonic()
            poll_timeout = max(1, min(DEFAULT_LONG_POLL_TIMEOUT_SECONDS, int(remaining)))
            updates = self._get_updates(
                offset=local_offset, timeout_seconds=poll_timeout
            )
            for update in updates:
                local_offset = max(local_offset, update.get("update_id", 0) + 1)
                msg = update.get("message") or update.get("channel_post")
                if not msg:
                    continue
                text = (msg.get("text") or "").strip()
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if chat_id and chat_id != self._chat_id:
                    continue
                if not text or text.startswith("/"):
                    continue
                return datetime.now(UTC).isoformat()
            time.sleep(0.1)
        return None

    # ==================================================================
    # Heartbeat
    # ==================================================================

    def write_heartbeat(self) -> None:
        """Write ``runtime/bot_heartbeat.json``. Called from the poll loop."""
        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "last_heartbeat": datetime.now(UTC).isoformat(),
                "pid": os.getpid(),
                "status": "ok",
            }
            path = self._runs_dir / _BOT_HEARTBEAT_FILENAME
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            tmp.replace(path)
            self._last_heartbeat = time.monotonic()
        except OSError as exc:
            _logger.error("failed to write bot_heartbeat.json: %s", exc)

    # ==================================================================
    # Internal: polling loop
    # ==================================================================

    def _poll_loop(self) -> None:
        _logger.info("telegram bot polling loop started")
        self.write_heartbeat()
        while not self._stop_event.is_set():
            try:
                updates = self._get_updates(
                    offset=self._offset, timeout_seconds=DEFAULT_LONG_POLL_TIMEOUT_SECONDS
                )
                for update in updates:
                    self._offset = max(self._offset, update.get("update_id", 0) + 1)
                    self._dispatch(update)
                if (
                    time.monotonic() - self._last_heartbeat
                    >= self._heartbeat_interval
                ):
                    self.write_heartbeat()
            except Exception as exc:  # noqa: BLE001 — poll loop must survive
                _logger.error("telegram poll loop error: %s", exc)
                time.sleep(5)
        _logger.info("telegram bot polling loop stopped")

    def _dispatch(self, update: dict[str, Any]) -> None:
        msg = update.get("message") or update.get("channel_post")
        if not msg:
            return
        text = (msg.get("text") or "").strip()
        if text == "/stop" or text.startswith("/stop@"):
            self.handle_stop_command()

    # ==================================================================
    # Internal: Telegram API calls
    # ==================================================================

    def _get_updates(self, *, offset: int, timeout_seconds: int) -> list[dict[str, Any]]:
        """Long-poll ``getUpdates``. Returns the ``result`` array (empty on error)."""
        url = TELEGRAM_API_BASE.format(token=self._bot_token, method="getUpdates")
        params = urllib.parse.urlencode(
            {"offset": offset, "timeout": timeout_seconds}
        )
        full_url = f"{url}?{params}"
        req = urllib.request.Request(full_url, method="GET")
        # Long-poll: the server holds the connection for up to timeout_seconds,
        # so the HTTP read timeout must exceed it.
        try:
            with urllib.request.urlopen(
                req, timeout=timeout_seconds + 10
            ) as resp:
                if 200 <= resp.status < 300:
                    body = json.loads(resp.read().decode("utf-8"))
                    if body.get("ok"):
                        return body.get("result", []) or []
                _logger.warning("getUpdates non-ok: status=%s", resp.status)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            _logger.warning("getUpdates network error: %s", exc)
        return []
