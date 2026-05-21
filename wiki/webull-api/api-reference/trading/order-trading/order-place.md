---
title: "Order Place"
method: POST
endpoint: /openapi/trade/order/place
rate_limit: "15 req/s (US), 1 req/s (HK/A-share)"
source: https://developer.webull.hk/apis/docs/reference/common-order-place
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Order Place

- Function description: Place equity, options orders (preferred). The A-Share trading function is disabled by default.
- Frequency limit: US stock order interface: 15 requests/second, HK/A-share order interface: 1 request/second

## OpenAPI definition

```json
{
  "path": "/openapi/trade/order/place",
  "method": "post",
  "tags": ["Trading"],
  "operationId": "Common Order Place",
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
    "description": "Order Place",
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
            "client_combo_order_id": {
              "type": "string",
              "description": "Unique client-defined identifier for the combined order. If combo_type != NORMAL, server will auto-generate if not provided.",
              "example": "0KGOHL4PR2SLC0DKIND4TI0001"
            },
            "new_orders": {
              "type": "array",
              "description": "Order Details",
              "items": {
                "required": ["client_order_id", "combo_type", "entrust_type", "instrument_type", "market", "order_type", "side", "symbol", "time_in_force"],
                "type": "object",
                "properties": {
                  "combo_type": {
                    "type": "string",
                    "description": "NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, OTO, OCO, OTOCO",
                    "example": "NORMAL"
                  },
                  "client_order_id": {
                    "type": "string",
                    "description": "Unique client-defined identifier (max 32 chars). Allowed: A-Z, a-z, 0-9, -, _",
                    "example": "0KGOHL4PR2SLC0DKIND4TI0002"
                  },
                  "instrument_type": {
                    "type": "string",
                    "description": "EQUITY, OPTION, FUTURES",
                    "example": "EQUITY",
                    "enum": ["EQUITY", "OPTION", "FUTURES"]
                  },
                  "market": {
                    "type": "string",
                    "description": "US, HK, CN",
                    "example": "US",
                    "enum": ["US", "HK", "CN"]
                  },
                  "symbol": {
                    "type": "string",
                    "description": "Trading symbol",
                    "example": "BULL"
                  },
                  "order_type": {
                    "type": "string",
                    "description": "Order type. Varies by market.",
                    "example": "MARKET",
                    "enum": ["LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "ENHANCED_LIMIT", "AT_AUCTION", "AT_AUCTION_LIMIT", "MARKET_ON_OPEN", "TRAILING_STOP_LOSS", "TRAILING_STOP_LOSS_LIMIT", "TOUCH_MKT", "TOUCH_LMT"]
                  },
                  "entrust_type": {
                    "type": "string",
                    "description": "QTY or AMOUNT",
                    "example": "QTY",
                    "enum": ["QTY", "AMOUNT"]
                  },
                  "support_trading_session": {
                    "type": "string",
                    "description": "NIGHT, ALL, CORE, ALL_DAY (US only)",
                    "example": "CORE",
                    "enum": ["Y", "N", "NIGHT", "ALL", "CORE", "ALL_DAY"]
                  },
                  "time_in_force": {
                    "type": "string",
                    "description": "DAY, GTD, GTC",
                    "example": "DAY",
                    "enum": ["DAY", "GTD", "GTC"]
                  },
                  "side": {
                    "type": "string",
                    "description": "BUY, SELL, SHORT",
                    "example": "BUY",
                    "enum": ["BUY", "SELL", "SHORT"]
                  },
                  "quantity": {
                    "type": "string",
                    "description": "Transaction quantity",
                    "example": "1"
                  },
                  "total_cash_amount": {
                    "type": "string",
                    "description": "Total order amount (US fractional share, when entrust_type=AMOUNT)",
                    "example": "100.4"
                  },
                  "limit_price": {
                    "type": "string",
                    "description": "Limit price (required for LIMIT, STOP_LOSS_LIMIT, TOUCH_LMT)",
                    "example": "11.0"
                  },
                  "stop_price": {
                    "type": "string",
                    "description": "Stop price (required for STOP_LOSS, STOP_LOSS_LIMIT, TOUCH_MKT, TOUCH_LMT)",
                    "example": "11.0"
                  },
                  "trailing_type": {
                    "type": "string",
                    "description": "AMOUNT or PERCENTAGE",
                    "example": "AMOUNT",
                    "enum": ["AMOUNT", "PERCENTAGE"]
                  },
                  "trailing_stop_step": {
                    "type": "string",
                    "description": "Trailing Stop Spread",
                    "example": "1"
                  },
                  "trailing_limit_price": {
                    "type": "string",
                    "description": "Trailing limit price (for TRAILING_STOP_LOSS_LIMIT)",
                    "example": "11.0"
                  },
                  "trigger_price_type": {
                    "type": "string",
                    "description": "PRICE, PRICE_BID, PRICE_ASK",
                    "example": "PRICE",
                    "enum": ["PRICE", "PRICE_BID", "PRICE_ASK"]
                  },
                  "sender_sub_id": {
                    "type": "string",
                    "description": "Identifier for the firm or sub-account in third-party transactions."
                  },
                  "no_party_ids": {
                    "type": "array",
                    "description": "List of party identifiers (HK stock only).",
                    "items": {
                      "required": ["party_id", "party_id_source", "party_role"],
                      "type": "object",
                      "properties": {
                        "party_id": { "type": "string", "description": "Broker client ID (CE Number.BCAN format)", "example": "ABC123.2568" },
                        "party_id_source": { "type": "string", "description": "Must be 'D'", "example": "D" },
                        "party_role": { "type": "string", "description": "Must be '3'", "example": "3" }
                      }
                    }
                  },
                  "expire_date": {
                    "type": "string",
                    "description": "GTD expire date (yyyy-MM-dd)",
                    "example": "2026-01-01"
                  },
                  "option_strategy": {
                    "type": "string",
                    "description": "SINGLE",
                    "example": "SINGLE",
                    "enum": ["SINGLE"]
                  },
                  "legs": {
                    "type": "array",
                    "description": "Option leg detail (for option orders).",
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
                "title": "OrderCommonPlaceItemParam"
              }
            }
          },
          "title": "OrderCommonPlaceParam"
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
            "type": "object",
            "properties": {
              "client_order_id": { "type": "string", "description": "Client-defined order identifier", "example": "0KGOHL4PR2SLC0DKIND4TI0002" },
              "order_id": { "type": "string", "description": "System-generated order identifier", "example": "80HG7CPSFDPCAL3TP66LKBAS69" }
            },
            "title": "OrderCommonWriteResult"
          }
        }
      }
    },
    "401": { "description": "Unauthorized" },
    "417": { "description": "Business logic error" },
    "500": { "description": "Internal Server Error" }
  }
}
```

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| account_id | string | Yes | Account identifier |
| client_combo_order_id | string | No | Combined order ID (for non-NORMAL combo types) |
| new_orders | array | Yes | Array of order detail objects |

### new_orders items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| combo_type | string | Yes | NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, OTO, OCO, OTOCO |
| client_order_id | string | Yes | Unique client-defined identifier (max 32 chars) |
| instrument_type | string | Yes | EQUITY, OPTION, FUTURES |
| market | string | Yes | US, HK, CN |
| symbol | string | Yes | Trading symbol |
| order_type | string | Yes | Order type (varies by market) |
| entrust_type | string | Yes | QTY or AMOUNT |
| side | string | Yes | BUY, SELL, SHORT |
| time_in_force | string | Yes | DAY, GTD, GTC |
| quantity | string | No | Transaction quantity |
| total_cash_amount | string | No | Total amount (for AMOUNT entrust_type) |
| limit_price | string | No | Limit price |
| stop_price | string | No | Stop price |
| trailing_type | string | No | AMOUNT or PERCENTAGE |
| trailing_stop_step | string | No | Trailing stop spread |
| trailing_limit_price | string | No | Trailing limit price |
| trigger_price_type | string | No | PRICE, PRICE_BID, PRICE_ASK |
| support_trading_session | string | No | NIGHT, ALL, CORE, ALL_DAY |
| expire_date | string | No | GTD expire date (yyyy-MM-dd) |
| option_strategy | string | No | SINGLE |
| legs | array | No | Option leg details |
| sender_sub_id | string | No | Sub-account identifier |
| no_party_ids | array | No | Party identifiers (HK only) |

## Response

### 200 OK

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| client_order_id | string | Client-defined order identifier | 0KGOHL4PR2SLC0DKIND4TI0002 |
| order_id | string | System-generated order identifier | 80HG7CPSFDPCAL3TP66LKBAS69 |

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized: Authentication required |
| 417 | Business logic error |
| 500 | Internal Server Error |
