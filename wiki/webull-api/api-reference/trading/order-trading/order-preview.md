---
title: "Order Preview"
method: POST
endpoint: /openapi/trade/order/preview
rate_limit: "40 req/10s"
source: https://developer.webull.hk/apis/docs/reference/common-order-preview
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Order Preview

- Function description: Calculate the estimated amount and cost based on the incoming information, and support simple orders.
- Frequency limit: Rate limit 40 requests every 10 seconds

## OpenAPI definition

```json
{
  "path": "/openapi/trade/order/preview",
  "method": "post",
  "tags": ["Trading"],
  "operationId": "Common Order Preview",
  "parameters": [
    {
      "name": "x-app-key", "in": "header", "required": true,
      "description": "A unique identifier issued to a developer for accessing an application's API.",
      "schema": { "type": "string" }
    },
    {
      "name": "x-app-secret", "in": "header", "required": true,
      "description": "A unique key issued to developers to access the application's API.",
      "schema": { "type": "string" }
    },
    {
      "name": "x-timestamp", "in": "header", "required": true,
      "description": "Timestamp of the request, follows ISO8601 format: YYYY-MM-DDThh:mm:ssZ",
      "schema": { "type": "string" }
    },
    {
      "name": "x-signature-version", "in": "header", "required": true,
      "description": "Signature algorithm version, default is 1.0.",
      "schema": { "type": "string", "default": "1.0" }
    },
    {
      "name": "x-signature-algorithm", "in": "header", "required": true,
      "description": "Signature algorithm, default is HMAC-SHA1.",
      "schema": { "type": "string", "default": "HMAC-SHA1" }
    },
    {
      "name": "x-signature-nonce", "in": "header", "required": true,
      "description": "Signature unique random number.",
      "schema": { "type": "string" }
    },
    {
      "name": "x-access-token", "in": "header", "required": true,
      "description": "An access token for accessing protected resources.",
      "schema": { "type": "string" }
    },
    {
      "name": "x-version", "in": "header", "required": true,
      "description": "Interface version, Accepts only the value v2.",
      "schema": { "type": "string", "default": "v2" }
    },
    {
      "name": "x-signature", "in": "header", "required": true,
      "description": "A digital fingerprint that verifies authenticity and integrity.",
      "schema": { "type": "string" }
    }
  ],
  "requestBody": {
    "description": "Order Preview",
    "content": {
      "application/json": {
        "schema": {
          "required": ["account_id", "new_orders"],
          "type": "object",
          "properties": {
            "account_id": {
              "type": "string",
              "description": "Account identifier",
              "example": "93IUJ28O9VO2KBGHDHR4H9"
            },
            "new_orders": {
              "type": "array",
              "description": "Order Details",
              "items": {
                "required": ["client_order_id", "combo_type", "entrust_type", "instrument_type", "market", "order_type", "side", "support_trading_session", "symbol", "time_in_force"],
                "type": "object",
                "properties": {
                  "combo_type": {
                    "type": "string",
                    "description": "Specifies the type of order combination. NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, OTO, OCO, OTOCO.",
                    "example": "NORMAL"
                  },
                  "client_order_id": {
                    "type": "string",
                    "description": "Unique client-defined identifier for the order. Max 32 chars. Allowed: A-Z, a-z, 0-9, -, _",
                    "example": "0KGOHL4PR2SLC0DKIND4TI0002"
                  },
                  "instrument_type": {
                    "type": "string",
                    "description": "Type of financial instrument.",
                    "example": "EQUITY",
                    "enum": ["EQUITY", "OPTION", "FUTURES"]
                  },
                  "market": {
                    "type": "string",
                    "description": "Market code.",
                    "example": "US",
                    "enum": ["US", "HK", "CN"]
                  },
                  "symbol": {
                    "type": "string",
                    "description": "Trading symbol of the financial instrument.",
                    "example": "AAPL"
                  },
                  "order_type": {
                    "type": "string",
                    "description": "Specifies the type of order to be placed. Available types depend on market and instrument.",
                    "example": "MARKET",
                    "enum": ["LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "ENHANCED_LIMIT", "AT_AUCTION", "AT_AUCTION_LIMIT", "MARKET_ON_OPEN", "TRAILING_STOP_LOSS", "TRAILING_STOP_LOSS_LIMIT", "TOUCH_MKT", "TOUCH_LMT"]
                  },
                  "entrust_type": {
                    "type": "string",
                    "description": "QTY: Order by quantity. AMOUNT: Order by total cash amount (US stocks fractional).",
                    "example": "QTY",
                    "enum": ["QTY", "AMOUNT"]
                  },
                  "support_trading_session": {
                    "type": "string",
                    "description": "Trading session for US stock orders. NIGHT, ALL, CORE, ALL_DAY.",
                    "example": "CORE",
                    "enum": ["Y", "N", "NIGHT", "ALL", "CORE", "ALL_DAY"]
                  },
                  "time_in_force": {
                    "type": "string",
                    "description": "DAY, GTD, GTC.",
                    "example": "DAY",
                    "enum": ["DAY", "GTD", "GTC"]
                  },
                  "side": {
                    "type": "string",
                    "description": "Order side.",
                    "example": "BUY",
                    "enum": ["BUY", "SELL", "SHORT"]
                  },
                  "quantity": {
                    "type": "string",
                    "description": "Transaction quantity.",
                    "example": "1"
                  },
                  "limit_price": {
                    "type": "string",
                    "description": "Limit price. Required for LIMIT, STOP_LOSS_LIMIT.",
                    "example": "11.0"
                  },
                  "stop_price": {
                    "type": "string",
                    "description": "Stop price. Required for STOP_LOSS, STOP_LOSS_LIMIT.",
                    "example": "11.0"
                  },
                  "option_strategy": {
                    "type": "string",
                    "description": "Options strategy type. SINGLE: single-leg options order.",
                    "example": "SINGLE",
                    "enum": ["SINGLE"]
                  },
                  "legs": {
                    "type": "array",
                    "description": "Option leg detail. Only required for option orders.",
                    "items": {
                      "required": ["instrument_type", "market", "side", "symbol"],
                      "type": "object",
                      "properties": {
                        "instrument_type": { "type": "string", "example": "OPTION", "enum": ["EQUITY", "OPTION", "FUTURES"] },
                        "market": { "type": "string", "example": "US", "enum": ["US", "HK", "CN"] },
                        "symbol": { "type": "string", "example": "AAPL" },
                        "side": { "type": "string", "example": "BUY", "enum": ["BUY", "SELL", "SHORT"] },
                        "strike_price": { "type": "string", "example": "11.0" },
                        "option_expire_date": { "type": "string", "example": "2025-08-01" },
                        "option_type": { "type": "string", "example": "CALL", "enum": ["CALL", "PUT"] },
                        "quantity": { "type": "string", "example": "1" }
                      }
                    }
                  }
                },
                "title": "OrderCommonPreviewItemParam"
              }
            }
          },
          "title": "OrderCommonPreviewParam"
        },
        "examples": {
          "Stock": {
            "summary": "Stock Limit Order",
            "value": {
              "account_id": "",
              "new_orders": [{
                "client_order_id": "", "combo_type": "NORMAL", "symbol": "AAPL",
                "instrument_type": "EQUITY", "market": "US", "order_type": "LIMIT",
                "limit_price": "180.00", "quantity": "10", "side": "BUY",
                "time_in_force": "DAY", "support_trading_session": "CORE", "entrust_type": "QTY"
              }]
            }
          },
          "Options": {
            "summary": "Single Leg Order",
            "value": {
              "account_id": "",
              "new_orders": [{
                "client_order_id": "", "combo_type": "NORMAL", "order_type": "LIMIT",
                "limit_price": "11.25", "quantity": "1", "option_strategy": "SINGLE",
                "side": "BUY", "time_in_force": "DAY", "entrust_type": "QTY",
                "instrument_type": "OPTION", "market": "US", "symbol": "AAPL",
                "legs": [{
                  "side": "BUY", "quantity": "1", "symbol": "AAPL",
                  "strike_price": "220.00", "option_expire_date": "2025-11-19",
                  "instrument_type": "OPTION", "option_type": "CALL", "market": "US"
                }]
              }]
            }
          }
        }
      }
    },
    "required": true
  },
  "responses": {
    "200": {
      "description": "OK",
      "content": {
        "application/json": {
          "schema": {
            "required": ["estimated_cost", "estimated_transaction_fee"],
            "type": "object",
            "properties": {
              "estimated_cost": {
                "type": "string",
                "description": "Estimated capital required for the order.",
                "example": "100"
              },
              "estimated_transaction_fee": {
                "type": "string",
                "description": "Estimated transaction fee including exchange, clearing, and commission fees.",
                "example": "1"
              }
            },
            "title": "OrderCommonPreviewResult"
          }
        }
      }
    },
    "401": { "description": "Unauthorized: Authentication required" },
    "417": { "description": "Business logic error" },
    "500": { "description": "Internal Server Error" }
  }
}
```

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| account_id | string | Yes | Account identifier |
| new_orders | array | Yes | Array of order detail objects |

### new_orders items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| combo_type | string | Yes | Order combination type: NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, OTO, OCO, OTOCO |
| client_order_id | string | Yes | Unique client-defined identifier (max 32 chars) |
| instrument_type | string | Yes | EQUITY, OPTION, FUTURES |
| market | string | Yes | US, HK, CN |
| symbol | string | Yes | Trading symbol |
| order_type | string | Yes | Order type (varies by market) |
| entrust_type | string | Yes | QTY or AMOUNT |
| support_trading_session | string | Yes | Trading session (NIGHT, ALL, CORE, ALL_DAY) |
| time_in_force | string | Yes | DAY, GTD, GTC |
| side | string | Yes | BUY, SELL, SHORT |
| quantity | string | No | Transaction quantity |
| limit_price | string | No | Limit price (required for LIMIT, STOP_LOSS_LIMIT) |
| stop_price | string | No | Stop price (required for STOP_LOSS, STOP_LOSS_LIMIT) |
| option_strategy | string | No | SINGLE |
| legs | array | No | Option leg details |

## Response

### 200 OK

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| estimated_cost | string | Estimated capital required for the order | 100 |
| estimated_transaction_fee | string | Estimated transaction fee | 1 |

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized: Authentication required |
| 417 | Business logic error |
| 500 | Internal Server Error |
