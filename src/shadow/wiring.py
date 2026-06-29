"""Wire shadow modules with the trading pipeline — dependency injection factory.

Default behaviour is **safe (dry-run)**: a :class:`DryRunPipeline` that never
contacts a broker or LLM, so dashboards/summaries keep rendering. Real
paper-order observation requires explicit opt-in — ``dry_run=False`` or
``SHADOW_LIVE=1`` — which builds a real :class:`TradingPipeline` and wraps it in
a :class:`ShadowPipelineAdapter` (see wiki/decisions/2026-06-15-pipeline-orchestrator.md).

Safety invariant: a bare ``build_shadow_stack(config, ...)`` with no DI kwargs
never constructs a ``TradingPipeline`` backed by the real ``WebullCLIAdapter``.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any, Optional

from src.config.settings import RuntimeConfig
from src.shadow.drill import AlertDrillRunner
from src.shadow.metrics import MetricsCollector
from src.shadow.runner import Pipeline, PipelineResult, ShadowObservationRunner
from src.shadow.state import ObservationStateStore
from src.state.ledger import AuditLedger


class DryRunPipeline:
    """Deterministic dry-run pipeline — returns a fixed, valid ``PipelineResult``.

    No broker/LLM is contacted. The fixed stage rows let shadow dashboards and
    summaries render in dry-run mode. For real paper-order observation, build a
    live stack (``dry_run=False`` / ``SHADOW_LIVE=1``), which wraps a real
    ``TradingPipeline`` via :class:`ShadowPipelineAdapter`.
    """

    _DRY_RUN_STAGES = [
        {"stage": "parse", "latency_ms": 0.0, "outcome": "success"},
        {"stage": "llm", "latency_ms": 0.0, "outcome": "success"},
        {"stage": "ta", "latency_ms": 0.0, "outcome": "ta_skipped"},
        {"stage": "sizing", "latency_ms": 0.0, "outcome": "success"},
        {"stage": "execution_gate", "latency_ms": 0.0, "outcome": "success"},
        {"stage": "broker", "latency_ms": 0.0, "outcome": "success"},
    ]

    def run(self, signal_text: str, signal_id: str) -> PipelineResult:
        return PipelineResult(
            signal_id=signal_id,
            stages=[dict(row) for row in self._DRY_RUN_STAGES],
            total_latency_ms=0.0,
            outcome="success",
        )


def build_shadow_stack(
    config: RuntimeConfig,
    *,
    ledger_path: str = "runtime/shadow_ledger.jsonl",
    state_db_path: str = "runtime/shadow_state.db",
    incidents_dir: str = "runtime/incidents",
    pipeline: Optional[Pipeline] = None,
    ta_mode: str = "skip",
    with_parser: bool = True,
    account_id: Optional[str] = None,
    broker: Any = None,
    parser: Any = None,
    ta_gateway: Optional[Any] = None,
    require_reconcile: Optional[bool] = None,
    confirm_handler: Optional[Any] = None,
    dry_run: bool = True,
) -> dict:
    """Build the full shadow observation stack with dependency injection.

    Returns a dict with all wired components:
    - runner: ShadowObservationRunner
    - metrics: MetricsCollector
    - drill: AlertDrillRunner
    - state: ObservationStateStore
    - pipeline: the shadow Pipeline (DryRunPipeline, an injected pipeline, or a
      ShadowPipelineAdapter wrapping a real TradingPipeline)
    - ledger: AuditLedger
    - adapter: ShadowPipelineAdapter when a live stack was built, else None
    - trading_stack: PipelineStack when a live stack was built, else None

    Resolution:
    - ``pipeline`` non-None → use it directly (full DI test path; no guard).
    - otherwise ``live = (not dry_run) or SHADOW_LIVE=="1"``:
        * live  → ``_build_real_pipeline`` (real TradingPipeline via build_pipeline
          + override kwargs, wrapped in ShadowPipelineAdapter).
        * else  → DryRunPipeline + a warning (default, safe).
    """
    ledger = AuditLedger(ledger_path)
    metrics = MetricsCollector(ledger, source="shadow")
    state = ObservationStateStore(state_db_path)
    drill = AlertDrillRunner(ledger, incidents_dir=incidents_dir)

    adapter: Optional[Any] = None
    trading_stack: Optional[Any] = None

    if pipeline is not None:
        # Full DI (test path) — trust the caller, do not guard.
        shadow_pipeline = pipeline
    else:
        live = (not dry_run) or os.environ.get("SHADOW_LIVE") == "1"
        if live:
            shadow_pipeline, adapter, trading_stack = _build_real_pipeline(
                config,
                ledger_path=ledger_path,
                ta_mode=ta_mode,
                with_parser=with_parser,
                account_id=account_id,
                broker=broker,
                parser=parser,
                ta_gateway=ta_gateway,
                require_reconcile=require_reconcile,
                confirm_handler=confirm_handler,
            )
        else:
            warnings.warn(
                "Shadow stack built in dry-run mode — no orders are placed. "
                "Pass dry_run=False or set SHADOW_LIVE=1 for real paper-order "
                "observation.",
                stacklevel=2,
            )
            shadow_pipeline = DryRunPipeline()

    runner = ShadowObservationRunner(
        state_store=state,
        metrics_collector=metrics,
        ledger=ledger,
        pipeline=shadow_pipeline,
    )

    return {
        "runner": runner,
        "metrics": metrics,
        "drill": drill,
        "state": state,
        "pipeline": shadow_pipeline,
        "ledger": ledger,
        "adapter": adapter,
        "trading_stack": trading_stack,
    }


def _build_real_pipeline(
    config: RuntimeConfig,
    *,
    ledger_path: str,
    ta_mode: str,
    with_parser: bool,
    account_id: Optional[str],
    broker: Any,
    parser: Any,
    ta_gateway: Optional[Any],
    require_reconcile: Optional[bool],
    confirm_handler: Optional[Any],
) -> tuple[Any, Any, Any]:
    """Build a real Webull-backed TradingPipeline wrapped in a ShadowPipelineAdapter.

    Ledgers are co-located with the shadow ledger (``runtime/``) so live shadow
    observation writes audit/portfolio ledgers next to the shadow ledger.
    """
    from src.pipeline.wiring import build_pipeline
    from src.shadow.pipeline_adapter import ShadowPipelineAdapter

    ledger_dir = Path(ledger_path).parent
    stack = build_pipeline(
        config,
        ta_mode=ta_mode,
        with_parser=with_parser,
        ledger_dir=ledger_dir,
        account_id=account_id,
        require_reconcile=require_reconcile,
        confirm_handler=confirm_handler,
        broker=broker,
        parser=parser,
        ta_gateway=ta_gateway,
    )
    adapter = ShadowPipelineAdapter(stack.pipeline, stack.account_id)
    return adapter, adapter, stack
