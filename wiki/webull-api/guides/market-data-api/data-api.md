---
title: Data API
source: https://developer.webull.hk/apis/docs/market-data-api/data-api
updated: 2026-05-17
tags: [webull, guide, market-data, http]
---

# Data API

The Data API uses the HTTP protocol for on-demand market data queries. Use it for historical data retrieval, snapshot lookups, and backtesting. For the full list of available endpoints, see Market Data API Overview.

All Data API requests are standard HTTP GET or POST calls. Every request must include the authentication headers described in Authentication Overview.

## Example Request

```
GET /openapi/market-data/stock/snapshot?symbols=AAPL&category=US_STOCK&extend_hour_required=false&overnight_required=false
x-app-key: <your_app_key>
x-app-secret: <your_app_secret>
x-timestamp: 2025-03-19T10:00:00Z
x-signature-algorithm: HMAC-SHA1
x-signature-version: 1.0
x-signature-nonce: <unique_nonce>
x-version: v2
x-access-token: <your_access_token>
x-signature: <computed_signature>
```

## Example Response

```json
[
  {
    "symbol": "AAPL",
    "instrument_id": "913256135",
    "price": "185.50",
    "open": "184.00",
    "high": "186.20",
    "low": "183.80",
    "volume": "52340000",
    "change": "1.50",
    "change_ratio": "0.0082",
    "pre_close": "184.00",
    "last_trade_time": 1710849600000
  }
]
```

Timestamps in responses are Unix timestamps in milliseconds. Prices and numeric values are returned as strings to preserve precision.

If you exceed the rate limit, the server will return an error.
