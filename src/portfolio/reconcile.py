"""Reconciler — compare local portfolio snapshot against broker data."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from src.portfolio.ledger import PortfolioLedger
from src.portfolio.models import PortfolioSnapshot, ReconcileDifference, ReconcileResult
from src.safety.runtime_guard import RuntimeGuard


class Reconciler:
    """Compare local portfolio snapshot against broker snapshot.

    Tolerance (D6):
    - Position quantity: ±0 (exact match)
    - Buying power: ±$1 or 0.1%, whichever is larger
    - Open orders: order_id set exact match
    """

    # Tolerance constants
    BUYING_POWER_ABS_TOLERANCE = 1.0  # $1
    BUYING_POWER_PCT_TOLERANCE = 0.001  # 0.1%

    def reconcile(
        self,
        local: PortfolioSnapshot,
        broker: PortfolioSnapshot,
    ) -> ReconcileResult:
        """Compare local vs broker snapshots and return differences."""
        reconcile_id = f"recon_{uuid.uuid4().hex[:12]}"
        differences: list[ReconcileDifference] = []

        # Compare positions
        differences.extend(self._compare_positions(local, broker))

        # Compare buying power
        differences.extend(self._compare_buying_power(local, broker))

        # Compare open orders
        differences.extend(self._compare_open_orders(local, broker))

        status = "mismatch" if any(d.exceeded for d in differences) else "ok"

        return ReconcileResult(
            reconcile_id=reconcile_id,
            status=status,
            local_snapshot_hash=self._hash_snapshot(local),
            broker_snapshot_hash=self._hash_snapshot(broker),
            differences=differences,
            action_taken="blocked_all_execution" if status == "mismatch" else "none",
            requires_manual_clear=status == "mismatch",
        )

    # ------------------------------------------------------------------
    # Position comparison (exact match, D6)
    # ------------------------------------------------------------------

    def _compare_positions(
        self, local: PortfolioSnapshot, broker: PortfolioSnapshot
    ) -> list[ReconcileDifference]:
        diffs: list[ReconcileDifference] = []
        broker_by_symbol = {p.symbol.upper(): p for p in broker.positions}
        seen = set()

        for local_pos in local.positions:
            sym = local_pos.symbol.upper()
            seen.add(sym)
            broker_pos = broker_by_symbol.get(sym)

            if broker_pos is None:
                diffs.append(
                    ReconcileDifference(
                        field=f"position.{sym}.exists",
                        local_value=True,
                        broker_value=False,
                        tolerance=False,
                        exceeded=True,
                    )
                )
            elif local_pos.quantity != broker_pos.quantity:
                diffs.append(
                    ReconcileDifference(
                        field=f"position.{sym}.quantity",
                        local_value=local_pos.quantity,
                        broker_value=broker_pos.quantity,
                        tolerance=0,
                        exceeded=True,
                    )
                )

        # Check for positions in broker but not in local
        for broker_pos in broker.positions:
            sym = broker_pos.symbol.upper()
            if sym not in seen:
                diffs.append(
                    ReconcileDifference(
                        field=f"position.{sym}.exists",
                        local_value=False,
                        broker_value=True,
                        tolerance=False,
                        exceeded=True,
                    )
                )

        return diffs

    # ------------------------------------------------------------------
    # Buying power comparison (±$1 or 0.1%, D6)
    # ------------------------------------------------------------------

    def _compare_buying_power(
        self, local: PortfolioSnapshot, broker: PortfolioSnapshot
    ) -> list[ReconcileDifference]:
        delta = abs(local.buying_power_usd - broker.buying_power_usd)
        tolerance = max(
            self.BUYING_POWER_ABS_TOLERANCE,
            broker.buying_power_usd * self.BUYING_POWER_PCT_TOLERANCE,
        )
        exceeded = delta > tolerance

        if delta > 0 or exceeded:
            return [
                ReconcileDifference(
                    field="buying_power",
                    local_value=local.buying_power_usd,
                    broker_value=broker.buying_power_usd,
                    tolerance=round(tolerance, 2),
                    exceeded=exceeded,
                )
            ]
        return []

    # ------------------------------------------------------------------
    # Open order comparison (order_id set exact match, D6)
    # ------------------------------------------------------------------

    def _compare_open_orders(
        self, local: PortfolioSnapshot, broker: PortfolioSnapshot
    ) -> list[ReconcileDifference]:
        local_ids = {o.order_id for o in local.open_orders}
        broker_ids = {o.order_id for o in broker.open_orders}

        diffs: list[ReconcileDifference] = []

        missing_in_broker = local_ids - broker_ids
        if missing_in_broker:
            diffs.append(
                ReconcileDifference(
                    field="open_orders.missing_in_broker",
                    local_value=sorted(missing_in_broker),
                    broker_value=[],
                    tolerance=[],
                    exceeded=True,
                )
            )

        extra_in_broker = broker_ids - local_ids
        if extra_in_broker:
            diffs.append(
                ReconcileDifference(
                    field="open_orders.extra_in_broker",
                    local_value=[],
                    broker_value=sorted(extra_in_broker),
                    tolerance=[],
                    exceeded=True,
                )
            )

        return diffs

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_snapshot(snapshot: PortfolioSnapshot) -> str:
        """Compute a deterministic hash of the snapshot for comparison."""
        data = snapshot.model_dump_json()
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class ReconcileGate:
    """Orchestrates reconcile checks and stop-the-world state.

    Flow:
    1. Reconciler.compare() → ReconcileResult
    2. ReconcileGate.check_and_gate() → updates guard + writes ledger + diff report
    3. If mismatch → guard.activate_stop() → all execution blocked
    4. Manual clear required → guard.deactivate_stop()
    5. Successful reconcile → guard.mark_reconcile_ok()
    """

    def __init__(
        self,
        guard: RuntimeGuard,
        reconciler: Reconciler,
        ledger: PortfolioLedger,
        reconciliations_dir: str | Path | None = None,
    ):
        self._guard = guard
        self._reconciler = reconciler
        self._ledger = ledger
        self._reconciliations_dir = Path(reconciliations_dir) if reconciliations_dir else None

    def check_and_gate(
        self,
        local: PortfolioSnapshot,
        broker: PortfolioSnapshot,
    ) -> ReconcileResult:
        """Run reconcile, update guard state, write audit trail.

        - Mismatch: activates stop, writes ledger + diff report
        - OK + was stopped: does NOT auto-clear (requires manual clear)
        - OK + was not stopped: no action
        """
        result = self._reconciler.reconcile(local, broker)

        if result.status == "mismatch":
            self._guard.activate_stop(
                reason=(
                    f"{len(result.differences)} difference(s) detected"
                    f" in reconcile {result.reconcile_id}"
                )
            )
            # Write ledger event
            self._ledger.append(
                "reconcile_mismatch",
                {
                    "reconcile_id": result.reconcile_id,
                    "differences_count": len(result.differences),
                    "differences": [
                        {"field": d.field, "local": d.local_value, "broker": d.broker_value}
                        for d in result.differences
                    ],
                },
                correlation_id=result.reconcile_id,
            )
            # Write diff report
            if self._reconciliations_dir is not None:
                self._write_diff_report(result)

        elif result.status == "ok":
            self._ledger.append(
                "reconcile_ok",
                {"reconcile_id": result.reconcile_id},
                correlation_id=result.reconcile_id,
            )
            # Do NOT auto-clear mismatch — requires manual intervention (D9)
            # Only mark OK if not in MISMATCH state
            self._guard.mark_reconcile_ok()

        return result

    def manual_clear(self) -> None:
        """Operator-triggered deactivation of stop-the-world.

        Sets guard to UNKNOWN, requiring a successful reconcile to reach OK.
        """
        self._guard.deactivate_stop()
        self._ledger.append("reconcile_manual_clear", {"cleared_by": "operator"})

    def _write_diff_report(self, result: ReconcileResult) -> None:
        """Write a full diff report to the reconciliations directory."""
        if self._reconciliations_dir is None:
            return
        self._reconciliations_dir.mkdir(parents=True, exist_ok=True)
        report_path = self._reconciliations_dir / f"{result.reconcile_id}.json"
        report_path.write_text(result.model_dump_json(indent=2) + "\n")
