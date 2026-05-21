---
title: "Open Order"
method: GET
endpoint: /openapi/trade/order/open
rate_limit: "40 req/2s"
source: https://developer.webull.hk/apis/docs/reference/order-open
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Open Order

- Function description: Query pending orders by page, and modify or cancel orders based on client_order_id.
- Frequency limit: Rate limit 40 requests every 2 seconds

## OpenAPI definition

```json
{
  "path": "/openapi/trade/order/open",
  "method": "get",
  "tags": ["Order Query"],
  "operationId": "orderOpen",
  "parameters": [
    {
      "name": "account_id", "in": "query", "required": true,
      "description": "Account identifier.",
      "schema": { "type": "String" },
      "example": "20150320010101000"
    },
    {
      "name": "page_size", "in": "query", "required": false,
      "description": "Number of records to return per query. Defaults to 10 if not specified. The value must be less than or equal to 200.",
      "schema": { "type": "String" },
      "example": "10"
    },
    {
      "name": "last_client_order_id", "in": "query", "required": false,
      "description": "The last client order ID returned from the previous response. Used for cursor-based pagination. Not required for the first page query.",
      "schema": { "type": "String" },
      "example": "THI82O5JB7MQ2K76LL5FSDS2CB"
    },
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
  "responses": {
    "200": {
      "description": "OK",
      "content": {
        "application/json": {
          "schema": {
            "type": "array",
            "items": {
              "required": ["client_order_id", "combo_type", "orders"],
              "type": "object",
              "properties": {
                "client_order_id": {
                  "type": "string",
                  "description": "Client-defined order identifier.",
                  "example": "THI82O5JB7MQ2K76LL5FSDS2CB"
                },
                "combo_type": {
                  "type": "string",
                  "description": "Specifies the type of order combination. NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, OTO, OCO, OTOCO.",
                  "example": "NORMAL",
                  "enum": ["NORMAL", "MASTER", "STOP_PROFIT", "STOP_LOSS", "OTO", "OCO", "OTOCO"]
                },
                "orders": {
                  "type": "array",
                  "description": "Order Details",
                  "items": {
                    "required": ["client_order_id", "filled_time", "filled_time_at", "order_id", "order_type", "place_time", "place_time_at", "side", "status", "symbol", "time_in_force", "total_quantity"],
                    "type": "object",
                    "properties": {
                      "client_order_id": {
                        "type": "string",
                        "description": "Client-defined order identifier.",
                        "example": "THI82O5JB7MQ2K76LL5FSDS2CB"
                      },
                      "order_id": {
                        "type": "string",
                        "description": "System-generated order identifier.",
                        "example": "0352U72LQI6DT0KF41GK000000"
                      },
                      "symbol": {
                        "type": "string",
                        "description": "Trading symbol of the financial instrument.",
                        "example": "AAPL"
                      },
                      "side": {
                        "type": "string",
                        "description": "Order side: BUY, SELL, SHORT.",
                        "example": "BUY",
                        "enum": ["BUY", "SELL", "SHORT"]
                      },
                      "status": {
                        "type": "string",
                        "description": "Order status: PENDING, SUBMITTED, CANCELLED, FILLED, FAILED, PARTIAL_FILLED.",
                        "example": "SUBMITTED",
                        "enum": ["PENDING", "SUBMITTED", "CANCELLED", "FILLED", "FAILED", "PARTIAL_FILLED"]
                      },
                      "order_type": {
                        "type": "string",
                        "description": "Order type. Available types depend on market and instrument type.",
                        "example": "MARKET",
                        "enum": ["LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "ENHANCED_LIMIT", "AT_AUCTION", "AT_AUCTION_LIMIT", "MARKET_ON_OPEN", "TRAILING_STOP_LOSS", "TRAILING_STOP_LOSS_LIMIT", "TOUCH_MKT", "TOUCH_LMT"]
                      },
                      "instrument_type": {
                        "type": "string",
                        "description": "Type of financial instrument.",
                        "example": "STOCK",
                        "enum": ["EQUITY", "OPTION", "FUTURES"]
                      },
                      "support_trading_session": {
                        "type": "string",
                        "description": "Trading session for US stock orders. NIGHT, ALL, CORE, ALL_DAY.",
                        "example": "CORE",
                        "enum": ["Y", "N", "NIGHT", "ALL", "CORE", "ALL_DAY"]
                      },
                      "time_in_force": {
                        "type": "string",
                        "description": "Time-in-force: DAY, GTD, GTC.",
                        "example": "DAY",
                        "enum": ["DAY", "GTD", "GTC"]
                      },
                      "total_quantity": {
                        "type": "string",
                        "description": "Total order quantity.",
                        "example": "1"
                      },
                      "filled_quantity": {
                        "type": "string",
                        "description": "Quantity that has been executed.",
                        "example": "1"
                      },
                      "filled_price": {
                        "type": "string",
                        "description": "Average transaction price of the filled quantity.",
                        "example": "11.0"
                      },
                      "limit_price": {
                        "type": "string",
                        "description": "Limit price of the order.",
                        "example": "11.0"
                      },
                      "stop_price": {
                        "type": "string",
                        "description": "Stop price of the order.",
                        "example": "11.0"
                      },
                      "trailing_type": {
                        "type": "string",
                        "description": "Trailing type: AMOUNT or PERCENTAGE.",
                        "example": "AMOUNT",
                        "enum": ["AMOUNT", "PERCENTAGE"]
                      },
                      "trailing_stop_step": {
                        "type": "string",
                        "description": "Trailing Stop Spread.",
                        "example": "1"
                      },
                      "trailing_limit_price": {
                        "type": "string",
                        "description": "Trailing limit price of the order.",
                        "example": "11.0"
                      },
                      "trigger_price_type": {
                        "type": "string",
                        "description": "Trigger price type: PRICE, PRICE_BID, PRICE_ASK.",
                        "example": "PRICE",
                        "enum": ["PRICE", "PRICE_BID", "PRICE_ASK"]
                      },
                      "place_time": {
                        "type": "string",
                        "description": "Order placement time in milliseconds since Unix epoch.",
                        "example": "1726745361658"
                      },
                      "place_time_at": {
                        "type": "string",
                        "description": "Order placement time in ISO8601 format (UTC).",
                        "example": "2025-11-11T05:44:35.385Z"
                      },
                      "filled_time": {
                        "type": "string",
                        "description": "Time of the last executed trade in milliseconds since Unix epoch.",
                        "example": "1726745361871"
                      },
                      "filled_time_at": {
                        "type": "string",
                        "description": "Time of the last executed trade in ISO8601 format (UTC).",
                        "example": "2025-11-11T05:44:35.385Z"
                      },
                      "legs": {
                        "type": "array",
                        "description": "Leg detail",
                        "items": {
                          "required": ["option_category", "option_expire_date", "option_type", "quantity", "side", "strike_price", "symbol"],
                          "type": "object",
                          "properties": {
                            "symbol": { "type": "string", "description": "Trading symbol.", "example": "AAPL" },
                            "side": { "type": "string", "description": "Order side.", "example": "BUY", "enum": ["BUY", "SELL", "SHORT"] },
                            "quantity": { "type": "string", "description": "Quantity of the order.", "example": "1" },
                            "option_type": { "type": "string", "description": "Option type: CALL or PUT.", "example": "CALL", "enum": ["CALL", "PUT"] },
                            "option_category": { "type": "string", "description": "Option category: AMERICAN or EUROPEAN.", "example": "AMERICAN", "enum": ["AMERICAN", "EUROPEAN"] },
                            "option_strategy": { "type": "string", "description": "Options strategy type.", "example": "SINGLE", "enum": ["SINGLE"] },
                            "strike_price": { "type": "string", "description": "Exercise price (strike price).", "example": "190.0" },
                            "option_contract_multiplier": { "type": "string", "description": "Shares per option contract.", "example": "100" },
                            "option_contract_deliverable": { "type": "string", "description": "Shares required to exercise.", "example": "100" },
                            "option_expire_date": { "type": "string", "description": "Expiration date (yyyy-MM-dd).", "example": "2025-11-21" }
                          },
                          "title": "OrderListLeg"
                        }
                      }
                    },
                    "title": "OrderListItem"
                  }
                }
              },
              "title": "OrderListResult"
            }
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

## Parameters

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | String | Yes | Account identifier |
| page_size | String | No | Number of records per page (default 10, max 200) |
| last_client_order_id | String | No | Last client order ID for cursor-based pagination |

### Header Parameters

| Name | Required | Description |
|------|----------|-------------|
| x-app-key | Yes | A unique identifier issued to a developer for accessing an application's API. |
| x-app-secret | Yes | A unique key issued to developers to access the application's API. |
| x-timestamp | Yes | Timestamp of the request, follows ISO8601 format: YYYY-MM-DDThh:mm:ssZ |
| x-signature-version | Yes | Signature algorithm version, default is 1.0. |
| x-signature-algorithm | Yes | Signature algorithm, default is HMAC-SHA1. |
| x-signature-nonce | Yes | Signature unique random number. |
| x-access-token | Yes | An access token for accessing protected resources. |
| x-version | Yes | Interface version, Accepts only the value v2. |
| x-signature | Yes | A digital fingerprint that verifies authenticity and integrity. |

## Response

### 200 OK

Returns an array of order objects:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| client_order_id | string | Client-defined order identifier | THI82O5JB7MQ2K76LL5FSDS2CB |
| combo_type | string | Order combination type (NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, OTO, OCO, OTOCO) | NORMAL |
| orders | array | Array of order detail objects | (see below) |

#### orders items

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| client_order_id | string | Client-defined order identifier | THI82O5JB7MQ2K76LL5FSDS2CB |
| order_id | string | System-generated order identifier | 0352U72LQI6DT0KF41GK000000 |
| symbol | string | Trading symbol | AAPL |
| side | string | Order side (BUY, SELL, SHORT) | BUY |
| status | string | Order status (PENDING, SUBMITTED, CANCELLED, FILLED, FAILED, PARTIAL_FILLED) | SUBMITTED |
| order_type | string | Order type | MARKET |
| instrument_type | string | Instrument type (EQUITY, OPTION, FUTURES) | STOCK |
| support_trading_session | string | Trading session (NIGHT, ALL, CORE, ALL_DAY) | CORE |
| time_in_force | string | Time-in-force (DAY, GTD, GTC) | DAY |
| total_quantity | string | Total order quantity | 1 |
| filled_quantity | string | Executed quantity | 1 |
| filled_price | string | Average fill price | 11.0 |
| limit_price | string | Limit price | 11.0 |
| stop_price | string | Stop price | 11.0 |
| trailing_type | string | Trailing type (AMOUNT, PERCENTAGE) | AMOUNT |
| trailing_stop_step | string | Trailing stop spread | 1 |
| trailing_limit_price | string | Trailing limit price | 11.0 |
| trigger_price_type | string | Trigger price type (PRICE, PRICE_BID, PRICE_ASK) | PRICE |
| place_time | string | Placement time (ms epoch) | 1726745361658 |
| place_time_at | string | Placement time (ISO8601) | 2025-11-11T05:44:35.385Z |
| filled_time | string | Last fill time (ms epoch) | 1726745361871 |
| filled_time_at | string | Last fill time (ISO8601) | 2025-11-11T05:44:35.385Z |
| legs | array | Option leg details | (see below) |

#### legs items (for option orders)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| symbol | string | Trading symbol | AAPL |
| side | string | Order side (BUY, SELL, SHORT) | BUY |
| quantity | string | Quantity | 1 |
| option_type | string | Option type (CALL, PUT) | CALL |
| option_category | string | Option category (AMERICAN, EUROPEAN) | AMERICAN |
| option_strategy | string | Options strategy (SINGLE) | SINGLE |
| strike_price | string | Exercise price | 190.0 |
| option_contract_multiplier | string | Shares per contract | 100 |
| option_contract_deliverable | string | Shares required to exercise | 100 |
| option_expire_date | string | Expiration date (yyyy-MM-dd) | 2025-11-21 |

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized: Authentication required |
| 417 | Business logic error |
| 500 | Internal Server Error |
