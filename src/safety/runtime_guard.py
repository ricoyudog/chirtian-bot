"""Runtime mode guard — safety checks before daemon start and broker mutations."""

from src.config.settings import RuntimeConfig

MVP_ALLOWED_MODES = frozenset({"offline_replay", "shadow", "uat_confirm"})


class RuntimeGuard:
    """Guards against unsafe runtime configurations.

    Call `assert_safe_to_run()` once at daemon startup.
    Call `assert_mutation_allowed()` before any mutating broker operation.
    """

    def __init__(self, config: RuntimeConfig):
        self.config = config

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

        In non-auto modes, mutation is allowed but should be logged/confirmed.
        In auto mode with a safe environment, mutation is allowed.
        This method only blocks the prod+auto combination.
        """
        if self.config.environment == "prod" and self.config.confirmation_mode == "auto":
            raise RuntimeError(
                "FATAL: mutation blocked — prod environment with auto confirmation."
            )
