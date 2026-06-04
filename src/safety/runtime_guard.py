"""Runtime mode guard — safety checks before daemon start and broker mutations."""

from __future__ import annotations

from enum import Enum

from src.config.settings import RuntimeConfig

MVP_ALLOWED_MODES = frozenset({"offline_replay", "shadow", "uat_confirm"})


class ReconcileStatus(Enum):
    """Reconcile state of the system.

    OK: local state matches broker — sizing and execution allowed.
    MISMATCH: local state diverges from broker — all execution blocked.
    UNKNOWN: initial state, typically before first reconcile — blocked.
    """

    OK = "ok"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


class ReconcileBlockedError(RuntimeError):
    """Raised when execution is blocked due to reconcile mismatch."""


class RuntimeGuard:
    """Guards against unsafe runtime configurations and reconcile mismatches.

    Call `assert_safe_to_run()` once at daemon startup.
    Call `assert_mutation_allowed()` before any mutating broker operation.
    Call `assert_reconcile_ok()` before sizing or execution.
    """

    def __init__(self, config: RuntimeConfig):
        self.config = config
        self._reconcile_status: ReconcileStatus = ReconcileStatus.UNKNOWN
        self._stopped_reason: str | None = None

    def assert_safe_to_run(self) -> None:
        """Hard fail if the configuration is inherently unsafe."""
        if self.config.environment == "prod" and self.config.confirmation_mode == "auto":
            raise RuntimeError(
                "FATAL: prod environment with auto confirmation is not allowed. "
                "Set confirmation_mode to 'confirm' or switch environment to 'uat'."
            )

        if self.config.mode not in MVP_ALLOWED_MODES:
            raise RuntimeError(
                f"FATAL: mode '{self.config.mode}' is not supported in MVP. "
                f"Allowed modes: {sorted(MVP_ALLOWED_MODES)}"
            )

    def assert_mutation_allowed(self) -> None:
        """Check before any mutating broker operation.

        Blocks if:
        - prod + auto (hard config violation)
        - reconcile status is not OK (stop-the-world)
        """
        if self.config.environment == "prod" and self.config.confirmation_mode == "auto":
            raise RuntimeError(
                "FATAL: mutation blocked — prod environment with auto confirmation."
            )

        self.assert_reconcile_ok()

    def assert_reconcile_ok(self) -> None:
        """Check before sizing or execution.

        Raises ReconcileBlockedError if reconcile status is not OK.
        """
        if self._reconcile_status != ReconcileStatus.OK:
            raise ReconcileBlockedError(
                f"Execution blocked: reconcile status is {self._reconcile_status.value}."
                + (
                    f" Reason: {self._stopped_reason}"
                    if self._stopped_reason
                    else ""
                )
                + " Resolve mismatch and manually clear before resuming."
            )

    # -- Reconcile status management --

    def activate_stop(self, reason: str) -> None:
        """Activate stop-the-world due to reconcile mismatch.

        After activation, assert_reconcile_ok() and assert_mutation_allowed()
        will raise ReconcileBlockedError until manually cleared via deactivate_stop().
        """
        self._reconcile_status = ReconcileStatus.MISMATCH
        self._stopped_reason = reason

    def deactivate_stop(self) -> None:
        """Manually clear stop-the-world state.

        This is the ONLY way to recover from MISMATCH. It must be called
        by an operator after verifying the system is consistent.
        Does NOT automatically activate — sets status to UNKNOWN,
        requiring a successful reconcile to reach OK.
        """
        self._reconcile_status = ReconcileStatus.UNKNOWN
        self._stopped_reason = None

    def mark_reconcile_ok(self) -> None:
        """Mark reconcile as OK after a successful reconciliation.

        Only valid when called after deactivate_stop() (manual clear)
        followed by a successful reconcile. This two-step process ensures
        human intervention is required before recovery.
        """
        if self._reconcile_status == ReconcileStatus.MISMATCH:
            # Cannot go directly from MISMATCH to OK — requires manual clear first
            return
        self._reconcile_status = ReconcileStatus.OK
        self._stopped_reason = None

    @property
    def reconcile_status(self) -> ReconcileStatus:
        """Current reconcile status."""
        return self._reconcile_status

    @property
    def is_stopped(self) -> bool:
        """Whether stop-the-world is active."""
        return self._reconcile_status != ReconcileStatus.OK

    @property
    def stopped_reason(self) -> str | None:
        """Reason for stop-the-world, if active."""
        return self._stopped_reason
