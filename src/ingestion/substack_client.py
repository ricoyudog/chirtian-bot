"""Substack MCP client — Python bridge to the Node.js MCP server via JSON-RPC over stdio."""

from __future__ import annotations

import json
import subprocess
from typing import Optional


class SubstackClient:
    """Python wrapper for the mcp-substack MCP server.

    Spawns the Node.js MCP server as a subprocess and communicates
    via JSON-RPC over stdio. The server manages authentication and
    checkpoint persistence internally.
    """

    def __init__(
        self,
        node_path: str = "/opt/homebrew/bin/node",
        server_script: str = "/Users/chunsingyu/softwares/mcp-substack/lib/index.mjs",
    ):
        self._node = node_path
        self._script = server_script
        self._proc: Optional[subprocess.Popen] = None
        self._request_id = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _ensure_started(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            return

        self._proc = subprocess.Popen(
            [self._node, self._script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # MCP initialization handshake
        self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "christian-bot", "version": "0.1.0"},
        })
        self._send_notification("notifications/initialized")

    def _send_request(self, method: str, params: dict) -> dict:
        self._ensure_started()
        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        self._proc.stdin.write(json.dumps(msg) + "\n")
        self._proc.stdin.flush()

        response_line = self._proc.stdout.readline()
        if not response_line:
            raise RuntimeError("MCP server closed connection")

        response = json.loads(response_line)

        # Skip notifications (no id)
        if "id" not in response:
            response_line = self._proc.stdout.readline()
            if not response_line:
                raise RuntimeError("MCP server closed connection")
            response = json.loads(response_line)

        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")

        return response.get("result", {})

    def _send_notification(self, method: str) -> None:
        msg = {"jsonrpc": "2.0", "method": method}
        self._proc.stdin.write(json.dumps(msg) + "\n")
        self._proc.stdin.flush()

    def check_updates(
        self,
        publication_ids: Optional[list[str]] = None,
        since: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Check for new Substack posts since last checkpoint.

        Returns list of update dicts with: updateId, title, canonicalUrl, publishedAt, excerpt.
        """
        args = {"limit": limit}
        if publication_ids:
            args["publicationIds"] = publication_ids
        if since:
            args["since"] = since

        result = self._send_request("tools/call", {
            "name": "substack_updates_check",
            "arguments": args,
        })

        content = result.get("content", [])
        if not content:
            return []

        text = content[0].get("text", "")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []

        return data.get("updates", [])

    def fetch_post(self, url: str, format: str = "text") -> dict:
        """Fetch a single post by URL.

        Returns dict with: url, title, text, publishedAt, blocks, etc.
        """
        result = self._send_request("tools/call", {
            "name": "substack_post_fetch",
            "arguments": {"url": url, "format": format},
        })

        content = result.get("content", [])
        if not content:
            return {}

        text = content[0].get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}

    def close(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._proc.wait(timeout=5)
        self._proc = None
