"""Tests for WebullCLIAdapter — persistent shim (stdin/stdout JSON) transport.

The adapter keeps ``scripts/webull_json.py`` alive as a subprocess and exchanges
newline-delimited JSON with it. These tests mock the subprocess + selector so
no real broker/SDK is required. (Live behaviour is covered by the sandbox run
and ``tests/smoke``.)
"""

from __future__ import annotations

import json
import selectors
import subprocess
from unittest.mock import MagicMock

import pytest

from src.executor.exceptions import BrokerAuthError, BrokerError, BrokerTimeoutError
from src.executor.webull_adapter import WebullCLIAdapter

ORDER_JSON = {
    "symbol": "AAPL",
    "side": "BUY",
    "order_type": "LIMIT",
    "limit_price": 180.0,
    "quantity": 10,
    "instrument_type": "EQUITY",
    "market": "US",
    "time_in_force": "DAY",
    "entrust_type": "QTY",
    "support_trading_session": "CORE",
    "combo_type": "NORMAL",
}


def _ok(payload):
    return json.dumps({"ok": True, "payload": payload, "detail": ""})


def _fail(detail):
    return json.dumps({"ok": False, "payload": None, "detail": detail})


def _wire(monkeypatch, response_line: str, *, ready: bool = True):
    """Patch Popen + DefaultSelector to feed one response line."""
    proc = MagicMock()
    proc.poll.return_value = None
    proc.stdin = MagicMock()
    proc.stdout = MagicMock()
    proc.stdout.readline = MagicMock(side_effect=[response_line])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)

    sel = MagicMock()
    sel.register = MagicMock()
    sel.unregister = MagicMock()
    sel.select.return_value = [(proc.stdout, selectors.EVENT_READ)] if ready else []
    monkeypatch.setattr(selectors, "DefaultSelector", lambda: sel)
    return proc


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_defaults(self):
        a = WebullCLIAdapter()
        assert a._python.endswith("python")
        assert a._shim.endswith("webull_json.py")

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("WEBULL_PYTHON", "/custom/python")
        monkeypatch.setenv("WEBULL_SHIM_SCRIPT", "/custom/shim.py")
        a = WebullCLIAdapter()
        assert a._python == "/custom/python"
        assert a._shim == "/custom/shim.py"


# ---------------------------------------------------------------------------
# _call transport
# ---------------------------------------------------------------------------


class TestCall:
    def test_returns_payload(self, monkeypatch):
        proc = _wire(monkeypatch, _ok({"equity": 50000.0}))
        adapter = WebullCLIAdapter()

        result = adapter.get_balance("ACC001")

        assert result == {"equity": 50000.0}
        # request is a JSON line on stdin
        written = proc.stdin.write.call_args[0][0]
        assert json.loads(written) == {"action": "balance", "account_id": "ACC001"}

    def test_ok_false_raises_broker_error(self, monkeypatch):
        _wire(monkeypatch, _fail("order rejected: insufficient buying power"))
        adapter = WebullCLIAdapter()

        with pytest.raises(BrokerError, match="order rejected"):
            adapter.get_balance("ACC001")

    def test_auth_detail_raises_broker_auth(self, monkeypatch):
        _wire(monkeypatch, _fail("ERROR_CHECK_TOKEN: unauthorized"))
        adapter = WebullCLIAdapter()

        with pytest.raises(BrokerAuthError):
            adapter.get_balance("ACC001")

    def test_oauth_error_code_is_not_auth(self, monkeypatch):
        # Regression: "OAuth_" error codes must NOT be classified as auth.
        _wire(monkeypatch, _fail("OAUTH_OPENAPI_NO_TRADING_DAY: Non-trading day."))
        adapter = WebullCLIAdapter()

        with pytest.raises(BrokerError):
            try:
                adapter.get_balance("ACC001")
            except BrokerAuthError:
                pytest.fail("OAUTH_ business error misclassified as BrokerAuthError")

    def test_empty_line_raises_broker_error(self, monkeypatch):
        proc = MagicMock()
        proc.poll.return_value = None
        proc.stdin = MagicMock()
        proc.stdout.readline = MagicMock(return_value="")  # shim exited
        monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)
        sel = MagicMock()
        sel.select.return_value = [(proc.stdout, selectors.EVENT_READ)]
        monkeypatch.setattr(selectors, "DefaultSelector", lambda: sel)

        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerError, match="exited unexpectedly"):
            adapter.get_balance("ACC001")

    def test_timeout_raises_broker_timeout(self, monkeypatch):
        _wire(monkeypatch, "", ready=False)  # selector never fires
        adapter = WebullCLIAdapter(timeout=1)

        with pytest.raises(BrokerTimeoutError):
            adapter.get_balance("ACC001")

    def test_missing_interpreter_raises_broker_error(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "Popen", MagicMock(side_effect=FileNotFoundError("no python"))
        )
        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerError, match="not found"):
            adapter.get_balance("ACC001")


# ---------------------------------------------------------------------------
# Public methods build the right request dicts
# ---------------------------------------------------------------------------


class TestRequestShapes:
    @pytest.mark.parametrize(
        "method, args, expected",
        [
            ("get_account_list", (), {"action": "account_list"}),
            ("get_balance", ("ACC1",), {"action": "balance", "account_id": "ACC1"}),
            ("get_positions", ("ACC1",), {"action": "positions", "account_id": "ACC1"}),
            ("get_open_orders", ("ACC1",), {"action": "open_orders", "account_id": "ACC1"}),
            ("get_stock_snapshot", ("AAPL",), {"action": "quote", "symbol": "AAPL"}),
        ],
    )
    def test_account_data(self, monkeypatch, method, args, expected):
        proc = _wire(monkeypatch, _ok({}) if method != "get_account_list" else _ok([]))
        adapter = WebullCLIAdapter()
        getattr(adapter, method)(*args)
        assert json.loads(proc.stdin.write.call_args[0][0]) == expected

    def test_preview_order(self, monkeypatch):
        proc = _wire(monkeypatch, _ok({"estimated_cost": "100.00"}))
        adapter = WebullCLIAdapter()
        adapter.preview_order("ACC1", ORDER_JSON)
        req = json.loads(proc.stdin.write.call_args[0][0])
        assert req["action"] == "preview"
        assert req["account_id"] == "ACC1"
        assert req["order"] == ORDER_JSON

    def test_place_order(self, monkeypatch):
        proc = _wire(monkeypatch, _ok({"order_id": "ORD1"}))
        adapter = WebullCLIAdapter()
        result = adapter.place_order("ACC1", ORDER_JSON)
        req = json.loads(proc.stdin.write.call_args[0][0])
        assert req["action"] == "place"
        assert req["order"] == ORDER_JSON
        assert result == {"order_id": "ORD1"}

    def test_get_order_status(self, monkeypatch):
        proc = _wire(monkeypatch, _ok({"status": "filled"}))
        adapter = WebullCLIAdapter()
        adapter.get_order_status("ACC1", "ORD1")
        req = json.loads(proc.stdin.write.call_args[0][0])
        assert req == {"action": "order_detail", "account_id": "ACC1", "order_id": "ORD1"}

    def test_cancel_order(self, monkeypatch):
        proc = _wire(monkeypatch, _ok({"cancelled": "ORD1"}))
        adapter = WebullCLIAdapter()
        adapter.cancel_order("ACC1", "ORD1")
        req = json.loads(proc.stdin.write.call_args[0][0])
        assert req == {"action": "cancel", "account_id": "ACC1", "order_id": "ORD1"}
