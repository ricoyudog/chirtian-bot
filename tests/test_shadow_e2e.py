"""End-to-end shadow tests.

- ``test_shadow_e2e_smoke``: deterministic full-stack smoke using an injected
  fake pipeline (no Webull/Claude dependency), with the clock pinned to a
  Wednesday so the deferred-window path never interferes.
- ``test_shadow_e2e_real_adapter_with_fakes``: the key regression test — a real
  ``TradingPipeline`` (with fake broker/provider/parser/TA) wrapped in the
  ``ShadowPipelineAdapter`` and injected via ``pipeline=``, asserting that a
  ``placed`` outcome surfaces as overall ``success`` with a broker row.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from src.analyzer.parser_schema import ParseResult
from src.config.settings import RiskConfig, RuntimeConfig
from src.executor.execution_gate import ExecutionGate
from src.executor.order_builder import OrderBuilder
from src.pipeline.orchestrator import TradingPipeline
from src.pipeline.wiring import StubTAGateway, make_direct_instruction
from src.portfolio.ledger import PortfolioLedger
from src.portfolio.provider import FakeAccountProvider
from src.portfolio.reconcile import ReconcileGate, Reconciler
from src.portfolio.sizing import SizingEngine
from src.safety.runtime_guard import RuntimeGuard
from src.shadow.pipeline_adapter import ShadowPipelineAdapter
from src.shadow.runner import PipelineResult
from src.shadow.wiring import build_shadow_stack
from src.state.ledger import AuditLedger


# Wednesday 2026-06-10 — a trading day, pinned so signals are never deferred.
def _wednesday():
    return datetime(2026, 6, 10, tzinfo=UTC)


def _config() -> RuntimeConfig:
    return RuntimeConfig(
        mode="shadow",
        environment="uat",
        region="US",
        account_ids=["TEST001"],
        confirmation_mode="auto",
        risk=RiskConfig(
            max_notional_usd=10000,
            max_quantity=1000,
            max_concentration_pct=10.0,
            symbol_whitelist=["AAPL", "TSLA"],
        ),
    )


class _FakePipeline:
    """Deterministic shadow pipeline — emits fixed stage rows, touches nothing."""

    def run(self, text, signal_id):
        return PipelineResult(
            signal_id=signal_id,
            stages=[
                {"stage": "parse", "latency_ms": 10.0, "outcome": "success"},
                {"stage": "ta", "latency_ms": 5.0, "outcome": "ta_skipped"},
                {"stage": "broker", "latency_ms": 20.0, "outcome": "success"},
            ],
            total_latency_ms=35.0,
            outcome="success",
        )


def test_shadow_e2e_smoke(tmp_path, monkeypatch):
    """Full smoke test: start observation → process signal → check status → summary.

    Uses an injected fake pipeline (no Webull/Claude) and a pinned Wednesday clock
    so the run is fully deterministic.
    """
    monkeypatch.chdir(tmp_path)

    config = _config()

    stack = build_shadow_stack(
        config,
        ledger_path=str(tmp_path / "runtime" / "shadow_ledger.jsonl"),
        state_db_path=str(tmp_path / "runtime" / "shadow_state.db"),
        incidents_dir=str(tmp_path / "runtime" / "incidents"),
        pipeline=_FakePipeline(),
    )

    runner = stack["runner"]
    runner._now = _wednesday  # pin clock so signals process (not deferred)
    metrics = stack["metrics"]
    drill = stack["drill"]
    state = stack["state"]

    # Step 1: Start observation period
    obs_id = state.start(config)
    assert obs_id is not None

    # Step 2: Process test signals
    result1 = runner.process_signal("加倉 AAPL 1%", "sig-test-001")
    assert result1.signal_id == "sig-test-001"
    assert result1.outcome == "success"

    result2 = runner.process_signal("賣出 TSLA 0.5%", "sig-test-002")
    assert result2.signal_id == "sig-test-002"

    # Step 3: Check status
    status = runner.check_status()
    assert status["status"] == "active"
    assert status["signals_processed"] == 2

    # Step 4: Check metrics were recorded
    report = metrics.generate_report()
    assert report.total_signals == 2

    # Step 5: Run alert drill
    from datetime import UTC, datetime
    drill_result = drill.run_drill(
        confirm_callback=lambda: datetime.now(UTC).isoformat()
    )
    assert drill_result.result == "PASS"

    # Step 6: Verify drill gate passes
    assert drill.check_drill_passed() is True

    # Step 7: Generate summary
    summary = runner.generate_summary()
    assert "Shadow Run Summary" in summary
    assert "Go/No-Go Readiness" in summary

    # Step 8: Verify files exist
    assert (tmp_path / "runtime" / "shadow_ledger.jsonl").exists()
    assert (tmp_path / "runtime" / "shadow_state.db").exists()
    assert (tmp_path / "runtime" / "incidents").exists()
    summaries_dir = tmp_path / "runtime" / "shadow_summaries"
    assert summaries_dir.exists()
    assert len(list(summaries_dir.glob("*.md"))) == 1

    # Step 9: Stop observation
    final = state.stop()
    assert final["status"] == "completed"  # insufficient signals but we just stop it


class _FakeParser:
    """Returns an EXECUTABLE AAPL BUY instruction keyed to the post_id."""

    def parse(self, post_id, raw_text):
        inst = make_direct_instruction("AAPL", "BUY", 1.0, post_id=post_id)
        return ParseResult(
            post_id=post_id,
            status="EXECUTABLE",
            instructions=[inst],
        )


def _build_real_pipeline_with_fakes(tmp_path) -> TradingPipeline:
    """A real TradingPipeline wired with fakes so a BUY AAPL 1% places."""
    config = _config()
    audit = AuditLedger(tmp_path / "audit.jsonl")
    pledger = PortfolioLedger(tmp_path / "portfolio.jsonl")

    provider = FakeAccountProvider(
        equity_usd=50000.0,
        buying_power_usd=10000.0,
        quotes={"AAPL": _fresh_quote("AAPL", 150.0)},
        account_id="TEST001",
    )
    guard = RuntimeGuard(config)
    sizing = SizingEngine(config.risk, config.portfolio, pledger)
    gate = ExecutionGate(config, audit)
    reconcile_gate = ReconcileGate(guard, Reconciler(), pledger)

    broker = MagicMock()
    broker.preview_order.return_value = {"status": "preview_ok"}
    broker.place_order.return_value = {"order_id": "ORD-1", "status": "submitted"}

    return TradingPipeline(
        config=config,
        provider=provider,
        sizing_engine=sizing,
        execution_gate=gate,
        runtime_guard=guard,
        order_builder=OrderBuilder(),
        broker=broker,
        audit_ledger=audit,
        portfolio_ledger=pledger,
        ta_gateway=StubTAGateway(rating="Buy", available=True),
        reconcile_gate=reconcile_gate,
        require_reconcile=False,
        parser=_FakeParser(),
    )


def _fresh_quote(symbol: str = "AAPL", price: float = 150.0):
    from src.portfolio.models import Quote

    return Quote(symbol=symbol, price=price, timestamp=datetime.now(UTC).isoformat())


def test_shadow_e2e_real_adapter_with_fakes(tmp_path, monkeypatch):
    """A real TradingPipeline (fakes) wrapped in ShadowPipelineAdapter places.

    This is the regression test that catches adapter bugs: one ``placed``
    orchestrator outcome must surface as overall ``success`` with a successful
    broker stage row in the folded PipelineResult.
    """
    monkeypatch.chdir(tmp_path)
    config = _config()

    trading_pipeline = _build_real_pipeline_with_fakes(tmp_path)
    adapter = ShadowPipelineAdapter(trading_pipeline, account_id="TEST001")

    stack = build_shadow_stack(
        config,
        ledger_path=str(tmp_path / "runtime" / "shadow_ledger.jsonl"),
        state_db_path=str(tmp_path / "runtime" / "shadow_state.db"),
        incidents_dir=str(tmp_path / "runtime" / "incidents"),
        pipeline=adapter,
    )
    runner = stack["runner"]
    runner._now = _wednesday
    state = stack["state"]

    state.start(config)
    result = runner.process_signal("加倉 AAPL 1%", "sig-real-001")

    # The adapter folded a `placed` outcome into overall success.
    assert result.signal_id == "sig-real-001"
    assert result.outcome == "success"

    broker_rows = [s for s in result.stages if s["stage"] == "broker"]
    assert broker_rows, "expected a broker stage row for a placed order"
    assert broker_rows[0]["outcome"] == "success"
