"""CLI entry point for the poll daemon: ``python -m src.ops``.

Wires the real Webull-backed pipeline via :func:`build_pipeline`, swaps in
:class:`CrossCheckParser` (3 × DeepSeek V4 Flash cross-check) for the
automatic poll path, then starts the :class:`PollDaemon` tick loop.

Required environment variables
------------------------------
``DEEPSEEK_API_KEY``
    API key for the 3 × DeepSeek V4 Flash cross-check calls.
``WEBULL_UAT_ACCOUNT_ID`` (or ``--account`` / ``config.runtime.account_ids``)
    Webull paper-trading account id.

Optional environment variables
------------------------------
``DEEPSEEK_BASE_URL``
    Override the DeepSeek API base URL (default: ``https://api.deepseek.com``).
``CHRISTIAN_PUBLICATION_IDS``
    Comma-separated Substack publication ids to poll (default: all).
``CHRISTIAN_POST_LIMIT``
    Max posts to fetch per tick (default: 10).

Usage
-----
::

    python -m src.ops --config config.yaml --ta real
    python -m src.ops --ta stub            # smoke test without real TA
    python -m src.ops --tick-interval 5    # tight tick for debugging

SIGTERM triggers a graceful shutdown (≤15s); the lock at
``runtime/daemon.lock`` is released and the in-flight run is recorded as
aborted. A second invocation while one is running exits immediately.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from src.analyzer.parser_crosscheck import CrossCheckParser
from src.config.validation import load_config
from src.ingestion.seen_store import ProcessedPostStore
from src.ingestion.substack_client import SubstackClient
from src.ops.daemon import RUNTIME_DIR, PollDaemon
from src.ops.run_record import RunRecorder
from src.pipeline.wiring import build_pipeline
from src.portfolio.provider import WebullAccountProvider

DEFAULT_CONFIG = "config.yaml"
DEFAULT_LEDGER_DIR = RUNTIME_DIR
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
TA_CHOICES = ("real", "stub", "skip")
TA_DEFAULT = "real"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m src.ops",
        description="Christian Bot poll daemon — 60s tick loop with safety gates.",
    )
    p.add_argument("--config", default=DEFAULT_CONFIG, help="Path to config.yaml")
    p.add_argument(
        "--account",
        default=None,
        help="Webull account id (else env/config resolution).",
    )
    p.add_argument(
        "--ta",
        choices=TA_CHOICES,
        default=TA_DEFAULT,
        help="TradingAgents source (default: real).",
    )
    p.add_argument(
        "--ledger-dir",
        default=str(DEFAULT_LEDGER_DIR),
        help="Runtime/ledger directory (default: runtime).",
    )
    p.add_argument(
        "--tick-interval",
        type=int,
        default=60,
        help="Seconds between ticks (default: 60).",
    )
    p.add_argument(
        "--circuit-breaker-threshold",
        type=int,
        default=5,
        help="Consecutive failures before kill switch (default: 5).",
    )
    p.add_argument(
        "--publication-ids",
        default=os.environ.get("CHRISTIAN_PUBLICATION_IDS"),
        help="Comma-separated Substack publication ids (default: all).",
    )
    p.add_argument(
        "--post-limit",
        type=int,
        default=int(os.environ.get("CHRISTIAN_POST_LIMIT", "10")),
        help="Max posts to fetch per tick (default: 10).",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Log verbosity (default: INFO).",
    )
    return p


def _resolve_publication_ids(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [pid.strip() for pid in raw.split(",") if pid.strip()]


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # --- DeepSeek cross-check parser (required for daemon mode) ------------
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print(
            "FATAL: DEEPSEEK_API_KEY is required for daemon mode "
            "(CrossCheckParser uses 3 × DeepSeek V4 Flash).",
            file=sys.stderr,
        )
        return 2
    base_url = os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL)
    ledger_dir = Path(args.ledger_dir)
    crosscheck_parser = CrossCheckParser(
        deepseek_api_key=api_key,
        deepseek_base_url=base_url,
        runs_dir=ledger_dir,
    )

    # --- Pipeline stack ----------------------------------------------------
    config = load_config(args.config)
    stack = build_pipeline(
        config,
        ta_mode=args.ta,
        account_id=args.account,
        ledger_dir=ledger_dir,
        with_parser=False,
        parser=crosscheck_parser,
    )

    # --- Daemon dependencies ----------------------------------------------
    seen_store = ProcessedPostStore(ledger_dir / "processed_posts.json")
    run_recorder = RunRecorder(runs_dir=ledger_dir)
    provider = WebullAccountProvider(stack.adapter)

    substack_client = SubstackClient()

    daemon = PollDaemon(
        pipeline=stack.pipeline,
        parser=crosscheck_parser,
        substack_client=substack_client,
        seen_store=seen_store,
        account_id=stack.account_id,
        config=config,
        guard=stack.guard,
        run_recorder=run_recorder,
        provider=provider,
        tick_interval_seconds=args.tick_interval,
        circuit_breaker_threshold=args.circuit_breaker_threshold,
        runs_dir=ledger_dir,
        deepseek_api_key=api_key,
        deepseek_base_url=base_url,
        publication_ids=_resolve_publication_ids(args.publication_ids),
        post_limit=args.post_limit,
    )

    # SubstackClient manages a Node.js subprocess; the context manager closes
    # it on exit. The daemon loop blocks here until SIGTERM or circuit break.
    with substack_client:
        daemon.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
