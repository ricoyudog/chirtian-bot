---
title: Historical Bars Batch
method: POST
endpoint: /openapi/market-data/stock/batch-bars
rate_limit: 1 call/sec per App Key
source: https://developer.webull.hk/apis/docs/reference/market-display-solution-data-api/query-batch-bars-using-post
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - display-solution
---

# Historical Bars Batch

```
POST

## /openapi/market-data/stock/batch-bars
```

Batch query interface. Query the recent N bars of data based on stock symbols, time granularity, and type. Supports historical bars of various granularities like M1, M5, etc. Currently, daily bars (D) and above only provide forward-adjusted bars; minute bars provide unadjusted bars.

- Frequency limit: 1 call/sec per App Key

## Request

## Responses

- 200 OK
