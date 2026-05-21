"""Tests for RuntimeGuard."""

import pytest

from src.config.settings import RiskConfig, RuntimeConfig
from src.safety.runtime_guard import RuntimeGuard


def _make_config(**overrides):
    defaults = dict(
        mode="offline_replay",
        environment="uat",
        region="US",
        account_ids=["ACC001"],
        confirmation_mode="confirm",
        risk=RiskConfig(
            max_notional_usd=10000, max_quantity=100, max_concentration_pct=5.0
        ),
    )
    defaults.update(overrides)
    return RuntimeConfig(**defaults)


class TestAssertSafeToRun:
    def test_prod_auto_hard_fails(self):
        config = _make_config(mode="prod_auto", environment="prod", confirmation_mode="auto")
        guard = RuntimeGuard(config)
        with pytest.raises(RuntimeError, match="prod environment with auto confirmation"):
            guard.assert_safe_to_run()

    def test_valid_modes_pass(self):
        for mode in ("offline_replay", "shadow", "uat_confirm"):
            config = _make_config(mode=mode)
            guard = RuntimeGuard(config)
            guard.assert_safe_to_run()  # should not raise

    def test_invalid_mode_rejected(self):
        config = _make_config(mode="prod_confirm")
        guard = RuntimeGuard(config)
        with pytest.raises(RuntimeError, match="not supported in MVP"):
            guard.assert_safe_to_run()

    def test_prod_auto_mode_rejected_by_mvp_guard(self):
        """prod_auto is not in MVP allowed modes even with confirmation_mode=confirm."""
        config = _make_config(mode="prod_auto", environment="prod", confirmation_mode="confirm")
        guard = RuntimeGuard(config)
        with pytest.raises(RuntimeError, match="not supported in MVP"):
            guard.assert_safe_to_run()


class TestAssertMutationAllowed:
    def test_mutation_blocked_prod_auto(self):
        config = _make_config(mode="prod_auto", environment="prod", confirmation_mode="auto")
        guard = RuntimeGuard(config)
        with pytest.raises(RuntimeError, match="mutation blocked"):
            guard.assert_mutation_allowed()

    def test_mutation_allowed_uat_confirm(self):
        config = _make_config(mode="uat_confirm", confirmation_mode="confirm")
        guard = RuntimeGuard(config)
        guard.assert_mutation_allowed()  # should not raise

    def test_mutation_allowed_offline_replay(self):
        config = _make_config(mode="offline_replay")
        guard = RuntimeGuard(config)
        guard.assert_mutation_allowed()  # should not raise

    def test_mutation_allowed_shadow(self):
        config = _make_config(mode="shadow")
        guard = RuntimeGuard(config)
        guard.assert_mutation_allowed()  # should not raise
