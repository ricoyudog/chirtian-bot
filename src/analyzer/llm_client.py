"""LLM client adapter — protocol, error classes, and Claude CLI implementation."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Protocol, runtime_checkable

import jsonschema

# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


class LLMError(Exception):
    """Base for all LLM client errors."""


class LLMUnavailableError(LLMError):
    """Raised when the LLM binary is not found in PATH."""


class LLMTimeoutError(LLMError):
    """Raised when the LLM call exceeds the specified timeout.

    Attributes:
        timeout: The configured timeout in seconds.
        elapsed: Actual elapsed time in seconds.
    """

    def __init__(self, timeout: float, elapsed: float) -> None:
        self.timeout = timeout
        self.elapsed = elapsed
        super().__init__(f"LLM call timed out after {elapsed:.1f}s (limit: {timeout}s)")


class LLMOutputError(LLMError):
    """Raised when the LLM returns invalid JSON or a non-zero exit code.

    Attributes:
        raw_output: The raw stdout/stderr from the LLM process.
    """

    def __init__(self, message: str, raw_output: str = "") -> None:
        self.raw_output = raw_output
        super().__init__(message)


class LLMSchemaError(LLMError):
    """Raised when LLM output is valid JSON but fails schema validation.

    Attributes:
        validation_error: The jsonschema validation error message.
    """

    def __init__(self, message: str, validation_error: str = "") -> None:
        self.validation_error = validation_error
        super().__init__(message)


# ---------------------------------------------------------------------------
# LLMClient protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM clients that return schema-validated JSON."""

    def complete_json(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        timeout_seconds: int,
    ) -> dict[str, Any]:
        """Call the LLM and return validated JSON matching *schema*.

        Raises:
            LLMUnavailableError: LLM binary not found.
            LLMTimeoutError: Call exceeded timeout.
            LLMOutputError: Invalid JSON or non-zero exit.
            LLMSchemaError: JSON does not conform to schema.
        """
        ...  # pragma: no cover


# ---------------------------------------------------------------------------
# ClaudeCliClient — wraps `claude` CLI via subprocess
# ---------------------------------------------------------------------------

_DEFAULT_BUDGET_USD = 0.05


class ClaudeCliClient:
    """LLMClient implementation backed by the ``claude`` CLI.

    Invokes::

        claude -p --bare --output-format json --tools "" --max-budget-usd <budget>

    via :func:`subprocess.run`.
    """

    def __init__(
        self,
        *,
        cli_path: str = "claude",
        max_budget_usd: float = _DEFAULT_BUDGET_USD,
    ) -> None:
        self._cli_path = cli_path
        self._max_budget_usd = max_budget_usd

    # -- public interface ---------------------------------------------------

    def complete_json(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        timeout_seconds: int,
    ) -> dict[str, Any]:
        """Call Claude CLI and return validated JSON.

        Returns:
            Parsed and schema-validated dict.

        Raises:
            LLMUnavailableError: ``claude`` not in PATH.
            LLMTimeoutError: Exceeded *timeout_seconds*.
            LLMOutputError: Non-zero exit or invalid JSON.
            LLMSchemaError: JSON fails schema validation.
        """
        cmd = self._build_command(prompt)

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            raise LLMUnavailableError(f"'{self._cli_path}' not found in PATH")
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            raise LLMTimeoutError(
                timeout=float(timeout_seconds),
                elapsed=elapsed,
            )

        elapsed = time.monotonic() - start

        if result.returncode != 0:
            raise LLMOutputError(
                f"claude CLI exited with code {result.returncode}",
                raw_output=result.stderr,
            )

        # Parse JSON output
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise LLMOutputError(
                f"Invalid JSON from LLM: {exc}",
                raw_output=result.stdout,
            )

        # Validate against schema
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            raise LLMSchemaError(
                f"LLM output failed schema validation: {exc.message}",
                validation_error=str(exc),
            )

        return data

    # -- internals ----------------------------------------------------------

    def _build_command(self, prompt: str) -> list[str]:
        return [
            self._cli_path,
            "-p",
            prompt,
            "--bare",
            "--output-format",
            "json",
            "--tools",
            "",
            "--max-budget-usd",
            str(self._max_budget_usd),
        ]
