---
title: Tick
method: GET
endpoint: /openapi/market-data/stock/tick
rate_limit: 1 call/sec per App Key
source: https://developer.webull.hk/apis/docs/reference/market-display-solution-data-api/tick-using-get
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - display-solution
---

# Tick

```
GET

## /openapi/market-data/stock/tick
```

Get tick-by-tick trade data for a security. Returns detailed tick trade records within a specified time range for a given security, including trade time, price, volume, direction, and other details. Data is sorted in reverse chronological order (latest first).

- Frequency limit: 1 call/sec per App Key

## Request

## Responses

- 200 OK
