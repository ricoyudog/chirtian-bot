"""Shared fixtures for Phase 1 tests."""

import pytest


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a temporary SQLite database path."""
    return tmp_path / "test_queue.db"


@pytest.fixture
def tmp_ledger(tmp_path):
    """Provide a temporary JSONL ledger path."""
    return tmp_path / "test_ledger.jsonl"


@pytest.fixture
def sample_config_dict():
    """Provide a minimal valid config dict for testing."""
    return {
        "runtime": {
            "mode": "offline_replay",
            "environment": "uat",
            "region": "US",
            "account_ids": ["ACC001"],
            "confirmation_mode": "confirm",
        },
        "risk": {
            "max_notional_usd": 10000,
            "max_quantity": 1000,
            "max_concentration_pct": 10.0,
            "symbol_whitelist": ["AAPL", "TSLA"],
        },
    }


@pytest.fixture
def sample_config_yaml(tmp_path, sample_config_dict):
    """Write a sample config.yaml and return its path."""
    import yaml

    path = tmp_path / "config.yaml"
    with open(path, "w") as f:
        yaml.dump(sample_config_dict, f)
    return path
