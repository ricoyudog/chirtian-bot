---
title: Webull HK OpenAPI Documentation
source: https://developer.webull.hk/apis/home/
llms_txt: https://developer.webull.hk/apis/llms.txt
updated: 2026-05-17
tags: [webull, api, trading, market-data, reference]
---

# Webull HK OpenAPI Documentation

> Webull HK OpenAPI provides programmatic access to trading, market data, and brokerage services for Hong Kong, US, and China Mainland markets. Supports HTTP REST, MQTT streaming, and gRPC event subscriptions.

## API Environments

### Production
| Service | Host |
|---------|------|
| HTTP API | `api.webull.hk` |
| Trading Events (gRPC) | `events-api.webull.hk` |
| Market Data Streaming (MQTT) | `data-api.webull.hk` |
| Broker API | `broker-api.webull.hk` |
| Display Solution API | `co-branding-openapi.webull.hk` |

### Sandbox
| Service | Host |
|---------|------|
| HTTP API | `api.sandbox.webull.hk` |
| Trading Events (gRPC) | `events-api.sandbox.webull.hk` |
| Market Data Streaming (MQTT) | `data-api.sandbox.webull.hk` |
| Broker API | `broker-api.sandbox.webull.hk` |
| Display Solution API | `hk-co-branding-openapi.uat.webullbroker.com` |

## Official SDKs

### Python
```bash
pip3 install --upgrade webull-openapi-python-sdk
```

### Java (Maven)
```xml
<dependency>
    <groupId>com.webull.openapi</groupId>
    <artifactId>webull-openapi-java-sdk</artifactId>
    <version>1.0.3</version>
</dependency>
```

## Documentation Structure

### Guides
- [[webull-api/guides/getting-started/welcome|Welcome to Webull API]]
- [[webull-api/guides/getting-started/about|About Webull]]
- [[webull-api/guides/getting-started/about-open-api|About Webull OpenAPI]]
- [[webull-api/guides/getting-started/getting-started|Getting Started]]
- [[webull-api/guides/getting-started/sdk|SDKs and Tools]]
- [[webull-api/guides/getting-started/resources|Additional Resources]]
- [[webull-api/guides/authentication/overview|Authentication Overview]]
- [[webull-api/guides/authentication/trading-api-application|Trading API Application]]
- [[webull-api/guides/authentication/broker-api-application|Broker API Application]]
- [[webull-api/guides/authentication/signature|Signature (HMAC-SHA1)]]
- [[webull-api/guides/authentication/token|Token Lifecycle]]
- [[webull-api/guides/market-data-api/overview|Market Data API Overview]]
- [[webull-api/guides/market-data-api/getting-started|Market Data API Getting Started]]
- [[webull-api/guides/market-data-api/data-api|Data API]]
- [[webull-api/guides/market-data-api/data-streaming-api|Data Streaming API]]
- [[webull-api/guides/market-data-api/subscribe-quotes|Subscribe Advanced Quotes]]
- [[webull-api/guides/market-data-api/hosted-display-solution|Hosted Display Solution]]
- [[webull-api/guides/market-data-api/faq|Market Data API FAQ]]
- [[webull-api/guides/trading-api/overview|Trading API Overview]]
- [[webull-api/guides/trading-api/getting-started|Trading API Getting Started]]
- [[webull-api/guides/trading-api/account|Accounts]]
- [[webull-api/guides/trading-api/stock|Stock Trading]]
- [[webull-api/guides/trading-api/options|Options Trading]]
- [[webull-api/guides/trading-api/faq|Trading API FAQ]]
- [[webull-api/guides/broker-api/omnibus-va|Omnibus with Virtual Account]]
- [[webull-api/guides/connect-api/getting-started|Connect API Getting Started]]

### API Reference

#### Authentication (Server-to-Server)
| API | Method | Endpoint | Rate Limit |
|-----|--------|----------|------------|
| [[webull-api/api-reference/auth/create-token\|Create Token]] | POST | `/openapi/auth/token/create` | 10 req/30s |
| [[webull-api/api-reference/auth/check-token\|Check Token]] | POST | `/openapi/auth/token/check` | 10 req/30s |

#### Market Data - Non-Display
| API | Method | Endpoint | Rate Limit |
|-----|--------|----------|------------|
| [[webull-api/api-reference/market-data/non-display/tick\|Tick]] | GET | `/openapi/market-data/stock/tick` | 60 req/60s |
| [[webull-api/api-reference/market-data/non-display/snapshot\|Snapshot]] | GET | `/openapi/market-data/stock/snapshot` | 60 req/60s |
| [[webull-api/api-reference/market-data/non-display/quotes\|Quotes]] | GET | `/openapi/market-data/stock/quotes` | 60 req/60s |
| [[webull-api/api-reference/market-data/non-display/footprint\|Footprint]] | POST | `/openapi/market-data/stock/footprint` | 600 req/min |
| [[webull-api/api-reference/market-data/non-display/historical-bars\|Historical Bars (Batch)]] | POST | `/openapi/market-data/stock/batch-bars` | 60 req/60s |
| [[webull-api/api-reference/market-data/non-display/bars\|Historical Bars (Single)]] | GET | `/openapi/market-data/stock/bars` | 60 req/60s |

#### Market Data - Streaming
| API | Method | Endpoint | Rate Limit |
|-----|--------|----------|------------|
| [[webull-api/api-reference/market-data/streaming/subscribe\|Subscribe]] | POST | `/openapi/market-data/streaming/subscribe` | 60 req/60s |
| [[webull-api/api-reference/market-data/streaming/unsubscribe\|Unsubscribe]] | POST | `/openapi/market-data/streaming/unsubscribe` | 60 req/60s |

#### Trading API - Instrument
| API | Method | Endpoint | Rate Limit |
|-----|--------|----------|------------|
| [[webull-api/api-reference/trading/instrument/instrument-list\|Get Instruments]] | GET | `/openapi/instrument/stock/list` | 60 req/60s |

#### Trading API - Account & Assets
| API | Method | Endpoint | Rate Limit |
|-----|--------|----------|------------|
| [[webull-api/api-reference/trading/account/account-list\|Account List]] | GET | `/openapi/account/list` | - |
| [[webull-api/api-reference/trading/assets/account-balance\|Account Balance]] | GET | `/openapi/assets/balance` | - |
| [[webull-api/api-reference/trading/assets/account-positions\|Account Positions]] | GET | `/openapi/assets/positions` | - |

#### Trading API - Orders
| API | Method | Endpoint | Rate Limit |
|-----|--------|----------|------------|
| [[webull-api/api-reference/trading/order-trading/order-preview\|Order Preview]] | POST | `/openapi/trade/order/preview` | 40 req/10s |
| [[webull-api/api-reference/trading/order-trading/order-place\|Order Place]] | POST | `/openapi/trade/order/place` | 15 req/s (US), 1 req/s (HK) |
| [[webull-api/api-reference/trading/order-trading/order-replace\|Order Replace]] | POST | `/openapi/trade/order/replace` | 15 req/s (US), 1 req/s (HK) |
| [[webull-api/api-reference/trading/order-trading/order-cancel\|Order Cancel]] | POST | `/openapi/trade/order/cancel` | 15 req/s (US), 1 req/s (HK) |
| [[webull-api/api-reference/trading/order-query/open-order\|Open Order]] | GET | `/openapi/trade/order/open` | 40 req/2s |
| [[webull-api/api-reference/trading/order-query/order-history\|Order History]] | GET | `/openapi/trade/order/history` | 40 req/2s |
| [[webull-api/api-reference/trading/order-query/order-detail\|Order Detail]] | GET | `/openapi/trade/order/detail` | 40 req/2s |
| [[webull-api/api-reference/trading/trade-events/subscribe-trade-events\|Trade Events]] | gRPC | - | - |

#### Broker API - Full Reference
See [[webull-api/api-reference/broker/_broker-index|Broker API Index]] for complete list.
