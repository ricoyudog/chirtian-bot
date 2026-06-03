"""Tests for LLM client adapter."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.analyzer.llm_client import (
    ClaudeCliClient,
    LLMOutputError,
    LLMSchemaError,
    LLMTimeoutError,
    LLMUnavailableError,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SAMPLE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "instructions": {"type": "array"},
    },
    "required": ["status"],
}

_GOOD_RESPONSE = json.dumps({"status": "EXECUTABLE", "instructions": []})


def _make_client(cli_path: str = "claude", **kwargs: float) -> ClaudeCliClient:
    return ClaudeCliClient(cli_path=cli_path, **kwargs)


def _mock_completed_process(
    *,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> MagicMock:
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


class TestSuccess:
    def test_returns_validated_json(self) -> None:
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(stdout=_GOOD_RESPONSE)

            result = _make_client().complete_json(
                prompt="test",
                schema=_SAMPLE_SCHEMA,
                timeout_seconds=30,
            )

        assert result == {"status": "EXECUTABLE", "instructions": []}

    def test_command_includes_required_flags(self) -> None:
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(stdout=_GOOD_RESPONSE)

            _make_client().complete_json(
                prompt="hello",
                schema=_SAMPLE_SCHEMA,
                timeout_seconds=10,
            )

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "claude"
        assert "-p" in cmd
        assert "hello" in cmd
        assert "--bare" in cmd
        assert "--output-format" in cmd
        assert "json" in cmd
        assert "--tools" in cmd
        assert "" in cmd
        assert "--max-budget-usd" in cmd
        assert "0.05" in cmd

    def test_custom_budget(self) -> None:
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(stdout=_GOOD_RESPONSE)

            _make_client(max_budget_usd=0.10).complete_json(
                prompt="x",
                schema=_SAMPLE_SCHEMA,
                timeout_seconds=5,
            )

        cmd = mock_run.call_args[0][0]
        assert "0.1" in cmd

    def test_custom_cli_path(self) -> None:
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(stdout=_GOOD_RESPONSE)

            _make_client(cli_path="/usr/local/bin/claude").complete_json(
                prompt="x",
                schema=_SAMPLE_SCHEMA,
                timeout_seconds=5,
            )

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "/usr/local/bin/claude"


# ---------------------------------------------------------------------------
# Error: CLI not found
# ---------------------------------------------------------------------------


class TestUnavailable:
    def test_raises_unavailable_when_not_in_path(self) -> None:
        with patch(
            "src.analyzer.llm_client.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            with pytest.raises(LLMUnavailableError, match="not found in PATH"):
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=5,
                )


# ---------------------------------------------------------------------------
# Error: Timeout
# ---------------------------------------------------------------------------


class TestTimeout:
    def test_raises_timeout(self) -> None:
        import subprocess as sp

        with patch(
            "src.analyzer.llm_client.subprocess.run",
            side_effect=sp.TimeoutExpired(cmd="claude", timeout=10),
        ):
            with pytest.raises(LLMTimeoutError) as exc_info:
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=10,
                )

        err = exc_info.value
        assert err.timeout == 10.0

    def test_timeout_carries_elapsed_time(self) -> None:
        import subprocess as sp

        with patch(
            "src.analyzer.llm_client.subprocess.run",
            side_effect=sp.TimeoutExpired(cmd="claude", timeout=5),
        ):
            with pytest.raises(LLMTimeoutError) as exc_info:
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=5,
                )

        assert exc_info.value.elapsed >= 0


# ---------------------------------------------------------------------------
# Error: Invalid JSON output
# ---------------------------------------------------------------------------


class TestInvalidJSON:
    def test_raises_output_error_on_bad_json(self) -> None:
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(stdout="not json{{{")

            with pytest.raises(LLMOutputError, match="Invalid JSON"):
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=5,
                )

    def test_raw_output_captured_on_bad_json(self) -> None:
        raw = "not json{{{"
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(stdout=raw)

            with pytest.raises(LLMOutputError) as exc_info:
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=5,
                )

        assert exc_info.value.raw_output == raw


# ---------------------------------------------------------------------------
# Error: Non-zero exit code
# ---------------------------------------------------------------------------


class TestNonZeroExit:
    def test_raises_output_error_on_nonzero_exit(self) -> None:
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(
                returncode=1,
                stderr="some error occurred",
            )

            with pytest.raises(LLMOutputError, match="exited with code 1"):
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=5,
                )

    def test_stderr_captured_on_nonzero_exit(self) -> None:
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(
                returncode=2,
                stderr="budget exceeded",
            )

            with pytest.raises(LLMOutputError) as exc_info:
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=5,
                )

        assert "budget exceeded" in exc_info.value.raw_output


# ---------------------------------------------------------------------------
# Error: Schema validation failure
# ---------------------------------------------------------------------------


class TestSchemaMismatch:
    def test_raises_schema_error_on_validation_failure(self) -> None:
        bad_response = json.dumps({"wrong_field": True})  # missing "status"
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(stdout=bad_response)

            with pytest.raises(LLMSchemaError, match="schema validation"):
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=5,
                )

    def test_schema_error_carries_validation_details(self) -> None:
        bad_response = json.dumps({"wrong_field": True})
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(stdout=bad_response)

            with pytest.raises(LLMSchemaError) as exc_info:
                _make_client().complete_json(
                    prompt="test",
                    schema=_SAMPLE_SCHEMA,
                    timeout_seconds=5,
                )

        assert exc_info.value.validation_error  # non-empty


# ---------------------------------------------------------------------------
# Stderr capture for audit
# ---------------------------------------------------------------------------


class TestStderrCapture:
    def test_stderr_available_on_success(self) -> None:
        """Verify stderr is accessible via the mock for audit logging."""
        with patch("src.analyzer.llm_client.subprocess.run") as mock_run:
            mock_run.return_value = _mock_completed_process(
                stdout=_GOOD_RESPONSE,
                stderr="model: claude-opus-4-8",
            )

            _make_client().complete_json(
                prompt="test",
                schema=_SAMPLE_SCHEMA,
                timeout_seconds=5,
            )

        # In real use, the caller would log stderr from the subprocess result.
        # Here we verify the mock captured it.
        assert mock_run.return_value.stderr == "model: claude-opus-4-8"
