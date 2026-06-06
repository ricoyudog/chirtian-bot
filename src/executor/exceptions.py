"""Executor exception classes."""


class BrokerError(Exception):
    """Base exception for broker interaction failures."""

    def __init__(self, message: str, detail: str = ""):
        self.detail = detail
        super().__init__(message)


class BrokerTimeoutError(BrokerError):
    """Broker request timed out."""


class BrokerAuthError(BrokerError):
    """Broker authentication failed (invalid or expired credentials)."""


class EnvironmentBlockedError(BrokerError):
    """Execution blocked because the runtime environment is not permitted."""


class DuplicateExecutionError(BrokerError):
    """A successful execution attempt with the same idempotency key already exists."""
