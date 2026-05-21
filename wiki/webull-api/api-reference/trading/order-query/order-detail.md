---
title: "Order Detail"
method: GET
endpoint: /openapi/trade/order/detail
rate_limit: "40 req/2s"
source: https://developer.webull.hk/apis/docs/reference/order-detail
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Order Detail

- Function description: Order details, query the specified order details through the order ID.
- Frequency limit: Rate limit 40 requests every 2 seconds

## OpenAPI definition

```json
{
  "path": "/openapi/trade/order/detail",
  "method": "get",
  "tags": ["Order Query"],
  "operationId": "orderDetail",
  "parameters": [
    {
      "name": "account_id", "in": "query", "required": true,
      "description": "Account identifier.",
      "schema": { "type": "String" },
      "example": "LOJOQITOD49R6G9BPQM489CISA"
    },
    {
      "name": "client_order_id", "in": "query", "required": true,
      "description": "Unique client-defined identifier for the order. Maximum length is 32 characters and must be unique per account.",
      "schema": { "type": "String" },
      "example": "0KGOHL4PR2SLC0DKIND4TI0002"
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
                "description": "NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, OTO, OCO, OTOCO",
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
                      "description": "Trading symbol.",
                      "example": "AAPL"
                    },
                    "side": {
                      "type": "string",
                      "description": "BUY, SELL, SHORT.",
                      "example": "BUY",
                      "enum": ["BUY", "SELL", "SHORT"]
                    },
                    "status": {
                      "type": "string",
                      "description": "PENDING, SUBMITTED, CANCELLED, FILLED, FAILED, PARTIAL_FILLED.",
                      "example": "SUBMITTED",
                      "enum": ["PENDING", "SUBMITTED", "CANCELLED", "FILLED", "FAILED", "PARTIAL_FILLED"]
                    },
                    "order_type": {
                      "type": "string",
                      "description": "Order type. Available types depend on market and instrument.",
                      "example": "MARKET",
                      "enum": ["LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "ENHANCED_LIMIT", "AT_AUCTION", "AT_AUCTION_LIMIT", "MARKET_ON_OPEN", "TRAILING_STOP_LOSS", "TRAILING_STOP_LOSS_LIMIT", "TOUCH_MKT", "TOUCH_LMT"]
                    },
                    "instrument_type": {
                      "type": "string",
                      "description": "EQUITY, OPTION, FUTURES.",
                      "example": "STOCK",
                      "enum": ["EQUITY", "OPTION", "FUTURES"]
                    },
                    "support_trading_session": {
                      "type": "string",
                      "description": "Trading session for US stock orders.",
                      "example": "CORE",
                      "enum": ["Y", "N", "NIGHT", "ALL", "CORE", "ALL_DAY"]
                    },
                    "time_in_force": {
                      "type": "string",
                      "description": "DAY, GTD, GTC.",
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
                          "quantity": { "type": "string", "description": "Quantity.", "example": "1" },
                          "option_type": { "type": "string", "description": "CALL or PUT.", "example": "CALL", "enum": ["CALL", "PUT"] },
                          "option_category": { "type": "string", "description": "AMERICAN or EUROPEAN.", "example": "AMERICAN", "enum": ["AMERICAN", "EUROPEAN"] },
                          "option_strategy": { "type": "string", "description": "SINGLE.", "example": "SINGLE", "enum": ["SINGLE"] },
                          "strike_price": { "type": "string", "description": "Exercise price.", "example": "190.0" },
                          "option_contract_multiplier": { "type": "string", "description": "Shares per contract.", "example": "100" },
                          "option_contract_deliverable": { "type": "string", "description": "Shares required to exercise.", "example": "100" },
                          "option_expire_date": { "type": "string", "description": "Expiration date (yyyy-MM-dd).", "example": "2025-11-21" }
                        },
                        "title": "OrderListLeg"
                      }
                    },
                    "commission": {
                      "type": "object",
                      "description": "Commission breakdown",
                      "properties": {
                        "actual_commission": { "type": "string", "description": "Actual commission collected", "example": "1.0" },
                        "receivable_commission": { "type": "string", "description": "Receivable commission", "example": "1.0" }
                      },
                      "title": "CommonCommissionResultVO"
                    },
                    "fees": {
                      "type": "array",
                      "description": "Fee breakdown",
                      "items": {
                        "type": "object",
                        "properties": {
                          "type": { "type": "string", "description": "Fee type", "example": "FINRA_CAT_REGULATORY_FEE" },
                          "actual_value": { "type": "string", "description": "Actual fee collected", "example": "1.0" },
                          "receivable_value": { "type": "string", "description": "Receivable fee", "example": "1.0" }
                        },
                        "title": "CommonFeeResultVO"
                      }
                    }
                  },
                  "title": "OrderDetailItem"
                }
              }
            },
            "title": "OrderDetailResult"
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
| client_order_id | String | Yes | Unique client-defined identifier for the order (max 32 chars) |

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

Returns a single order detail object:

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
| place_time | string | Placement time (ms epoch) | 1726745361658 |
| place_time_at | string | Placement time (ISO8601) | 2025-11-11T05:44:35.385Z |
| filled_time | string | Last fill time (ms epoch) | 1726745361871 |
| filled_time_at | string | Last fill time (ISO8601) | 2025-11-11T05:44:35.385Z |
| legs | array | Option leg details | (see open-order.md for legs structure) |
| commission | object | Commission breakdown | (see below) |
| fees | array | Fee breakdown | (see below) |

#### commission object

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| actual_commission | string | Actual commission collected | 1.0 |
| receivable_commission | string | Receivable commission | 1.0 |

#### fees items

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| type | string | Fee type | FINRA_CAT_REGULATORY_FEE |
| actual_value | string | Actual fee collected | 1.0 |
| receivable_value | string | Receivable fee | 1.0 |

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized: Authentication required |
| 417 | Business logic error |
| 500 | Internal Server Error |
