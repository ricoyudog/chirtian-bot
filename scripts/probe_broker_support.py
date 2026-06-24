"""Read-only broker probe: confirm token valid + which symbols the paper account supports.

Run from project root: .venv/bin/python scripts/probe_broker_support.py
Does NOT place any order.
"""
from __future__ import annotations

import os
import sys

from src.executor.webull_adapter import WebullCLIAdapter
from src.portfolio.provider import WebullAccountProvider

ACCOUNT = os.environ.get("WEBULL_UAT_ACCOUNT_ID", "FQGU74FVLF506T2VKVRNK7M559")

adapter = WebullCLIAdapter()
provider = WebullAccountProvider(adapter)

print(f"=== SNAPSHOT (account {ACCOUNT[:6]}...) — confirms token valid ===")
try:
    snap = provider.get_snapshot(ACCOUNT)
    print(
        f"OK  equity=${snap.equity_usd:,.2f}  buying_power=${snap.buying_power_usd:,.2f}  "
        f"positions={len(snap.positions)}  open_orders={len(snap.open_orders)}"
    )
    for p in snap.positions:
        print(f"    - {p.symbol}  qty={p.quantity}  side={getattr(p, 'side', '?')}")
except Exception as e:  # noqa: BLE001
    print(f"FAIL {type(e).__name__}: {str(e)[:200]}")

print("\n=== QUOTE PROBE — which symbols does this paper account support? ===")
for sym in ["AAPL", "TSLA", "PLTR", "SMCI", "NVDA", "QQQ", "MSFT"]:
    try:
        q = provider.get_quote(sym)
        print(f"OK   {sym:5} price={q.price}  ask={q.ask}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {sym:5} {type(e).__name__}: {str(e)[:140]}")
