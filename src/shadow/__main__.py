"""CLI entry point for shadow observation: python -m shadow observe start|stop|status|summary.

Live paper-order observation is opt-in: pass ``--live`` (or set ``SHADOW_LIVE=1``).
By default the stack is built in safe dry-run mode — no orders are placed.
"""

import argparse
import json
import os
import warnings
from pathlib import Path


def _load_config():
    """Load runtime config if available."""
    try:
        from src.config.settings import RuntimeConfig
        config_path = Path("config.yaml")
        if config_path.exists():
            import yaml
            with open(config_path) as f:
                data = yaml.safe_load(f)
            return RuntimeConfig(**data.get("runtime", {}))
    except Exception:
        pass
    return None


def _fallback_config():
    """Minimal config for dry-run tooling (status/summary/drill).

    Only used when no config.yaml is present AND the stack is dry-run — never
    used to satisfy a live request (see :func:`_make_runner`).
    """
    from src.config.settings import RiskConfig, RuntimeConfig

    return RuntimeConfig(
        mode="shadow",
        environment="uat",
        region="US",
        account_ids=["shadow"],
        confirmation_mode="auto",
        risk=RiskConfig(
            max_notional_usd=10000,
            max_quantity=1000,
            max_concentration_pct=10.0,
        ),
    )


def _real_account_available(config) -> bool:
    """True if a real account id can be resolved (env var or real config)."""
    if os.environ.get("WEBULL_UAT_ACCOUNT_ID"):
        return True
    return config is not None and bool(config.account_ids)


def _make_runner(dry_run: bool = True):
    """Construct the shadow stack via build_shadow_stack.

    ``dry_run=True`` (default) builds a safe DryRunPipeline; ``dry_run=False``
    opts into a real TradingPipeline wrapped in a ShadowPipelineAdapter.

    Safety: if live mode is requested (``--live`` or ``SHADOW_LIVE=1``) but no
    real account is resolvable, the request falls back to dry-run with a
    warning rather than building a broker-backed pipeline with a bogus account.
    Returns ``(runner, state)``.
    """
    from src.shadow.wiring import build_shadow_stack

    config = _load_config()
    live = (not dry_run) or os.environ.get("SHADOW_LIVE") == "1"

    if live and not _real_account_available(config):
        warnings.warn(
            "Live shadow mode requested but no account is resolvable "
            "(set WEBULL_UAT_ACCOUNT_ID or config.runtime.account_ids); "
            "falling back to dry-run. No orders will be placed.",
            stacklevel=2,
        )
        live = False
        # Honor our refusal: clear the env flag so build_shadow_stack does not
        # re-trigger the live path via its own SHADOW_LIVE check.
        os.environ.pop("SHADOW_LIVE", None)

    if config is None:
        config = _fallback_config()

    stack = build_shadow_stack(
        config,
        ledger_path="runtime/shadow_ledger.jsonl",
        state_db_path="runtime/shadow_state.db",
        incidents_dir="runtime/incidents",
        dry_run=not live,
    )
    return stack["runner"], stack["state"]


def cmd_start(args):
    config = _load_config()
    from src.shadow.state import ObservationStateStore

    state = ObservationStateStore("runtime/shadow_state.db")
    obs_id = state.start(config)
    mode = "LIVE (paper orders)" if args.dry_run is False else "dry-run (no orders)"
    print(f"Observation started: {obs_id}  [{mode}]")


def cmd_stop(args):
    _, state = _make_runner(dry_run=args.dry_run)
    result = state.stop()
    print(f"Observation stopped: {json.dumps(result, indent=2)}")


def cmd_status(args):
    runner, _ = _make_runner(dry_run=args.dry_run)
    status = runner.check_status()
    print(json.dumps(status, indent=2, default=str))


def cmd_summary(args):
    runner, _ = _make_runner(dry_run=args.dry_run)
    content = runner.generate_summary()
    print(content)


def main():
    parser = argparse.ArgumentParser(prog="shadow", description="Shadow observation CLI")
    sub = parser.add_subparsers(dest="command")

    observe = sub.add_parser("observe", help="Observation period commands")
    # Live paper-order observation is opt-in. Default is safe dry-run.
    mode = observe.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        dest="dry_run",
        action="store_false",
        help="Enable real paper-order observation via TradingPipeline (opt-in).",
    )
    mode.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Dry-run mode (default) — no orders are placed.",
    )
    observe.set_defaults(dry_run=True)

    observe_sub = observe.add_subparsers(dest="action")

    observe_sub.add_parser("start", help="Start observation period")
    observe_sub.add_parser("stop", help="Stop observation period")
    observe_sub.add_parser("status", help="Show observation status")
    observe_sub.add_parser("summary", help="Generate shadow run summary")

    args = parser.parse_args()

    if args.command == "observe":
        if args.action == "start":
            cmd_start(args)
        elif args.action == "stop":
            cmd_stop(args)
        elif args.action == "status":
            cmd_status(args)
        elif args.action == "summary":
            cmd_summary(args)
        else:
            observe.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
