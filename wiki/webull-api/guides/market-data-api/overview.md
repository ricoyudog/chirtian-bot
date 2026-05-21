---
title: Market Data API Overview
source: https://developer.webull.hk/apis/docs/market-data-api/overview
updated: 2026-05-17
tags: [webull, guide, market-data]
---

# Market Data API Overview

The Market Data API provides access to real-time and historical market data for Hong Kong stocks, US stocks, and China A-shares. It supports two access patterns:

- **Data API** — HTTP-based requests for historical and snapshot data. Ideal for backtesting, analysis, and on-demand queries. See Data API.
- **Data Streaming API** — Real-time data push via MQTT protocol over WebSocket/TCP. Ideal for live trading strategies and real-time monitoring. See Data Streaming API.

> **Tip:** The Webull SDK simplifies integration by handling authentication and protocol details. See SDKs and Tools for installation.

## Supported Markets and Products

| Market | Product |
| --- | --- |
| Hong Kong | Stocks, ETFs |
| US | Stocks, ETFs |
| US | Overnight Session |
| China Mainland | A-Shares (Stock Connect) |

## Available Endpoints

### Market Data

| Endpoint | Protocol | Description |
| --- | --- | --- |
| Snapshot | HTTP | Real-time market snapshot with latest price, price change, volume, turnover rate, etc. Supports pre-market, after-hours, and overnight data |
| Quotes Depth | HTTP | Latest bid/ask data at specified depth, including price, quantity, and order details |
| Tick | HTTP | Tick-by-tick trade records including time, price, volume, and direction. Sorted latest first |
| Historical Bars (Single Symbol) | HTTP | OHLCV candlestick data at various granularities (M1, M5, D, etc.). Daily and above: forward-adjusted; minute bars: unadjusted |
| Historical Bars (Batch) | HTTP | Batch query for multiple symbols. Same granularity and adjustment rules as single symbol |
| Footprint | HTTP | Query the most recent N footprint records based on stock symbol, and category, time granularity. |

### Instruments

| Endpoint | Protocol | Description |
| --- | --- | --- |
| Get Instruments | HTTP | Get security information for one or more instruments |

### Real-Time Streaming

| Endpoint | Protocol | Description |
| --- | --- | --- |
| Subscribe | HTTP | Subscribe to real-time market data push via MQTT |
| Unsubscribe | HTTP | Unsubscribe from real-time market data push |

## Market Data Permissions

| Market | Category | How to Access |
| --- | --- | --- |
| US Market | Stocks, ETFs, Overnight Session | Purchase Level 1 and/or Level 2 US stock market data on the Webull website |
| Hong Kong Market | Stocks, ETFs | LV1 data is free. For LV2 data, purchase HKEX Level 2 (Global Edition) on the Webull website |
| China Mainland | A-Shares (Stock Connect) | LV1 data is free (15-minute delay outside Mainland China; not available in Mainland China) |

> **Caution:** Market data subscriptions purchased through the Webull mobile app or desktop platform (QT) are independent of OpenAPI. You need a separate subscription specifically enabled for OpenAPI usage. Only one device may access LV1/LV2 data at any one time. For details on how to subscribe, see Subscribe Advanced Quotes.
