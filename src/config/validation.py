"""Config loading, startup validation, and config hash computation."""

import hashlib
import json
from pathlib import Path

import yaml

from src.config.settings import RuntimeConfig


def load_config(path: str | Path) -> RuntimeConfig:
    """Load config from YAML file and return validated RuntimeConfig."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    # YAML has nested structure: {runtime: {...}, risk: {...}}
    # Flatten into the shape RuntimeConfig expects
    flat = {**raw.get("runtime", {}), "risk": raw.get("risk", {})}
    return RuntimeConfig.model_validate(flat)


def validate_startup(config: RuntimeConfig) -> None:
    """Fail-fast startup checks. Raises RuntimeError on unsafe configuration."""
    if config.environment == "prod" and config.confirmation_mode == "auto":
        raise RuntimeError(
            "FATAL: prod environment with auto confirmation is not allowed. "
            "Set confirmation_mode to 'confirm' or switch environment to 'uat'."
        )

    allowed_modes_for_mvp = {"offline_replay", "shadow", "uat_confirm"}
    if config.mode not in allowed_modes_for_mvp:
        raise RuntimeError(
            f"FATAL: mode '{config.mode}' is not yet supported in MVP. "
            f"Allowed modes: {sorted(allowed_modes_for_mvp)}"
        )

    supported_regions = {"US"}
    if config.region not in supported_regions:
        raise RuntimeError(
            f"FATAL: region '{config.region}' is not supported. "
            f"Supported: {sorted(supported_regions)}"
        )


def compute_config_hash(config: RuntimeConfig) -> str:
    """Compute a deterministic SHA-256 hash of the config for audit trails."""
    canonical = json.dumps(config.model_dump(mode="json"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
