#!/usr/bin/env python3
"""Refresh positions.db from Webull UAT — used after pipeline runs.

Reads WEBULL_UAT_ACCOUNT_ID from env. Writes one fresh snapshot row.
"""
import os
import sqlite3
import time
from pathlib import Path

from src.executor.webull_adapter import WebullCLIAdapter

ACCOUNT = os.environ["WEBULL_UAT_ACCOUNT_ID"]
DB = Path("runtime/positions.db")
DB.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    broker = WebullCLIAdapter()
    positions = broker.get_positions(ACCOUNT)
    balance = broker.get_balance(ACCOUNT)

    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS position_snapshots (
            snapshot_id TEXT,
            run_id TEXT,
            tick_at TEXT,
            symbol TEXT,
            position_qty REAL,
            market_value REAL,
            unrealized_pnl REAL,
            pnl_pct REAL
        )
    """)
    # truncate so dashboard shows only the latest tick
    conn.execute("DELETE FROM position_snapshots")

    tick = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    rows = []
    for p in positions:
        sym = p.get("symbol") or p.get("ticker")
        qty = float(p.get("position") or p.get("quantity") or 0)
        mv = float(p.get("market_value") or 0)
        pnl = float(p.get("unrealized_pnl") or 0)
        cost = float(p.get("cost") or 0)
        pnl_pct = (pnl / cost * 100) if cost else 0.0
        rows.append(("live-sync", tick, sym, qty, mv, pnl, pnl_pct))

    if not rows:
        rows.append(("live-sync", tick, "CASH", 0, float(balance.get("equity", 0)), 0, 0))

    conn.executemany(
        "INSERT INTO position_snapshots (run_id, tick_at, symbol, position_qty, market_value, unrealized_pnl, pnl_pct) VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"Wrote {len(rows)} position rows to {DB} (tick={tick})")


if __name__ == "__main__":
    main()
