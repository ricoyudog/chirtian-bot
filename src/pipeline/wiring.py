"""Dependency-injection factory for the trading pipeline.

Assembles the real Webull-backed stack from a ``RuntimeConfig`` and selects the
TradingAgents source (real gateway / stub / skip). Also resolves the account id
and constructs a direct-injection instruction for deterministic testing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.analyzer.llm_client import ClaudeCliClient
from src.analyzer.parser import InstructionParser
from src.analyzer.parser_schema import ParsedInstruction
from src.analyzer.ta_gateway import TradingAgentsGateway
from src.analyzer.ta_models import TAResult
from src.config.settings import RuntimeConfig
from src.executor.execution_gate import ExecutionGate
from src.executor.order_builder import OrderBuilder
from src.executor.webull_adapter import WebullCLIAdapter
from src.pipeline.orchestrator import TradingPipeline
from src.portfolio.ledger import PortfolioLedger
from src.portfolio.provider import WebullAccountProvider
from src.portfolio.reconcile import ReconcileGate, Reconciler
from src.portfolio.sizing import SizingEngine
from src.safety.runtime_guard import RuntimeGuard
from src.state.ledger import AuditLedger

TA_REAL = "real"
TA_STUB = "stub"
TA_SKIP = "skip"


@dataclass
class PipelineStack:
    """Fully wired pipeline plus the handles a CLI/operator needs."""

    pipeline: TradingPipeline
    account_id: str
    config: RuntimeConfig
    guard: RuntimeGuard
    adapter: WebullCLIAdapter
    audit_ledger: AuditLedger
    portfolio_ledger: PortfolioLedger
    parser: Optional[InstructionParser]


class StubTAGateway:
    """Deterministic TA gateway — returns a fixed rating.

    Used for first-run validation without the ~30-minute TradingAgents
    dependency, and in tests. ``available=False`` simulates TA unreachable
    so fusion degrades to NEEDS_REVIEW.
    """

    def __init__(
        self,
        *,
        rating: str = "Buy",
        available: bool = True,
        error: Optional[str] = None,
    ) -> None:
        self._rating = rating
        self._available = available
        self._error = error

    def analyze(self, ticker: str, trade_date: str) -> TAResult:
        return TAResult(
            ticker=ticker,
            rating=self._rating if self._available else None,
            available=self._available,
            error=self._error,
        )


def resolve_account(config: RuntimeConfig, override: Optional[str] = None) -> str:
    """Resolve the account id: CLI arg > env > config > error."""
    if override:
        return override
    env = os.environ.get("WEBULL_UAT_ACCOUNT_ID")
    if env:
        return env
    if config.account_ids:
        return config.account_ids[0]
    raise RuntimeError(
        "No account id resolved. Set WEBULL_UAT_ACCOUNT_ID, pass --account, "
        "or set config.runtime.account_ids.",
    )


def make_direct_instruction(
    symbol: str,
    action: str,
    pct: float,
    *,
    post_id: str = "direct",
    sequence: int = 0,
) -> ParsedInstruction:
    """Build a fully-keyed ParsedInstruction for deterministic direct runs."""
    inst = ParsedInstruction(
        post_id=post_id,
        sequence=sequence,
        action=action,
        symbol=symbol.upper(),
        market="US",
        quantity_type="pct",
        quantity_pct=float(pct),
        confidence=1.0,
    )
    return inst.compute_keys()


def build_pipeline(
    config: RuntimeConfig,
    *,
    ta_mode: str = TA_REAL,
    account_id: Optional[str] = None,
    with_parser: bool = False,
    ledger_dir: str | Path = "runtime",
    require_reconcile: Optional[bool] = None,
    confirm_handler: Optional[Any] = None,
) -> PipelineStack:
    """Wire the real Webull-backed pipeline stack.

    Parameters
    ----------
    ta_mode : "real" | "stub" | "skip"
        Source of the TradingAgents double-confirmation.
    with_parser : bool
        Construct an LLM-backed parser (needed for ``run``; not for ``run-direct``).
    """
    ledger_dir = Path(ledger_dir)

    audit_ledger = AuditLedger(ledger_dir / "audit_ledger.jsonl")
    portfolio_ledger = PortfolioLedger(ledger_dir / "portfolio_ledger.jsonl")

    adapter = WebullCLIAdapter()
    provider = WebullAccountProvider(adapter)

    guard = RuntimeGuard(config)
    guard.assert_safe_to_run()  # fail fast on unsafe config

    reconcile_gate = ReconcileGate(
        guard=guard,
        reconciler=Reconciler(),
        ledger=portfolio_ledger,
        reconciliations_dir=ledger_dir / "reconciliations",
    )

    sizing = SizingEngine(config.risk, config.portfolio, portfolio_ledger)
    execution_gate = ExecutionGate(config, audit_ledger)
    order_builder = OrderBuilder()

    ta_gateway = _build_ta_gateway(ta_mode)
    parser = (
        InstructionParser(
            llm_client=ClaudeCliClient(),
            audit_ledger=audit_ledger,
        )
        if with_parser
        else None
    )

    pipeline = TradingPipeline(
        config=config,
        provider=provider,
        sizing_engine=sizing,
        execution_gate=execution_gate,
        runtime_guard=guard,
        order_builder=order_builder,
        broker=adapter,
        audit_ledger=audit_ledger,
        portfolio_ledger=portfolio_ledger,
        ta_gateway=ta_gateway,
        parser=parser,
        reconcile_gate=reconcile_gate,
        require_reconcile=require_reconcile,
        confirm_handler=confirm_handler,
    )

    account = resolve_account(config, account_id)

    return PipelineStack(
        pipeline=pipeline,
        account_id=account,
        config=config,
        guard=guard,
        adapter=adapter,
        audit_ledger=audit_ledger,
        portfolio_ledger=portfolio_ledger,
        parser=parser,
    )


def _build_ta_gateway(ta_mode: str) -> Optional[Any]:
    if ta_mode == TA_REAL:
        return TradingAgentsGateway()
    if ta_mode == TA_STUB:
        return StubTAGateway()
    if ta_mode == TA_SKIP:
        return None
    raise ValueError(
        f"Unknown ta_mode '{ta_mode}'. Expected one of: {TA_REAL}, {TA_STUB}, {TA_SKIP}.",
    )
