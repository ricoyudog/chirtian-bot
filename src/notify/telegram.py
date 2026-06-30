"""Telegram push notifications — stdlib-only HTTP client for the Bot API.

A thin wrapper over the Telegram Bot API ``sendMessage`` endpoint using
:mod:`urllib.request` (no external ``python-telegram-bot`` dependency).
Used by callers that only need to *push* alert messages and do not need
the polling/command-handling features of :class:`src.notify.bot.TelegramBot`.

Network errors are swallowed and logged: a Telegram outage must never
crash the daemon. The return value lets callers distinguish success from
failure for observability.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"
_DEFAULT_TIMEOUT_SECONDS = 10


class TelegramNotifier:
    """Sends formatted Telegram alert messages via the Bot API.

    All public ``send_*`` methods are best-effort: on network failure they
    log the error and return ``False`` rather than raising.
    """

    def __init__(
        self,
        *,
        bot_token: str,
        chat_id: str,
        runs_dir: str | Path = "runtime",
    ) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._runs_dir = Path(runs_dir)

    # ------------------------------------------------------------------
    # Low-level transport
    # ------------------------------------------------------------------

    def send_message(self, text: str) -> bool:
        """Send ``text`` to the configured chat. Returns True on success."""
        url = TELEGRAM_API_BASE.format(token=self._bot_token)
        payload: dict[str, Any] = {
            "chat_id": self._chat_id,
            "text": text,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_DEFAULT_TIMEOUT_SECONDS) as resp:
                if 200 <= resp.status < 300:
                    return True
                _logger.error(
                    "telegram sendMessage non-2xx status=%s body=%s",
                    resp.status,
                    resp.read().decode("utf-8", errors="replace")[:500],
                )
                return False
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            _logger.error("telegram sendMessage failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Formatted alert helpers
    # ------------------------------------------------------------------

    def send_pipeline_error(self, run_id: str, error_summary: str, stage: str) -> bool:
        """Push a pipeline-stage error alert."""
        text = (
            "\U0001F6A8 Pipeline Error\n"
            f"Run: {run_id}\n"
            f"Stage: {stage}\n"
            f"Error: {error_summary}"
        )
        return self.send_message(text)

    def send_circuit_breaker_alert(self) -> bool:
        """Push the circuit-breaker activation message."""
        text = (
            "\u26A0\uFE0F Circuit Breaker Activated\n"
            "5 consecutive tick failures.\n"
            "Kill switch engaged."
        )
        return self.send_message(text)

    def send_crosscheck_disagreement(
        self, post_excerpt: str, model_outputs: list[str]
    ) -> bool:
        """Push the parser cross-check 0/3 disagreement alert."""
        outputs = model_outputs + ["(none)"] * (3 - len(model_outputs))
        text = (
            "\U0001F50D Parser Cross-Check Disagreement\n"
            f"Post: {post_excerpt}...\n"
            f"Model 1: {outputs[0]}\n"
            f"Model 2: {outputs[1]}\n"
            f"Model 3: {outputs[2]}"
        )
        return self.send_message(text)


# ponytail: confirm_callback lives on TelegramBot (it needs getUpdates polling),
# not here — this class stays a stateless pusher.
