---
title: Historical Bars Single
method: GET
endpoint: /openapi/market-data/stock/bars
rate_limit: 1 call/sec per App Key
source: https://developer.webull.hk/apis/docs/reference/market-display-solution-data-api/bars-using-get
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - display-solution
---

# Historical Bars Single

```
GET

## /openapi/market-data/stock/bars
```

Query the recent N bars of data based on stock symbol, time granularity, and type. Supports historical bars of various granularities like M1, M5, etc. Currently, daily bars (D) and above only provide forward-adjusted bars; minute bars provide unadjusted bars.

- Frequency limit: 1 call/sec per App Key

## Request

## Responses

- 200 OK
