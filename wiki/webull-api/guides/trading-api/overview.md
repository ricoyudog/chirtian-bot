---
title: Trading API Overview
source: https://developer.webull.hk/apis/docs/trade-api/overview
updated: 2026-05-17
tags: [webull, guide, trading]
---

# Trading API Overview

The Trading API lets you manage accounts, place and manage orders, and receive real-time order status updates -- all programmatically. It supports US stocks, ETFs, and options, Hong Kong stocks and ETFs, and China Mainland A-shares via Stock Connect.

> **Tip:** The Webull SDK simplifies integration by handling authentication and protocol details. See SDKs and Tools for installation.

## Supported Markets

| Market | Region | Supported Instruments |
| --- | --- | --- |
| US Market | United States | Stocks, ETFs, Options |
| HK Market | Hong Kong | Stocks, ETFs |
| A-Share (Stock Connect) | China Mainland | Stock Connect eligible stocks |

> **Caution:** A-Share trading is disabled by default. Contact Webull to enable Stock Connect permissions.

## Feature Matrix

(Supported = checkmark, Not supported = dash)

| Feature | US Stocks | US Options | HK Stocks | A-Share |
| --- | --- | --- | --- | --- |
| **Order Types** | | | | |
| Limit Order (`LIMIT`) | yes | yes | -- | yes |
| Market Order (`MARKET`) | yes | -- | yes | -- |
| Enhanced Limit Order (`ENHANCED_LIMIT`) | -- | -- | yes | -- |
| Stop Loss (`STOP_LOSS`) | yes | yes | yes | -- |
| Stop Loss Limit (`STOP_LOSS_LIMIT`) | yes | yes | yes | -- |
| Trailing Stop Loss (`TRAILING_STOP_LOSS`) | -- | -- | yes | -- |
| Trailing Stop Loss Limit (`TRAILING_STOP_LOSS_LIMIT`) | -- | -- | yes | -- |
| Touch Market (`TOUCH_MKT`) | -- | -- | yes | -- |
| Touch Limit (`TOUCH_LMT`) | -- | -- | yes | -- |
| At-Auction (`AT_AUCTION`) | -- | -- | yes | -- |
| At-Auction Limit (`AT_AUCTION_LIMIT`) | -- | -- | yes | -- |
| Market on Open (`MARKET_ON_OPEN`) | yes | -- | -- | -- |
| Market on Close (`MARKET_ON_CLOSE`) | yes | -- | -- | -- |
| **Time in Force** | | | | |
| Day (`DAY`) | yes | yes | yes | yes |
| Good Till Cancelled (`GTC`) | yes | yes | yes | -- |
| Good Till Date (`GTD`) | yes | -- | -- | -- |
| **Trading Sessions** | | | | |
| Regular Hours (`CORE`) | yes | yes | yes | yes |
| Extended Hours (`ALL`) | yes | -- | -- | -- |
| Night Session (`NIGHT`) | yes | -- | -- | -- |
| Overnight (`ALL_DAY`) | yes | -- | -- | -- |
| **Other Features** | | | | |
| Fractional Shares (by amount) | yes | -- | -- | -- |
| Short Selling | yes | -- | -- | -- |
| BCAN Party ID Required | -- | -- | yes | -- |

HK stock orders require BCAN party identifiers (`no_party_ids`) for regulatory compliance.

## API Reference

### Account

| Endpoint | Rate Limit | Description |
| --- | --- | --- |
| Account List | 60/60s | Retrieve all accounts under your credentials |
| Account Balance | 60/60s | Query balance, buying power, and cash details |
| Account Positions | 60/60s | Retrieve current holdings and positions |

### Orders

| Endpoint | Rate Limit | Description |
| --- | --- | --- |
| Preview Order | 40/10s | Estimate costs before placing an order |
| Place Order | 15 req/s (US), 1 req/s (HK/A-share) | Submit orders |
| Replace Order | 15 req/s (US), 1 req/s (HK/A-share) | Modify an existing open order |
| Cancel Order | 15 req/s (US), 1 req/s (HK/A-share) | Cancel a pending or open order |
| Order History | 40/2s | Query historical order records |
| Open Orders | 40/2s | Retrieve current open orders |
| Order Detail | 40/2s | Get detailed info for a specific order |

### Real-Time Events

| Endpoint | Protocol | Description |
| --- | --- | --- |
| Trade Event Subscription | gRPC | Subscribe to live order status changes (filled, cancelled, failed, etc.) |

## What's Next

- Trading API Getting Started -- Make your first trade
- Accounts -- Query balances and positions
- Stock Trading -- Stock and ETF order management
- Options -- Options trading
