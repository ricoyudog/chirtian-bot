"""End-to-end trading orchestrator.

Wires the existing modules into a single executable pipeline::

    parse → TA fusion → snapshot → reconcile/bootstrap → sizing
         → execution gate → preview → confirm → place → record

All stages call existing, unit-tested modules. This module is the *glue*:
it owns ordering, the reconcile-bootstrap workaround for fresh accounts, and
the per-instruction outcome bookkeeping. Fail-closed semantics are preserved:
TA unavailable → NEEDS_REVIEW, reconcile mismatch → stop-the-world, idempotent
duplicate → blocked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Optional

from src.analyzer.decision_fusion import (
    FUSION_APPROVE,
    FUSION_NEEDS_REVIEW,
    FUSION_REJECT,
    FusionDecision,
    fuse,
)
from src.analyzer.parser_schema import ParsedInstruction
from src.analyzer.ta_models import TAResult
from src.config.settings import RuntimeConfig
from src.executor.exceptions import DuplicateExecutionError
from src.executor.factory import build_execution_intent
from src.executor.models import ExecutionAttempt, ExecutionIntent
from src.executor.order_builder import OrderBuilder, compute_request_hash
from src.safety.runtime_guard import RuntimeGuard
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent

# ---------------------------------------------------------------------------
# Outcome constants
# ---------------------------------------------------------------------------

OUTCOME_PLACED = "placed"
OUTCOME_SKIPPED = "skipped"
OUTCOME_NEEDS_REVIEW = "needs_review"
OUTCOME_REJECTED = "rejected"
OUTCOME_BLOCKED = "blocked"  # reconcile mismatch / safety gate / preview failure


@dataclass
class InstructionOutcome:
    """Result of processing one instruction end-to-end."""

    instruction_id: str
    symbol: str
    action: str
    outcome: str
    reason: str = ""
    fusion_status: Optional[str] = None
    ta_rating: Optional[str] = None
    sizing_status: Optional[str] = None
    order_quantity: int = 0
    limit_price: Optional[float] = None
    broker_order_id: Optional[str] = None
    preview: Optional[dict] = None
    place_result: Optional[dict] = None
    error: Optional[str] = None

    @property
    def placed(self) -> bool:
        return self.outcome == OUTCOME_PLACED


# Type of an optional confirmation handler for confirmation_mode="confirm".
# Receives an ExecutionIntent, returns the (possibly reduced) intent to place,
# or None / an intent with terminal status to abort.
ConfirmationHandler = Callable[[ExecutionIntent], Optional[ExecutionIntent]]


class TradingPipeline:
    """Orchestrates the full trade pipeline for a single account.

    Dependencies are injected so tests can swap in fakes/mocks. ``ta_gateway``
    is optional: ``None`` means skip double-confirmation (pass the Christian
    instruction straight through). A non-None gateway must implement
    ``analyze(ticker, trade_date) -> TAResult``.
    """

    def __init__(
        self,
        *,
        config: RuntimeConfig,
        provider: Any,  # AccountDataProvider
        sizing_engine: Any,  # SizingEngine
        execution_gate: Any,  # ExecutionGate
        runtime_guard: RuntimeGuard,
        order_builder: OrderBuilder,
        broker: Any,  # BrokerClient
        audit_ledger: AuditLedger,
        portfolio_ledger: Any,  # PortfolioLedger
        ta_gateway: Optional[Any] = None,
        parser: Any = None,  # InstructionParser
        reconcile_gate: Optional[Any] = None,
        require_reconcile: Optional[bool] = None,
        confirm_handler: Optional[ConfirmationHandler] = None,
    ) -> None:
        self._config = config
        self._provider = provider
        self._sizing = sizing_engine
        self._execution_gate = execution_gate
        self._guard = runtime_guard
        self._order_builder = order_builder
        self._broker = broker
        self._audit = audit_ledger
        self._portfolio_ledger = portfolio_ledger
        self._ta_gateway = ta_gateway
        self._parser = parser
        self._reconcile_gate = reconcile_gate
        self._require_reconcile = (
            require_reconcile
            if require_reconcile is not None
            else config.portfolio.require_reconcile_before_sizing
        )
        self._confirm_handler = confirm_handler

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    def process_post(
        self,
        post_id: str,
        raw_text: str,
        account_id: str,
    ) -> list[InstructionOutcome]:
        """Parse a post and process every instruction it yields."""
        if self._parser is None:
            raise RuntimeError(
                "No parser configured — use process_instruction() directly "
                "or pass a parser to the pipeline.",
            )

        parse_result = self._parser.parse(post_id, raw_text)

        if parse_result.status != "EXECUTABLE":
            return [
                InstructionOutcome(
                    instruction_id=post_id,
                    symbol="",
                    action="",
                    outcome=OUTCOME_SKIPPED,
                    reason=f"PARSE_{parse_result.status}",
                ),
            ]

        return [self.process_instruction(inst, account_id) for inst in parse_result.instructions]

    def process_instruction(
        self,
        instruction: ParsedInstruction,
        account_id: str,
    ) -> InstructionOutcome:
        """Run one instruction through the full pipeline."""
        oid = instruction.instruction_id
        symbol = instruction.symbol
        action = instruction.action

        # 0. MVP scope guards (fail-closed for unsupported instruments)
        scope_outcome = self._scope_check(instruction)
        if scope_outcome is not None:
            return scope_outcome

        # 1+2. TA + decision fusion
        decision = self._fuse(instruction)
        if decision.fusion_status == FUSION_REJECT:
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_REJECTED,
                reason=decision.reason,
                fusion_status=decision.fusion_status,
                ta_rating=decision.ta_rating,
            )
        if decision.fusion_status == FUSION_NEEDS_REVIEW:
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_NEEDS_REVIEW,
                reason=decision.reason,
                fusion_status=decision.fusion_status,
                ta_rating=decision.ta_rating,
            )

        # 3. Apply fused quantity (MODIFY halves it)
        fused_pct = decision.suggested_quantity_pct
        if fused_pct is not None and fused_pct != instruction.quantity_pct:
            instruction = instruction.model_copy(update={"quantity_pct": fused_pct})

        # 4. Account snapshot
        snapshot = self._provider.get_snapshot(account_id)

        # 5. Reconcile / bootstrap (fail-closed stop-the-world on mismatch)
        if self._reconcile_or_bootstrap(snapshot, account_id):
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_BLOCKED,
                reason="RECONCILE_MISMATCH",
                fusion_status=decision.fusion_status,
                ta_rating=decision.ta_rating,
            )

        # 6. Sizing
        quote = self._provider.get_quote(symbol)
        sizing = self._sizing.size(instruction, snapshot, quote)

        # 7. Build execution intent
        intent = build_execution_intent(sizing, self._config)
        if intent is None:
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_SKIPPED,
                reason=f"SIZING_{sizing.sizing_status}",
                fusion_status=decision.fusion_status,
                ta_rating=decision.ta_rating,
                sizing_status=sizing.sizing_status,
            )

        # 8. Pre-flight gates
        self._execution_gate.check_environment()
        try:
            self._execution_gate.check_idempotency(intent.idempotency_key)
        except DuplicateExecutionError:
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_BLOCKED,
                reason="DUPLICATE_EXECUTION",
                fusion_status=decision.fusion_status,
                ta_rating=decision.ta_rating,
                sizing_status=sizing.sizing_status,
                order_quantity=intent.quantity,
                limit_price=intent.limit_price,
            )
        self._guard.assert_mutation_allowed()

        # 9. Build order JSON + preview (fail-closed on preview error)
        order_json = self._order_builder.build_order_json(intent)
        try:
            preview = self._broker.preview_order(account_id, order_json)
        except Exception as exc:  # broker error → do not place
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_BLOCKED,
                reason="PREVIEW_FAILED",
                fusion_status=decision.fusion_status,
                sizing_status=sizing.sizing_status,
                order_quantity=intent.quantity,
                limit_price=intent.limit_price,
                error=str(exc),
            )

        # 10. Confirmation (auto → skip; confirm → handler)
        if self._config.confirmation_mode == "confirm":
            confirmed = self._await_confirmation(intent)
            if confirmed is None or confirmed.status in ("cancelled", "expired_review"):
                return InstructionOutcome(
                    instruction_id=oid,
                    symbol=symbol,
                    action=action,
                    outcome=OUTCOME_SKIPPED,
                    reason="CONFIRMATION_NOT_APPROVED",
                    fusion_status=decision.fusion_status,
                    preview=preview,
                )
            intent = confirmed

        # 11. Place order
        try:
            place_result = self._broker.place_order(account_id, order_json)
        except Exception as exc:
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_BLOCKED,
                reason="PLACE_FAILED",
                fusion_status=decision.fusion_status,
                ta_rating=decision.ta_rating,
                sizing_status=sizing.sizing_status,
                order_quantity=intent.quantity,
                limit_price=intent.limit_price,
                preview=preview,
                error=str(exc),
            )
        broker_order_id = None
        if isinstance(place_result, dict):
            broker_order_id = place_result.get("order_id") or place_result.get("broker_order_id")

        # 12. Record attempt + portfolio event + refresh baseline
        self._record_success(intent, order_json, place_result, broker_order_id)
        self._refresh_baseline(account_id)

        return InstructionOutcome(
            instruction_id=oid,
            symbol=symbol,
            action=action,
            outcome=OUTCOME_PLACED,
            reason="OK",
            fusion_status=decision.fusion_status,
            ta_rating=decision.ta_rating,
            sizing_status=sizing.sizing_status,
            order_quantity=intent.quantity,
            limit_price=intent.limit_price,
            broker_order_id=broker_order_id,
            preview=preview,
            place_result=place_result,
        )

    # ------------------------------------------------------------------
    # Stage helpers
    # ------------------------------------------------------------------

    def _scope_check(self, instruction: ParsedInstruction) -> Optional[InstructionOutcome]:
        """Reject unsupported instruments/markets/symbols before fusion."""
        oid = instruction.instruction_id
        symbol = instruction.symbol
        action = instruction.action

        if instruction.market != "US":
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_NEEDS_REVIEW,
                reason="NON_US_MARKET",
            )
        whitelist = self._config.risk.symbol_whitelist
        if whitelist and symbol.upper() not in [s.upper() for s in whitelist]:
            return InstructionOutcome(
                instruction_id=oid,
                symbol=symbol,
                action=action,
                outcome=OUTCOME_NEEDS_REVIEW,
                reason="SYMBOL_NOT_WHITELISTED",
            )
        return None

    def _fuse(self, instruction: ParsedInstruction) -> FusionDecision:
        """Run TA + fusion. ta_gateway=None → passthrough APPROVE."""
        qty_pct = self._quantity_pct_for_fusion(instruction)

        if self._ta_gateway is None:
            return FusionDecision(
                instruction_id=instruction.instruction_id,
                symbol=instruction.symbol,
                christian_action=instruction.action,
                fusion_status=FUSION_APPROVE,
                ta_rating=None,
                ta_available=False,
                reason="TA_SKIPPED",
                suggested_quantity_pct=qty_pct,
                original_quantity_pct=qty_pct,
            )

        ta: TAResult = self._ta_gateway.analyze(
            instruction.symbol,
            date.today().isoformat(),
        )
        return fuse(
            christian_action=instruction.action,
            symbol=instruction.symbol,
            instruction_id=instruction.instruction_id,
            quantity_pct=qty_pct,
            ta_result=ta,
        )

    @staticmethod
    def _quantity_pct_for_fusion(instruction: ParsedInstruction) -> float:
        if instruction.quantity_type == "all":
            return 100.0
        return instruction.quantity_pct if instruction.quantity_pct is not None else 0.0

    def _reconcile_or_bootstrap(
        self,
        snapshot: Any,
        account_id: str,
    ) -> bool:
        """Ensure the runtime guard is OK before sizing.

        Returns True if execution is blocked (stop-the-world).

        - No local baseline → bootstrap: trust broker as initial truth.
        - Baseline + reconcile enabled → diff; mismatch activates stop.
        - Baseline + reconcile disabled → adopt broker snapshot, mark OK.
        """
        baseline = self._portfolio_ledger.get_baseline()

        if baseline is None:
            self._portfolio_ledger.record_baseline(snapshot)
            self._guard.mark_reconcile_ok()
            self._audit.append(
                AuditEvent(
                    event_type="bootstrap_sync",
                    source="TradingPipeline",
                    data={
                        "account_id": account_id,
                        "equity_usd": snapshot.equity_usd,
                        "buying_power_usd": snapshot.buying_power_usd,
                        "position_count": len(snapshot.positions),
                        "open_order_count": len(snapshot.open_orders),
                    },
                    correlation_id=account_id,
                )
            )
            return False

        if self._reconcile_gate is not None and self._require_reconcile:
            self._reconcile_gate.check_and_gate(baseline, snapshot)
        else:
            self._portfolio_ledger.record_baseline(snapshot)
            self._guard.mark_reconcile_ok()

        return self._guard.is_stopped

    def _await_confirmation(self, intent: ExecutionIntent) -> Optional[ExecutionIntent]:
        if self._confirm_handler is None:
            raise NotImplementedError(
                "confirmation_mode='confirm' requires a confirmation handler. "
                "Use confirmation_mode='auto' for paper trading, or inject a "
                "confirm_handler(intent) -> ExecutionIntent | None.",
            )
        return self._confirm_handler(intent)

    def _record_success(
        self,
        intent: ExecutionIntent,
        order_json: dict,
        place_result: Any,
        broker_order_id: Optional[str],
    ) -> None:
        request_hash = compute_request_hash(order_json)
        response = place_result if isinstance(place_result, dict) else {"raw": str(place_result)}
        attempt = ExecutionAttempt(
            execution_id=intent.execution_id,
            idempotency_key=intent.idempotency_key,
            attempt_no=1,
            operation="place_order",
            request_hash=request_hash,
            broker_order_id=broker_order_id,
            status="success",
            response=response,
        )
        # record_attempt persists the attempt (including idempotency_key) so a
        # later check_idempotency with the same key blocks a duplicate place.
        self._execution_gate.record_attempt(attempt)
        self._portfolio_ledger.append(
            "order_placed",
            {
                "instruction_id": intent.instruction_id,
                "symbol": intent.symbol,
                "side": intent.side,
                "quantity": intent.quantity,
                "limit_price": intent.limit_price,
                "broker_order_id": broker_order_id,
                "idempotency_key": intent.idempotency_key,
            },
            correlation_id=intent.instruction_id,
        )

    def _refresh_baseline(self, account_id: str) -> None:
        """Re-baseline from broker after our own trade so the next reconcile
        reflects our action rather than flagging it as divergence."""
        try:
            new_snapshot = self._provider.get_snapshot(account_id)
            self._portfolio_ledger.record_baseline(new_snapshot)
        except Exception:
            # Best-effort: a stale baseline will surface as a reconcile
            # mismatch on the next run, which is the safe failure mode.
            pass
