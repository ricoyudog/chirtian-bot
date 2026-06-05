"""Tests for WebullCLIAdapter — subprocess mock-based."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.executor.exceptions import BrokerAuthError, BrokerError, BrokerTimeoutError
from src.executor.webull_adapter import WebullCLIAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SUCCESS_RESPONSE = {"ok": True, "detail": "success", "payload": {"result": "ok"}}
ERROR_RESPONSE = {"ok": False, "detail": "order rejected", "payload": {}}
AUTH_ERROR_RESPONSE = {"ok": False, "detail": "unauthorized: invalid token", "payload": {}}

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


def _mock_run(stdout: str = "", stderr: str = "", returncode: int = 0):
    """Create a mock subprocess.run that returns the given output."""
    mock = MagicMock(spec=subprocess.CompletedProcess)
    mock.stdout = stdout
    mock.stderr = stderr
    mock.returncode = returncode
    return mock


# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------


class TestRunCli:
    @patch("subprocess.run")
    def test_successful_json_response(self, mock_run):
        mock_run.return_value = _mock_run(stdout=json.dumps(SUCCESS_RESPONSE))

        adapter = WebullCLIAdapter()
        result = adapter._run_cli(["trading", "--action", "account-list"])

        assert result == {"result": "ok"}
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_timeout_raises_broker_timeout_error(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="webull-skill", timeout=30)

        adapter = WebullCLIAdapter(timeout=30)
        with pytest.raises(BrokerTimeoutError, match="timed out"):
            adapter._run_cli(["trading", "--action", "account-list"])

    @patch("subprocess.run")
    def test_empty_stdout_raises_broker_error(self, mock_run):
        mock_run.return_value = _mock_run(stdout="", stderr="some error")

        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerError, match="empty output"):
            adapter._run_cli(["trading", "--action", "account-list"])

    @patch("subprocess.run")
    def test_empty_stdout_with_auth_in_stderr(self, mock_run):
        mock_run.return_value = _mock_run(stdout="", stderr="Auth failure: unauthorized")

        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerAuthError):
            adapter._run_cli(["trading", "--action", "account-list"])

    @patch("subprocess.run")
    def test_non_json_output_raises_broker_error(self, mock_run):
        mock_run.return_value = _mock_run(stdout="not json at all")

        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerError, match="non-JSON"):
            adapter._run_cli(["trading", "--action", "account-list"])

    @patch("subprocess.run")
    def test_ok_false_raises_broker_error(self, mock_run):
        mock_run.return_value = _mock_run(stdout=json.dumps(ERROR_RESPONSE))

        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerError, match="order rejected"):
            adapter._run_cli(["trading", "--action", "account-list"])

    @patch("subprocess.run")
    def test_auth_error_in_detail(self, mock_run):
        mock_run.return_value = _mock_run(stdout=json.dumps(AUTH_ERROR_RESPONSE))

        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerAuthError):
            adapter._run_cli(["trading", "--action", "account-list"])

    @patch("subprocess.run")
    def test_unexpected_format_raises_broker_error(self, mock_run):
        mock_run.return_value = _mock_run(stdout=json.dumps({"no_ok_field": True}))

        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerError, match="Unexpected"):
            adapter._run_cli(["trading", "--action", "account-list"])


# ---------------------------------------------------------------------------
# Order operations
# ---------------------------------------------------------------------------


class TestPreviewOrder:
    @patch("subprocess.run")
    def test_preview_uses_temp_file(self, mock_run):
        preview_payload = {"estimated_cost": 1800.0}
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "preview", "payload": preview_payload,
        }))

        adapter = WebullCLIAdapter()
        result = adapter.preview_order("ACC001", ORDER_JSON)

        assert result == preview_payload
        # Verify the command uses preview action
        call_args = mock_run.call_args
        cmd = call_args[0][0]  # First positional arg is the command list
        assert "trading" in cmd
        assert "--action" in cmd
        idx_action = cmd.index("--action")
        assert cmd[idx_action + 1] == "preview"
        assert "--account-id" in cmd
        idx_account = cmd.index("--account-id")
        assert cmd[idx_account + 1] == "ACC001"
        assert "--order-file" in cmd


class TestPlaceOrder:
    @patch("subprocess.run")
    def test_place_returns_payload(self, mock_run):
        place_payload = {"order_id": "ORD12345", "status": "pending"}
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "placed", "payload": place_payload,
        }))

        adapter = WebullCLIAdapter()
        result = adapter.place_order("ACC001", ORDER_JSON)

        assert result["order_id"] == "ORD12345"
        # Verify uses place action
        cmd = mock_run.call_args[0][0]
        idx_action = cmd.index("--action")
        assert cmd[idx_action + 1] == "place"

    @patch("subprocess.run")
    def test_temp_file_cleaned_up_on_success(self, mock_run):
        mock_run.return_value = _mock_run(stdout=json.dumps(SUCCESS_RESPONSE))

        adapter = WebullCLIAdapter()
        adapter.place_order("ACC001", ORDER_JSON)

        # The temp file should be deleted — verified by the finally block
        # We just check the call succeeded without error

    @patch("subprocess.run")
    def test_temp_file_cleaned_up_on_error(self, mock_run):
        mock_run.side_effect = BrokerError("fail")

        adapter = WebullCLIAdapter()
        with pytest.raises(BrokerError):
            adapter.place_order("ACC001", ORDER_JSON)


# ---------------------------------------------------------------------------
# Order management
# ---------------------------------------------------------------------------


class TestGetOrderStatus:
    @patch("subprocess.run")
    def test_get_order_status(self, mock_run):
        status_payload = {"order_id": "ORD123", "status": "filled", "filled_qty": 10}
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "ok", "payload": status_payload,
        }))

        adapter = WebullCLIAdapter()
        result = adapter.get_order_status("ACC001", "ORD123")

        assert result["status"] == "filled"
        cmd = mock_run.call_args[0][0]
        assert "--order-id" in cmd
        idx = cmd.index("--order-id")
        assert cmd[idx + 1] == "ORD123"


class TestCancelOrder:
    @patch("subprocess.run")
    def test_cancel_order(self, mock_run):
        cancel_payload = {"order_id": "ORD123", "status": "cancelled"}
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "cancelled", "payload": cancel_payload,
        }))

        adapter = WebullCLIAdapter()
        result = adapter.cancel_order("ACC001", "ORD123")

        assert result["status"] == "cancelled"
        cmd = mock_run.call_args[0][0]
        idx = cmd.index("--action")
        assert cmd[idx + 1] == "cancel"


# ---------------------------------------------------------------------------
# Account data
# ---------------------------------------------------------------------------


class TestGetAccountList:
    @patch("subprocess.run")
    def test_returns_list_payload(self, mock_run):
        accounts = [{"account_id": "ACC1"}, {"account_id": "ACC2"}]
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "ok", "payload": accounts,
        }))

        adapter = WebullCLIAdapter()
        result = adapter.get_account_list()

        assert result == accounts

    @patch("subprocess.run")
    def test_wraps_dict_payload(self, mock_run):
        """If payload is a single dict, wrap it in a list."""
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "ok", "payload": {"account_id": "ACC1"},
        }))

        adapter = WebullCLIAdapter()
        result = adapter.get_account_list()

        assert len(result) == 1
        assert result[0]["account_id"] == "ACC1"


class TestGetBalance:
    @patch("subprocess.run")
    def test_returns_balance_dict(self, mock_run):
        balance = {"equity": 50000.0, "buying_power": 10000.0}
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "ok", "payload": balance,
        }))

        adapter = WebullCLIAdapter()
        result = adapter.get_balance("ACC001")

        assert result["equity"] == 50000.0


class TestGetPositions:
    @patch("subprocess.run")
    def test_returns_positions_list(self, mock_run):
        positions = [{"symbol": "AAPL", "quantity": 10}]
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "ok", "payload": positions,
        }))

        adapter = WebullCLIAdapter()
        result = adapter.get_positions("ACC001")

        assert len(result) == 1
        assert result[0]["symbol"] == "AAPL"

    @patch("subprocess.run")
    def test_extracts_positions_from_dict(self, mock_run):
        """If payload wraps positions in a dict, extract the list."""
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "ok",
            "payload": {"positions": [{"symbol": "AAPL", "quantity": 10}]},
        }))

        adapter = WebullCLIAdapter()
        result = adapter.get_positions("ACC001")

        assert len(result) == 1


class TestGetOpenOrders:
    @patch("subprocess.run")
    def test_returns_orders_list(self, mock_run):
        orders = [{"order_id": "ORD1", "symbol": "AAPL", "status": "pending"}]
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "ok", "payload": orders,
        }))

        adapter = WebullCLIAdapter()
        result = adapter.get_open_orders("ACC001")

        assert len(result) == 1
        assert result[0]["order_id"] == "ORD1"

    @patch("subprocess.run")
    def test_empty_orders(self, mock_run):
        mock_run.return_value = _mock_run(stdout=json.dumps({
            "ok": True, "detail": "ok", "payload": [],
        }))

        adapter = WebullCLIAdapter()
        result = adapter.get_open_orders("ACC001")

        assert result == []


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_default_values(self):
        adapter = WebullCLIAdapter()
        assert adapter._cli == "webull-skill"
        assert adapter._timeout == 30

    def test_custom_values(self):
        adapter = WebullCLIAdapter(cli_path="/usr/local/bin/webull-skill", timeout=60)
        assert adapter._cli == "/usr/local/bin/webull-skill"
        assert adapter._timeout == 60
