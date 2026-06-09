"""Webull CLI adapter — implements BrokerClient via subprocess calls to webull-skill."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

from src.executor.exceptions import BrokerAuthError, BrokerError, BrokerTimeoutError


class WebullCLIAdapter:
    """BrokerClient implementation via `webull-skill` CLI subprocess.

    Parameters
    ----------
    cli_path : str
        Path or command name for the webull-skill CLI binary.
    timeout : int
        Subprocess timeout in seconds (default 30).
    """

    def __init__(self, cli_path: str = "webull-skill", timeout: int = 30) -> None:
        self._cli = cli_path
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Internal subprocess runner
    # ------------------------------------------------------------------

    def _run_cli(self, args: list[str]) -> dict:
        """Execute a webull-skill CLI command and return parsed OperationResult.

        The CLI outputs JSON in OperationResult format:
            {"ok": bool, "detail": str, "payload": {...}}

        Raises
        ------
        BrokerTimeoutError
            If subprocess exceeds the configured timeout.
        BrokerError
            If CLI returns ``ok: false`` or output is not valid JSON.
        """
        cmd = [self._cli, *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise BrokerTimeoutError(
                f"webull-skill timed out after {self._timeout}s",
                detail=str(exc),
            ) from exc

        # Parse stdout
        stdout = result.stdout.strip()
        if not stdout:
            # If stdout is empty, check stderr for auth or other errors
            stderr = result.stderr.strip()
            if "auth" in stderr.lower() or "unauthorized" in stderr.lower():
                raise BrokerAuthError(
                    "Webull CLI authentication failed",
                    detail=stderr,
                )
            raise BrokerError(
                f"webull-skill returned empty output (exit code {result.returncode})",
                detail=stderr,
            )

        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise BrokerError(
                "webull-skill returned non-JSON output",
                detail=stdout[:500],
            ) from exc

        # Validate OperationResult structure
        if not isinstance(parsed, dict) or "ok" not in parsed:
            raise BrokerError(
                "Unexpected webull-skill output format",
                detail=str(parsed)[:500],
            )

        if not parsed["ok"]:
            detail = parsed.get("detail", "unknown error")
            # Detect auth errors from detail message
            if "auth" in detail.lower() or "unauthorized" in detail.lower():
                raise BrokerAuthError(
                    f"Webull auth error: {detail}",
                    detail=detail,
                )
            raise BrokerError(
                f"webull-skill error: {detail}",
                detail=detail,
            )

        return parsed.get("payload", {})

    # ------------------------------------------------------------------
    # Order operations
    # ------------------------------------------------------------------

    def preview_order(self, account_id: str, order_json: dict) -> dict:
        """Preview an order without submitting it."""
        return self._run_order_action("preview", account_id, order_json)

    def place_order(self, account_id: str, order_json: dict) -> dict:
        """Place an order to the broker."""
        return self._run_order_action("place", account_id, order_json)

    def _run_order_action(
        self, action: str, account_id: str, order_json: dict,
    ) -> dict:
        """Run a preview or place action using a temp order file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False,
        ) as tmp:
            json.dump(order_json, tmp)
            tmp_path = tmp.name
        try:
            return self._run_cli([
                "trading",
                "--action", action,
                "--account-id", account_id,
                "--order-file", tmp_path,
            ])
        finally:
            os.unlink(tmp_path)

    # ------------------------------------------------------------------
    # Order management
    # ------------------------------------------------------------------

    def get_order_status(self, account_id: str, order_id: str) -> dict:
        """Get the current status of an order."""
        return self._run_cli([
            "trading",
            "--action", "detail",
            "--account-id", account_id,
            "--order-id", order_id,
        ])

    def cancel_order(self, account_id: str, order_id: str) -> dict:
        """Cancel an existing order."""
        return self._run_cli([
            "trading",
            "--action", "cancel",
            "--account-id", account_id,
            "--order-id", order_id,
        ])

    # ------------------------------------------------------------------
    # Account data
    # ------------------------------------------------------------------

    def get_account_list(self) -> list[dict]:
        """List all accounts."""
        payload = self._run_cli(["trading", "--action", "account-list"])
        if isinstance(payload, list):
            return payload
        # Some endpoints wrap results in a key
        return payload.get("accounts", [payload]) if isinstance(payload, dict) else []

    def get_balance(self, account_id: str) -> dict:
        """Get account balance."""
        return self._run_cli([
            "trading",
            "--action", "balance",
            "--account-id", account_id,
        ])

    def get_positions(self, account_id: str) -> list[dict]:
        """Get account positions."""
        payload = self._run_cli([
            "trading",
            "--action", "position",
            "--account-id", account_id,
        ])
        if isinstance(payload, list):
            return payload
        return payload.get("positions", []) if isinstance(payload, dict) else []

    def get_open_orders(self, account_id: str) -> list[dict]:
        """Get open (pending) orders."""
        payload = self._run_cli([
            "trading",
            "--action", "open",
            "--account-id", account_id,
        ])
        if isinstance(payload, list):
            return payload
        return payload.get("orders", []) if isinstance(payload, dict) else []

    def get_stock_snapshot(self, symbol: str) -> dict:
        """Get stock snapshot / quote data for a single symbol."""
        return self._run_cli(["stock-snapshot", "--symbol", symbol])
