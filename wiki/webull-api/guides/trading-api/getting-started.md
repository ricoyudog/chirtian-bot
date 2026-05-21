---
title: Trading API Getting Started
source: https://developer.webull.hk/apis/docs/trade-api/getting-started
updated: 2026-05-17
tags: [webull, guide, trading, sdk]
---

# Trading API Getting Started

This guide walks you through making your first trade using the Webull SDK. By the end, you'll have queried your account list, checked balances, and placed an order.

## Prerequisites

- Webull SDK installed (SDKs and Tools)
- App Key and App Secret (Trading API Application)
- A valid access token with `NORMAL` status (Token)

## Step 1: Retrieve Your Account List

Before placing any orders, you need your Account ID.

```python
from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient

api_client = ApiClient("<your_app_key>", "<your_app_secret>", "hk")
api_client.add_endpoint("hk", "<api_endpoint>")

trade_client = TradeClient(api_client)
res = trade_client.get_account_list()
if res.status_code == 200:
    print("Accounts:", res.json())
```

Save the `account_id` from the response -- you'll need it for all subsequent calls.

**API Endpoints:**

- Trading API PROD: `api.webull.hk`
- Broker API PROD: `broker-api-event-push.webull.hk`
- Sandbox: `api.sandbox.webull.hk`

## Step 2: Query Account Balance

```python
account_id = "<your_account_id>"
res = trade_client.get_account_balance(account_id=account_id)
if res.status_code == 200:
    print("Balance:", res.json())
```

## Step 3: Place a Stock Order

Place a simple limit order to buy 100 shares:

```python
order_params = {
    "account_id": "<your_account_id>",
    "instrument_id": "<instrument_id>",
    "side": "BUY",
    "order_type": "LIMIT",
    "quantity": "100",
    "price": "150.00",
    "time_in_force": "DAY"
}

res = trade_client.place_order(**order_params)
if res.status_code == 200:
    print("Order placed:", res.json())
```

## Step 4: Subscribe to Order Status Updates

Monitor order status changes in real time via gRPC streaming:

```python
from webull.trade.events.types import ORDER_STATUS_CHANGED, EVENT_TYPE_ORDER
from webull.trade.trade_events_client import TradeEventsClient

def on_event(event_type, subscribe_type, payload, raw_message):
    if EVENT_TYPE_ORDER == event_type and ORDER_STATUS_CHANGED == subscribe_type:
        print("Order update:", payload)

events_client = TradeEventsClient("<your_app_key>", "<your_app_secret>", "hk")
events_client.on_events_message = on_event
events_client.do_subscribe(["<your_account_id>"])
```

> **Tip:**
> - Production gRPC: `events-api.webull.hk`
> - Sandbox gRPC: `events-api.sandbox.webull.hk`

## What's Next

- Accounts -- Query balances and positions
- Stock Trading -- Stock and ETF order management
- Options -- Options trading
- Trading API FAQ -- Common questions and troubleshooting
