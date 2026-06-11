"""CLI entry point for shadow observation: python -m shadow observe start|stop|status."""

import argparse
import json
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


def _make_runner():
    """Construct runner with default dependencies."""
    from src.shadow.metrics import MetricsCollector
    from src.shadow.runner import ShadowObservationRunner
    from src.shadow.state import ObservationStateStore
    from src.state.ledger import AuditLedger

    ledger = AuditLedger("runtime/shadow_ledger.jsonl")
    metrics = MetricsCollector(ledger, source="shadow")
    state = ObservationStateStore("runtime/shadow_state.db")
    return ShadowObservationRunner(state, metrics, ledger), state


def cmd_start(args):
    config = _load_config()
    from src.shadow.state import ObservationStateStore

    state = ObservationStateStore("runtime/shadow_state.db")
    obs_id = state.start(config)
    print(f"Observation started: {obs_id}")


def cmd_stop(args):
    _, state = _make_runner()
    result = state.stop()
    print(f"Observation stopped: {json.dumps(result, indent=2)}")


def cmd_status(args):
    runner, state = _make_runner()
    status = runner.check_status()
    print(json.dumps(status, indent=2, default=str))


def cmd_summary(args):
    runner, _ = _make_runner()
    content = runner.generate_summary()
    print(content)


def main():
    parser = argparse.ArgumentParser(prog="shadow", description="Shadow observation CLI")
    sub = parser.add_subparsers(dest="command")

    observe = sub.add_parser("observe", help="Observation period commands")
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
