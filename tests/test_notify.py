"""Integration tests for the ``src.notify`` package (task 3.11).

Covers:
- ``TelegramNotifier``: success / failure paths and message formatting for
  pipeline errors, circuit-breaker alerts, and parser cross-check
  disagreements.
- ``TelegramBot``: ``/stop`` command (writes kill_switch.flag and replies),
  push-alert delegation, heartbeat writer, and drill ``confirm_callback``
  (operator reply and timeout).

All HTTP is mocked at ``urllib.request.urlopen`` — no real Telegram calls.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.notify.bot import TelegramBot
from src.notify.telegram import TelegramNotifier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _MockResp:
    """Minimal context-manager mock for ``urllib.request.urlopen`` result."""

    def __init__(self, payload: bytes, status: int = 200):
        self._buf = io.BytesIO(payload)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._buf.getvalue()


def _mock_response(body: dict, status: int = 200) -> _MockResp:
    return _MockResp(json.dumps(body).encode("utf-8"), status)


def _ok_response(result=None) -> _MockResp:
    return _mock_response({"ok": True, "result": result or []})


@pytest.fixture
def runtime_dir(tmp_path: Path) -> Path:
    rd = tmp_path / "runtime"
    rd.mkdir(parents=True, exist_ok=True)
    return rd


@pytest.fixture
def notifier(runtime_dir: Path) -> TelegramNotifier:
    return TelegramNotifier(
        bot_token="TEST_TOKEN", chat_id="12345", runs_dir=runtime_dir
    )


@pytest.fixture
def bot(runtime_dir: Path) -> TelegramBot:
    return TelegramBot(
        bot_token="TEST_TOKEN", chat_id="12345", runs_dir=runtime_dir
    )


# ---------------------------------------------------------------------------
# TelegramNotifier — transport
# ---------------------------------------------------------------------------


class TestTelegramNotifier:
    def test_send_message_success(self, notifier: TelegramNotifier):
        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            return_value=_ok_response(),
        ) as mock_urlopen:
            assert notifier.send_message("hello") is True
        mock_urlopen.assert_called_once()

    def test_send_message_network_error(self, notifier: TelegramNotifier):
        import urllib.error

        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            # Network failure is swallowed, returns False, no raise.
            assert notifier.send_message("hello") is False

    def test_send_pipeline_error_format(self, notifier: TelegramNotifier):
        captured: dict = {}

        def _capture(req, *args, **kwargs):
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            return _ok_response()

        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            side_effect=_capture,
        ):
            notifier.send_pipeline_error("run-123", "LLMTimeoutError", "parser")

        text = captured["payload"]["text"]
        assert "run-123" in text
        assert "parser" in text
        assert "LLMTimeoutError" in text

    def test_send_circuit_breaker_alert(self, notifier: TelegramNotifier):
        captured: dict = {}

        def _capture(req, *args, **kwargs):
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            return _ok_response()

        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            side_effect=_capture,
        ):
            notifier.send_circuit_breaker_alert()

        text = captured["payload"]["text"]
        assert "Circuit Breaker" in text
        assert "kill switch" in text.lower() or "kill_switch" in text.lower()

    def test_send_crosscheck_disagreement(self, notifier: TelegramNotifier):
        captured: dict = {}

        def _capture(req, *args, **kwargs):
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            return _ok_response()

        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            side_effect=_capture,
        ):
            notifier.send_crosscheck_disagreement(
                "Christian: buy AAPL now",
                ["BUY AAPL", "SELL AAPL", "HOLD TSLA"],
            )

        text = captured["payload"]["text"]
        assert "buy AAPL now" in text
        assert "BUY AAPL" in text
        assert "SELL AAPL" in text
        assert "HOLD TSLA" in text


# ---------------------------------------------------------------------------
# TelegramBot — /stop command
# ---------------------------------------------------------------------------


class TestTelegramBotStopCommand:
    def test_stop_command_writes_kill_switch_flag(
        self, bot: TelegramBot, runtime_dir: Path
    ):
        # handle_stop_command sends the reply via the notifier; mock the HTTP.
        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            return_value=_ok_response(),
        ):
            bot.handle_stop_command()

        assert (runtime_dir / "kill_switch.flag").exists()

    def test_stop_command_replies_confirmation(
        self, bot: TelegramBot, runtime_dir: Path
    ):
        captured: dict = {}

        def _capture(req, *args, **kwargs):
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            return _ok_response()

        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            side_effect=_capture,
        ):
            bot.handle_stop_command()

        assert "Kill switch" in captured["payload"]["text"]


# ---------------------------------------------------------------------------
# TelegramBot — push alerts (delegation)
# ---------------------------------------------------------------------------


class TestTelegramBotPushAlerts:
    def test_push_pipeline_error_delegates(self, bot: TelegramBot):
        with patch.object(bot._notifier, "send_pipeline_error") as spy:
            bot.push_pipeline_error("run-1", "boom", "sizing")
            spy.assert_called_once_with("run-1", "boom", "sizing")

    def test_push_circuit_breaker_delegates(self, bot: TelegramBot):
        with patch.object(bot._notifier, "send_circuit_breaker_alert") as spy:
            bot.push_circuit_breaker()
            spy.assert_called_once_with()

    def test_push_crosscheck_disagreement_delegates(self, bot: TelegramBot):
        with patch.object(
            bot._notifier, "send_crosscheck_disagreement"
        ) as spy:
            bot.push_crosscheck_disagreement("excerpt", ["a", "b", "c"])
            spy.assert_called_once_with("excerpt", ["a", "b", "c"])


# ---------------------------------------------------------------------------
# TelegramBot — heartbeat
# ---------------------------------------------------------------------------


class TestTelegramBotHeartbeat:
    def test_write_heartbeat(self, bot: TelegramBot, runtime_dir: Path):
        bot.write_heartbeat()

        hb_path = runtime_dir / "bot_heartbeat.json"
        assert hb_path.exists()
        payload = json.loads(hb_path.read_text())
        assert "last_heartbeat" in payload
        assert "pid" in payload
        assert payload["status"] == "ok"


# ---------------------------------------------------------------------------
# TelegramBot — drill confirm_callback
# ---------------------------------------------------------------------------


class TestConfirmCallback:
    def test_confirm_callback_returns_timestamp_on_response(
        self, bot: TelegramBot
    ):
        # One operator reply message after the prompt.
        reply_update = [
            {
                "update_id": 1,
                "message": {
                    "message_id": 10,
                    "text": "confirmed",
                    "chat": {"id": 12345},
                },
            }
        ]

        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            return_value=_ok_response(result=reply_update),
        ) as mock_urlopen:
            ts = bot.confirm_callback(timeout_seconds=2)

        assert ts is not None
        # At least one HTTP call (prompt + at least one getUpdates poll).
        assert mock_urlopen.call_count >= 1

    def test_confirm_callback_returns_none_on_timeout(self, bot: TelegramBot):
        # Prompt send succeeds, but getUpdates returns no messages and the
        # short timeout forces the loop to exit.
        with patch(
            "src.notify.telegram.urllib.request.urlopen",
            return_value=_ok_response(result=[]),
        ):
            ts = bot.confirm_callback(timeout_seconds=1)

        assert ts is None
