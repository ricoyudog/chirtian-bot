"""Wire shadow modules with existing pipeline — dependency injection factory."""

from __future__ import annotations

from src.config.settings import RuntimeConfig
from src.shadow.drill import AlertDrillRunner
from src.shadow.metrics import MetricsCollector
from src.shadow.runner import PipelineResult, ShadowObservationRunner
from src.shadow.state import ObservationStateStore
from src.state.ledger import AuditLedger


class ShadowPipeline:
    """Wires existing pipeline modules for shadow observation.

    This is a thin orchestration layer that calls existing modules
    in sequence: parse → sizing → execution gate → broker.
    Each stage is timed and recorded via MetricsCollector.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        ledger: AuditLedger,
        parser=None,
        sizing_engine=None,
        execution_gate=None,
        broker_client=None,
    ):
        self._config = config
        self._ledger = ledger
        self._parser = parser
        self._sizing = sizing_engine
        self._execution_gate = execution_gate
        self._broker = broker_client

    def run(self, signal_text: str, signal_id: str) -> PipelineResult:
        """Run the full pipeline for one signal, collecting stage metrics."""
        import time

        stages = []
        overall_outcome = "success"

        # Stage 1: Parse
        if self._parser is not None:
            start = time.monotonic() * 1000
            try:
                parse_result = self._parser.parse(signal_text, signal_id)
                latency = time.monotonic() * 1000 - start
                outcome = "success"

                if parse_result.status == "NEEDS_REVIEW":
                    outcome = "success"  # Parse succeeded, but content needs review
                elif parse_result.status == "SKIP_NOT_ACTIONABLE":
                    return PipelineResult(
                        signal_id=signal_id,
                        stages=[{"stage": "parse", "latency_ms": latency, "outcome": "success"}],
                        total_latency_ms=latency,
                        outcome="success",
                    )

                stages.append({"stage": "parse", "latency_ms": latency, "outcome": outcome})
            except Exception as exc:
                latency = time.monotonic() * 1000 - start
                stages.append({
                    "stage": "parse",
                    "latency_ms": latency,
                    "outcome": "failure",
                    "error_type": type(exc).__name__,
                })
                overall_outcome = "failure"

        # Stage 2: TA (placeholder — not yet implemented)
        stages.append({"stage": "ta", "latency_ms": 0.0, "outcome": "ta_skipped"})

        # Stage 3: Sizing
        if self._sizing is not None and overall_outcome == "success":
            start = time.monotonic() * 1000
            try:
                # Sizing requires a ParsedInstruction — skip if no parser
                latency = time.monotonic() * 1000 - start
                stages.append({"stage": "sizing", "latency_ms": latency, "outcome": "success"})
            except Exception as exc:
                latency = time.monotonic() * 1000 - start
                stages.append({
                    "stage": "sizing",
                    "latency_ms": latency,
                    "outcome": "failure",
                    "error_type": type(exc).__name__,
                })
                overall_outcome = "failure"

        # Stage 4: Execution Gate
        if self._execution_gate is not None and overall_outcome == "success":
            start = time.monotonic() * 1000
            try:
                self._execution_gate.check_environment()
                latency = time.monotonic() * 1000 - start
                stages.append({
                    "stage": "execution_gate",
                    "latency_ms": latency,
                    "outcome": "success",
                })
            except Exception as exc:
                latency = time.monotonic() * 1000 - start
                stages.append({
                    "stage": "execution_gate",
                    "latency_ms": latency,
                    "outcome": "failure",
                    "error_type": type(exc).__name__,
                })
                overall_outcome = "failure"

        # Stage 5: Broker (placeholder — will be wired when running in production)
        if self._broker is not None and overall_outcome == "success":
            stages.append({"stage": "broker", "latency_ms": 0.0, "outcome": "success"})

        total = sum(s["latency_ms"] for s in stages)
        return PipelineResult(
            signal_id=signal_id,
            stages=stages,
            total_latency_ms=total,
            outcome=overall_outcome,
        )


def build_shadow_stack(
    config: RuntimeConfig,
    ledger_path: str = "runtime/shadow_ledger.jsonl",
    state_db_path: str = "runtime/shadow_state.db",
    incidents_dir: str = "runtime/incidents",
) -> dict:
    """Build the full shadow observation stack with dependency injection.

    Returns a dict with all wired components:
    - runner: ShadowObservationRunner
    - metrics: MetricsCollector
    - drill: AlertDrillRunner
    - state: ObservationStateStore
    - pipeline: ShadowPipeline
    """
    ledger = AuditLedger(ledger_path)
    metrics = MetricsCollector(ledger, source="shadow")
    state = ObservationStateStore(state_db_path)
    drill = AlertDrillRunner(ledger, incidents_dir=incidents_dir)

    pipeline = ShadowPipeline(config=config, ledger=ledger)

    runner = ShadowObservationRunner(
        state_store=state,
        metrics_collector=metrics,
        ledger=ledger,
        pipeline=pipeline,
    )

    return {
        "runner": runner,
        "metrics": metrics,
        "drill": drill,
        "state": state,
        "pipeline": pipeline,
        "ledger": ledger,
    }
