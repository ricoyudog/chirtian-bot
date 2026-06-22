"""CLI for the trading pipeline.

Examples
--------
Direct instruction (fastest path to a real paper order)::

    python -m src.pipeline run-direct --symbol AAPL --action BUY --pct 1 --ta real
    python -m src.pipeline run-direct --symbol AAPL --action BUY --pct 1 --ta stub

Full real parse of a Christian post::

    python -m src.pipeline run --text "加倉AAPL 1%" --post-id smoke001 --ta real

Inspect recent activity::

    python -m src.pipeline status
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from src.config.validation import load_config
from src.pipeline.wiring import (
    TA_REAL,
    TA_SKIP,
    TA_STUB,
    build_pipeline,
    make_direct_instruction,
)

DEFAULT_CONFIG = "config.yaml"
DEFAULT_LEDGER_DIR = "runtime"
TA_CHOICES = (TA_REAL, TA_STUB, TA_SKIP)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_run_direct(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    stack = build_pipeline(
        config,
        ta_mode=args.ta,
        account_id=args.account,
        ledger_dir=args.ledger_dir,
        require_reconcile=False if args.no_require_reconcile else None,
        with_parser=False,
    )

    instruction = make_direct_instruction(args.symbol, args.action, args.pct)
    outcome = stack.pipeline.process_instruction(instruction, stack.account_id)
    _print_outcomes([outcome])
    return 0 if outcome.placed else 1


def cmd_run(args: argparse.Namespace) -> int:
    if not args.text and not args.post_file:
        raise SystemExit("run requires --text or --post-file")

    config = load_config(args.config)
    stack = build_pipeline(
        config,
        ta_mode=args.ta,
        account_id=args.account,
        ledger_dir=args.ledger_dir,
        require_reconcile=False if args.no_require_reconcile else None,
        with_parser=True,
    )

    if args.post_file:
        text = Path(args.post_file).read_text()
    else:
        text = args.text
    post_id = args.post_id or "cli-run"

    outcomes = stack.pipeline.process_post(post_id, text, stack.account_id)
    _print_outcomes(outcomes)
    placed = any(o.placed for o in outcomes)
    return 0 if placed else 1


def cmd_status(args: argparse.Namespace) -> int:
    ledger_dir = Path(args.ledger_dir)
    audit_path = ledger_dir / "audit_ledger.jsonl"
    portfolio_path = ledger_dir / "portfolio_ledger.jsonl"

    attempts = _read_jsonl(audit_path)
    placements = _read_jsonl(portfolio_path)

    exec_attempts = [e for e in attempts if e.get("event_type") == "execution_attempt"]
    orders = [e for e in placements if e.get("type") == "order_placed"]
    bootstraps = [e for e in attempts if e.get("event_type") == "bootstrap_sync"]

    summary = {
        "account_id": args.account,
        "audit_ledger": str(audit_path),
        "portfolio_ledger": str(portfolio_path),
        "bootstrap_syncs": len(bootstraps),
        "execution_attempts": len(exec_attempts),
        "orders_placed": len(orders),
        "recent_orders": orders[-5:],
        "recent_attempts": [
            {
                "operation": e.get("data", {}).get("operation"),
                "status": e.get("data", {}).get("status"),
                "broker_order_id": e.get("data", {}).get("broker_order_id"),
                "timestamp": e.get("timestamp"),
            }
            for e in exec_attempts[-5:]
        ],
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


def cmd_poll(args: argparse.Namespace) -> int:
    """Poll Substack for new Christian posts → parse → TA → sizing → place.

    Uses a seen-state store so a re-poll does not re-process a post.
    """
    from src.ingestion.poll import poll_once
    from src.ingestion.seen_store import ProcessedPostStore
    from src.ingestion.substack_client import SubstackClient

    config = load_config(args.config)
    stack = build_pipeline(
        config,
        ta_mode=args.ta,
        account_id=args.account,
        ledger_dir=args.ledger_dir,
        require_reconcile=False if args.no_require_reconcile else None,
        with_parser=True,
    )
    if stack.parser is None:
        raise SystemExit("poll requires a parser")

    seen = ProcessedPostStore(Path(args.ledger_dir) / "processed_posts.json")
    pub_ids = args.publication_ids.split(",") if args.publication_ids else None

    with SubstackClient() as client:
        all_outcomes = poll_once(
            client=client,
            parser=stack.parser,
            pipeline=stack.pipeline,
            seen_store=seen,
            account_id=stack.account_id,
            publication_ids=pub_ids,
            limit=args.limit,
        )

    _print_outcomes(all_outcomes)
    print(f"\nProcessed {len(all_outcomes)} instruction outcome(s).")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_outcomes(outcomes) -> None:
    payload = [asdict(o) for o in outcomes]
    print(json.dumps(payload, indent=2, default=str))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", default=DEFAULT_CONFIG, help="Path to config.yaml")
    p.add_argument("--account", default=None, help="Account id (else env/config)")
    p.add_argument(
        "--ta",
        choices=TA_CHOICES,
        default=TA_REAL,
        help="TradingAgents source (default: real)",
    )
    p.add_argument("--ledger-dir", default=DEFAULT_LEDGER_DIR, help="Ledger directory")
    p.add_argument(
        "--no-require-reconcile",
        action="store_true",
        help="Skip reconcile gate (bootstrap only)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="Christian Bot end-to-end trading pipeline (paper/UAT).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_direct = sub.add_parser("run-direct", help="Inject a direct instruction (no LLM parser)")
    p_direct.add_argument("--symbol", required=True)
    p_direct.add_argument("--action", required=True, choices=["BUY", "SELL"])
    p_direct.add_argument("--pct", type=float, required=True, help="Quantity %% of equity/position")
    p_direct.add_argument("--post-id", default="direct")
    _add_common(p_direct)
    p_direct.set_defaults(func=cmd_run_direct)

    p_run = sub.add_parser("run", help="Parse a post then execute")
    p_run.add_argument("--text", default=None, help="Inline post text")
    p_run.add_argument("--post-file", default=None, help="Path to a post text file")
    p_run.add_argument("--post-id", default=None)
    _add_common(p_run)
    p_run.set_defaults(func=cmd_run)

    p_poll = sub.add_parser("poll", help="Poll Substack → parse → TA → place")
    p_poll.add_argument(
        "--publication-ids", default=None,
        help="Comma-separated Substack publication ids (default: all subscriptions)",
    )
    p_poll.add_argument("--limit", type=int, default=10, help="Max posts to fetch")
    _add_common(p_poll)
    p_poll.set_defaults(func=cmd_poll)

    p_status = sub.add_parser("status", help="Show recent pipeline activity")
    p_status.add_argument("--ledger-dir", default=DEFAULT_LEDGER_DIR)
    p_status.add_argument("--account", default=None)
    p_status.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
