---
title: "Webull Broker API Reference Index"
updated: "2026-05-17"
tags: [webull, api-reference, broker, index]
---

# Webull Broker API Reference Index

> **Base URL (Production):** `broker-api.webull.hk`
> **Base URL (Sandbox):** `broker-api.sandbox.webull.hk`
> **Events (Production):** `events-api.webull.hk`
> **Events (Sandbox):** `events-api.sandbox.webull.hk`
> **Source:** [Webull OpenAPI Documentation](https://developer.webull.hk/apis/docs)

---

## Account (ND)

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 1 | Create Virtual Account | `POST` | `/openapi/broker/account/nd/create` | Create a Virtual Account for a new customer | [broker-account-create](account/broker-account-create.md) |
| 2 | Update Virtual Account | `POST` | `/openapi/broker/account/nd/update` | Update virtual account information | [broker-account-update](account/broker-account-update.md) |
| 3 | Get Virtual Account Detail | `GET` | `/openapi/broker/account/nd/detail` | Query virtual account details | [broker-account-detail](account/broker-account-detail.md) |
| 4 | List Virtual Accounts | `GET` | `/openapi/broker/account/nd/list` | List all virtual accounts | [broker-account-list](account/broker-account-list.md) |

## Instrument

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 5 | Get Stock Instrument | `GET` | `/openapi/broker/instrument/stock/list` | Get instrument detail information | [broker-instrument-list](instrument/broker-instrument-list.md) |
| 6 | Get Stock Locate Detail | `GET` | `/openapi/broker/instrument/locate/detail` | Get stock short trading info (ETB/HTB, short qty, rate) | [broker-stock-locate-detail](instrument/broker-stock-locate-detail.md) |
| 7 | Get Corporate Actions Detail | `GET` | `/openapi/broker/instrument/corporate-actions/detail` | Query corporate actions details | [broker-corporate-actions-detail](instrument/broker-corporate-actions-detail.md) |

## Activities

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 8 | Get Account Activities | `GET` | `/openapi/broker/activities/cash` | Return account transaction activity records | [broker-activity-by-type](activities/broker-activity-by-type.md) |

## Assets

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 9 | Account Balance | `POST` | `/openapi/broker/assets/balance` | Query virtual account balance | [broker-assets-balance](assets/broker-assets-balance.md) |
| 10 | Account Positions | `GET` | `/openapi/broker/assets/positions` | Query virtual account positions | [broker-assets-positions](assets/broker-assets-positions.md) |

## Order - Trading

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 11 | Preview Order | `POST` | `/openapi/broker/trade/order/preview` | Preview order cost and fees | [broker-order-preview](order-trading/broker-order-preview.md) |
| 12 | Place Order | `POST` | `/openapi/broker/trade/order/place` | Place order on behalf of virtual account | [broker-order-place](order-trading/broker-order-place.md) |
| 13 | Replace Order | `POST` | `/openapi/broker/trade/order/replace` | Modify an existing open order | [broker-order-replace](order-trading/broker-order-replace.md) |
| 14 | Cancel Order | `POST` | `/openapi/broker/trade/order/cancel` | Cancel a pending order | [broker-order-cancel](order-trading/broker-order-cancel.md) |

## Order - Query

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 15 | Order Detail | `GET` | `/openapi/broker/trade/order/detail` | Query order details | [broker-order-detail](order-query/broker-order-detail.md) |
| 16 | Order History | `GET` | `/openapi/broker/trade/order/history` | Query historical orders | [broker-order-history](order-query/broker-order-history.md) |
| 17 | Open Order | `GET` | `/openapi/broker/trade/order/open` | Query pending orders | [broker-order-open](order-query/broker-order-open.md) |

## Funding - FX

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 18 | Get FX Rate | `GET` | `/openapi/broker/funding/fx/rate` | Query foreign exchange rates | [broker-funding-query-rate](funding/broker-funding-query-rate.md) |
| 19 | Create FX Request | `POST` | `/openapi/broker/funding/fx/create` | Create a foreign exchange request | [broker-funding-create-fx](funding/broker-funding-create-fx.md) |
| 20 | Get FX Detail | `GET` | `/openapi/broker/funding/fx/detail` | Query FX request details | [broker-funding-query-fx](funding/broker-funding-query-fx.md) |
| 21 | Create Instant Exchange | `POST` | `/openapi/broker/funding/fx/instant/create` | Create an instant currency exchange request | [broker-funding-create-instant-fx](funding/broker-funding-create-instant-fx.md) |
| 22 | Get Instant Exchange Detail | `GET` | `/openapi/broker/funding/fx/instant/detail` | Query instant exchange details | [broker-funding-query-instant-fx](funding/broker-funding-query-instant-fx.md) |

## Funding - Instant

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 23 | Create Instant Funding | `POST` | `/openapi/broker/funding/instant/create` | Create an instant funding request | [broker-funding-instant-create](funding/broker-funding-instant-create.md) |
| 24 | Get Instant Funding Detail | `GET` | `/openapi/broker/funding/instant/detail` | Query instant funding details | [broker-funding-instant-query](funding/broker-funding-instant-query.md) |

## Journals

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 25 | Create Cash Journal | `POST` | `/openapi/broker/journal/cash/create` | Create a cash journal entry | [broker-journal-cash-create](journals/broker-journal-cash-create.md) |
| 26 | Get Cash Journal Detail | `GET` | `/openapi/broker/journal/cash/detail` | Query cash journal details | [broker-journal-cash-query](journals/broker-journal-cash-query.md) |
| 27 | Create Position Journal | `POST` | `/openapi/broker/journal/position/create` | Create a position journal entry | [broker-journal-position-create](journals/broker-journal-position-create.md) |
| 28 | Get Position Journal Detail | `GET` | `/openapi/broker/journal/position/detail` | Query position journal details | [broker-journal-position-query](journals/broker-journal-position-query.md) |

## Master Data

| # | Endpoint | Method | API Path | Description | Doc |
|---|----------|--------|----------|-------------|-----|
| 29 | Trade Calendar | `POST` | `/openapi/broker/master-data/trade-calendar` | Query trading calendar | [broker-trade-calendar](master-data/broker-trade-calendar.md) |

## Events (gRPC Streaming)

| # | Endpoint | Protocol | Event Name | Description | Doc |
|---|----------|----------|------------|-------------|-----|
| 30 | Account Events | `gRPC` | `broker-account-events` | Account status change events | [broker-account-events](events/broker-account-events.md) |
| 31 | Instrument Events | `gRPC` | `broker-instrument-events` | Instrument data change events | [broker-instrument-events](events/broker-instrument-events.md) |
| 32 | Corporate Actions Events | `gRPC` | `broker-corporate-actions-events` | Corporate actions events | [broker-ca-events](events/broker-ca-events.md) |
| 33 | Trade Events | `gRPC` | `broker-trade-events` | Trade execution events | [broker-trade-events](events/broker-trade-events.md) |
| 34 | Funding Events | `gRPC` | `broker-funding-events` | Funding status change events | [broker-funding-events](events/broker-funding-events.md) |
| 35 | Journal Events | `gRPC` | `broker-journal-events` | Journal entry events | [broker-journal-events](events/broker-journal-events.md) |
| 36 | Master Data Events | `gRPC` | `broker-master-data-events` | Master data change events | [broker-master-data-events](events/broker-master-data-events.md) |

---

## Authentication

All Broker API endpoints require HMAC-SHA1 signature authentication with the following headers:

| Header | Description |
|--------|-------------|
| `x-app-key` | Application API key |
| `x-app-secret` | Application API secret |
| `x-timestamp` | Request timestamp (ISO 8601) |
| `x-signature-version` | Signature version (`1.0`) |
| `x-signature-algorithm` | Signature algorithm (`HMAC-SHA1`) |
| `x-signature-nonce` | Unique nonce for the request |
| `x-version` | API version (`v2`) |
| `x-signature` | HMAC-SHA1 signature |

## Summary

| Category | Count | Methods |
|----------|-------|---------|
| Account | 4 | POST, GET |
| Instrument | 3 | GET |
| Activities | 1 | GET |
| Assets | 2 | POST, GET |
| Order Trading | 4 | POST |
| Order Query | 3 | GET |
| Funding - FX | 5 | GET, POST |
| Funding - Instant | 2 | POST, GET |
| Journals | 4 | POST, GET |
| Master Data | 1 | POST |
| Events | 7 | gRPC |
| **Total** | **36** | |

## Related Resources

- [Webull API Documentation](https://developer.webull.hk/apis/docs)
- [Broker API Overview - Omnibus with VA](https://developer.webull.hk/apis/docs/broker-api/omnibus-va)
- [Authentication Guide](https://developer.webull.hk/apis/docs/authentication/overview)
- [Signature Algorithm](https://developer.webull.hk/apis/docs/authentication/signature)
- [Token Management](https://developer.webull.hk/apis/docs/authentication/token)
- [Python SDK](https://pypi.org/project/webull-openapi-python-sdk/)
- [Java SDK (Maven)](https://developer.webull.hk/apis/docs/sdk)
