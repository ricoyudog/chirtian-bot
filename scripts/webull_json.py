#!/usr/bin/env python3
"""Persistent JSON shim over the Webull OpenAPI SDK for christian-bot.

WHY: ``webull-skill`` prints human-readable text on success (no JSON mode),
which is unusable for programmatic parsing. This shim calls the official SDK
directly (reusing the skill's ``.env`` + token + ``.venv-webull``) and prints
JSON, normalized into the dict shapes ``WebullAccountProvider`` expects.

PERSISTENT: the SDK client is initialized ONCE, then the shim reads
newline-delimited JSON requests from stdin and writes one JSON response per
line. This avoids re-checking the token on every call (the token endpoint is
rate-limited to 10 req/30s) — which matters because the orchestrator makes
several broker calls per order.

RUN WITH:  .venv-webull/bin/python scripts/webull_json.py
(The SDK requires Python <3.14; the orchestrator's own venv is 3.14.)

Each request is one JSON line::
    {"action": "...", "account_id": "...", "symbol": "...", "order": {...}}
Each response is one JSON line::
    {"ok": true,  "payload": <normalized>, "detail": ""}
    {"ok": false, "payload": null,        "detail": "<error>"}

Actions: account_list | balance | positions | open_orders | quote |
         preview | place | order_detail | cancel
"""

from __future__ import annotations

import json
import sys
import uuid


def _emit(ok: bool, payload=None, detail: str = "") -> None:
    sys.stdout.write(
        json.dumps({"ok": ok, "payload": payload, "detail": detail}, ensure_ascii=False)
    )
    sys.stdout.write("\n")
    sys.stdout.flush()


def _coid() -> str:
    return ("cb" + uuid.uuid4().hex)[:24]


def _to_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _handle(req: dict, sdk, extract) -> None:
    action = req.get("action", "")
    trade = sdk.trade
    account_id = req.get("account_id", "")

    try:
        # ---- account -------------------------------------------------
        if action == "account_list":
            data = extract(trade.account_v2.get_account_list())
            if isinstance(data, dict):
                data = data.get("account_list") or data.get("accounts") or [data]
            items = data if isinstance(data, list) else []
            return _emit(True, [
                {
                    "id": a.get("account_id") or a.get("id"),
                    "account_id": a.get("account_id") or a.get("id"),
                    "account_number": a.get("account_number") or a.get("account_no"),
                    "type": a.get("account_type"),
                }
                for a in items if isinstance(a, dict)
            ])

        if action == "balance":
            data = extract(trade.account_v2.get_account_balance(account_id)) or {}
            equity = _to_float(
                data.get("total_net_liquidation_value")
                or data.get("total_account_value")
                or data.get("total_cash_balance")
            )
            segs = data.get("account_currency_assets") or []
            usd = next((s for s in segs if str(s.get("currency")).upper() == "USD"), None)
            usd = usd or (segs[0] if segs else {})
            return _emit(True, {
                "equity": equity,
                "buying_power": _to_float(usd.get("buying_power")),
                "currency": usd.get("currency") or "USD",
            })

        if action == "positions":
            data = extract(trade.account_v2.get_account_position(account_id))
            raw = data if isinstance(data, list) else ((data or {}).get("positions") or [])
            norm = []
            for p in raw:
                if not isinstance(p, dict):
                    continue
                qty = _to_float(p.get("quantity") or p.get("qty"))
                last = _to_float(p.get("last_price"))
                mv = p.get("market_value")
                norm.append({
                    "symbol": p.get("symbol"),
                    "quantity": int(qty),
                    "avg_cost": _to_float(
                        p.get("cost_price") or p.get("avg_cost") or p.get("cost_basis")
                    ),
                    "market_value": _to_float(mv, last * qty),
                })
            return _emit(True, norm)

        if action == "open_orders":
            data = extract(trade.order_v3.get_order_open(account_id=account_id))
            raw = data if isinstance(data, list) else (
                (data or {}).get("orders") or (data or {}).get("items") or []
            )
            norm = []
            for group in raw:
                if not isinstance(group, dict):
                    continue
                # Webull nests the real order fields under a per-order "orders"
                # leg list (combo_type NORMAL → one leg). Fall back to the group
                # itself if it is already a flat order object.
                legs = group.get("orders") if isinstance(group.get("orders"), list) else None
                candidates = legs if legs else [group]
                for o in candidates:
                    if not isinstance(o, dict):
                        continue
                    lp = _to_float(o.get("limit_price"))
                    qty = _to_float(
                        o.get("total_quantity") or o.get("quantity") or o.get("qty")
                    )
                    norm.append({
                        "order_id": o.get("order_id") or o.get("id"),
                        "symbol": o.get("symbol"),
                        "side": o.get("side"),
                        "quantity": int(qty),
                        "order_type": o.get("order_type"),
                        "limit_price": lp or None,
                        "status": o.get("status"),
                    })
            return _emit(True, norm)

        # ---- market data ---------------------------------------------
        if action == "quote":
            symbol = req.get("symbol", "")
            data = extract(sdk.data.market_data.get_snapshot(
                symbols=[symbol], category=req.get("category", "US_STOCK"),
            ))
            snaps = data if isinstance(data, list) else ([data] if data else [])
            snap = snaps[0] if snaps else {}
            ask = _to_float(snap.get("ask"))
            bid = _to_float(snap.get("bid"))
            return _emit(True, {
                "symbol": snap.get("symbol") or symbol,
                "price": _to_float(snap.get("price") or snap.get("last_price")),
                "ask": ask or None,
                "bid": bid or None,
            })

        # ---- orders --------------------------------------------------
        if action in ("preview", "place"):
            order = dict(req.get("order") or {})
            order.setdefault("client_order_id", req.get("client_order_id") or _coid())
            for k in ("quantity", "limit_price", "stop_price", "total_cash_amount"):
                if order.get(k) is not None:
                    order[k] = str(order[k])
            if action == "preview":
                data = extract(trade.order_v3.preview_order(
                    account_id=account_id, preview_orders=[order],
                ))
            else:
                data = extract(trade.order_v3.place_order(
                    account_id=account_id, new_orders=[order],
                ))
            return _emit(True, data if isinstance(data, dict) else {"raw": data})

        if action == "order_detail":
            # SDK get_order_detail(account_id, client_order_id) — keyed on
            # client_order_id, not the broker order_id. Accept either from the
            # caller (adapter sends "order_id") and pass it as client_order_id.
            coid = req.get("client_order_id") or req.get("order_id", "")
            data = extract(trade.order_v3.get_order_detail(
                account_id=account_id, client_order_id=coid,
            ))
            return _emit(True, data if isinstance(data, dict) else {"raw": data})

        if action == "cancel":
            coid = req.get("client_order_id") or req.get("order_id")
            data = extract(trade.order_v3.cancel_order(
                account_id=account_id, client_order_id=coid,
            ))
            return _emit(True, data if isinstance(data, dict) else {"cancelled": coid})

        return _emit(False, detail=f"unknown action: {action}")

    except Exception as e:
        return _emit(False, detail=f"{action}: {type(e).__name__}: {e}")


def main() -> int:
    # Init SDK ONCE; reuse across all requests in this process.
    try:
        from webull_skill.config import load_config
        from webull_skill.formatters import extract_response_data
        from webull_skill.sdk_client import SDKClient

        cfg = load_config()
        sdk = SDKClient(cfg)
        sdk.initialize(interactive=False)  # reuse token; fail fast if 2FA expired
        extract = extract_response_data
    except Exception as e:
        # SDK won't init — report failure for every incoming request until EOF.
        for line in sys.stdin:
            if line.strip():
                _emit(False, detail=f"sdk init failed: {type(e).__name__}: {e}")
        return 1

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            _emit(False, detail=f"invalid JSON request: {e}")
            continue
        _handle(req, sdk, extract)
    return 0


if __name__ == "__main__":
    sys.exit(main())
