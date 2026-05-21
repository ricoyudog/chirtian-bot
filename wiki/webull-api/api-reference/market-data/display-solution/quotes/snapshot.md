---
title: Snapshot
method: POST
endpoint: /openapi/market-data/stock/snapshot
rate_limit: 1 call/sec per App Key
source: https://developer.webull.hk/apis/docs/reference/market-display-solution-data-api/snapshot-using-get
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - display-solution
---

# Snapshot

```
POST

## /openapi/market-data/stock/snapshot
```

Real-time snapshot for Display Solution. Returns key market indicators such as latest price, price change, volume, turnover rate, etc. Supports querying various security types including US stocks, etc., with optional inclusion of pre-market, after-hours, and overnight trading data.

## Request

## Responses

- 200 OK
