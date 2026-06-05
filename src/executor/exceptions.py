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
