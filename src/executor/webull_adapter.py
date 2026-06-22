"""Webull broker adapter — talks to the SDK via a persistent webull_json shim.

``webull-skill`` prints human-readable text on success (no JSON mode), which is
unusable for programmatic parsing. Instead this adapter spawns
``scripts/webull_json.py`` **once** and keeps it alive, sending newline-delimited
JSON requests and reading one JSON response per line. The shim initializes the
SDK (and its token) a single time, so the orchestrator's several broker calls
per order do not each re-check the token (the token endpoint is rate-limited to
10 req/30s).

The shim runs under ``.venv-webull/bin/python`` (the official SDK requires
Python <3.14; the orchestrator's own venv is 3.14) and reuses the skill's
``.env`` + token. Responses are normalized by the shim into the shapes that
``WebullAccountProvider`` expects.
"""

from __future__ import annotations

import json
import os
import subprocess

from src.executor.exceptions import BrokerAuthError, BrokerError, BrokerTimeoutError


class WebullCLIAdapter:
    """BrokerClient implementation backed by the persistent webull_json shim."""

    def __init__(
        self,
        python_bin: str | None = None,
        shim_script: str | None = None,
        timeout: int = 90,
    ) -> None:
        self._python = python_bin or os.environ.get(
            "WEBULL_PYTHON", ".venv-webull/bin/python"
        )
        self._shim = shim_script or os.environ.get(
            "WEBULL_SHIM_SCRIPT", "scripts/webull_json.py"
        )
        self._timeout = timeout
        self._proc: subprocess.Popen | None = None

    # ------------------------------------------------------------------
    # Persistent shim process
    # ------------------------------------------------------------------

    def _ensure_proc(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            return
        try:
            self._proc = subprocess.Popen(
                [self._python, self._shim],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError as exc:
            raise BrokerError(
                f"webull interpreter or shim not found: {self._python} / {self._shim}",
                detail=str(exc),
            ) from exc

    def _call(self, request: dict) -> dict:
        """Send one request line; return the response payload.

        Raises BrokerTimeoutError if the shim does not respond within timeout,
        BrokerAuthError on auth/token/2FA failures, BrokerError otherwise.
        """
        self._ensure_proc()
        assert self._proc is not None
        assert self._proc.stdin is not None and self._proc.stdout is not None

        try:
            self._proc.stdin.write(json.dumps(request) + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self._proc = None
            raise BrokerError("webull shim pipe closed", detail=str(exc)) from exc

        # Bounded read so a hung SDK call cannot block forever.
        import selectors

        sel = selectors.DefaultSelector()
        sel.register(self._proc.stdout, selectors.EVENT_READ)
        ready = sel.select(timeout=self._timeout)
        sel.unregister(self._proc.stdout)
        if not ready:
            raise BrokerTimeoutError(
                f"webull shim did not respond within {self._timeout}s",
                detail=str(request.get("action")),
            )

        line = self._proc.stdout.readline()
        if not line:
            self._proc = None
            raise BrokerError("webull shim exited unexpectedly", detail=str(request))

        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BrokerError(
                "webull shim returned non-JSON output", detail=line[:500]
            ) from exc

        if not parsed.get("ok"):
            detail = parsed.get("detail") or "unknown webull error"
            if _looks_like_auth(detail):
                raise BrokerAuthError(detail, detail=detail)
            raise BrokerError(f"webull error: {detail}", detail=detail)

        payload = parsed.get("payload")
        return payload if payload is not None else {}

    # ------------------------------------------------------------------
    # Account data
    # ------------------------------------------------------------------

    def get_account_list(self) -> list[dict]:
        return self._call({"action": "account_list"})

    def get_balance(self, account_id: str) -> dict:
        return self._call({"action": "balance", "account_id": account_id})

    def get_positions(self, account_id: str) -> list[dict]:
        return self._call({"action": "positions", "account_id": account_id})

    def get_open_orders(self, account_id: str) -> list[dict]:
        return self._call({"action": "open_orders", "account_id": account_id})

    def get_stock_snapshot(self, symbol: str) -> dict:
        return self._call({"action": "quote", "symbol": symbol})

    # ------------------------------------------------------------------
    # Order operations
    # ------------------------------------------------------------------

    def preview_order(self, account_id: str, order_json: dict) -> dict:
        return self._call(
            {"action": "preview", "account_id": account_id, "order": order_json}
        )

    def place_order(self, account_id: str, order_json: dict) -> dict:
        return self._call(
            {"action": "place", "account_id": account_id, "order": order_json}
        )

    def get_order_status(self, account_id: str, order_id: str) -> dict:
        return self._call(
            {"action": "order_detail", "account_id": account_id, "order_id": order_id}
        )

    def cancel_order(self, account_id: str, order_id: str) -> dict:
        return self._call(
            {"action": "cancel", "account_id": account_id, "order_id": order_id}
        )


def _looks_like_auth(detail: str) -> bool:
    # Specific markers only — bare "auth"/"token" would false-match "OAuth"
    # error codes like OAUTH_OPENAPI_NO_TRADING_DAY (which is NOT an auth error).
    d = detail.lower()
    return any(
        k in d
        for k in (
            "unauthorized",
            "invalid_token",
            "invalid access token",
            "2fa",
            "error_init_token",
            "error_check_token",
            "no_available_device",
        )
    )
