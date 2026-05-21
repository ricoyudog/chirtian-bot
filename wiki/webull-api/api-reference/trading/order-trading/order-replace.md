---
title: "Order Replace"
method: POST
endpoint: /openapi/trade/order/replace
rate_limit: "15 req/s (US), 1 req/s (HK/A-share)"
source: https://developer.webull.hk/apis/docs/reference/common-order-replace
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Order Replace

- Function description: Modify equity, options orders.
- Frequency limit: US stock order interface: 15 requests/second, HK/A-share order interface: 1 request/second

## OpenAPI definition

```json
{
  "path": "/openapi/trade/order/replace",
  "method": "post",
  "tags": ["Trading"],
  "operationId": "Common Order Replace",
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
    "content": {
      "application/json": {
        "schema": {
          "required": ["account_id", "modify_orders"],
          "type": "object",
          "properties": {
            "account_id": {
              "type": "string",
              "description": "Account identifier",
              "example": "93IUJ28O9VO2KBGHDHR4H9"
            },
            "modify_orders": {
              "type": "array",
              "description": "Order Details",
              "items": {
                "required": ["client_order_id"],
                "type": "object",
                "properties": {
                  "client_order_id": {
                    "type": "string",
                    "description": "Unique client-defined identifier for the order. Max 32 chars.",
                    "example": "0KGOHL4PR2SLC0DKIND4TI0002"
                  },
                  "time_in_force": {
                    "type": "string",
                    "description": "DAY, GTD, GTC",
                    "example": "DAY",
                    "enum": ["DAY", "GTD", "GTC"]
                  },
                  "quantity": {
                    "type": "string",
                    "description": "Transaction quantity",
                    "example": "1"
                  },
                  "expire_date": {
                    "type": "string",
                    "description": "GTD expire date (yyyy-MM-dd)",
                    "example": "2026-01-01"
                  },
                  "limit_price": {
                    "type": "string",
                    "description": "Limit price",
                    "example": "11.0"
                  },
                  "stop_price": {
                    "type": "string",
                    "description": "Stop price",
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
                    "description": "Trailing limit price",
                    "example": "11.0"
                  },
                  "trigger_price_type": {
                    "type": "string",
                    "description": "PRICE, PRICE_BID, PRICE_ASK",
                    "example": "PRICE",
                    "enum": ["PRICE", "PRICE_BID", "PRICE_ASK"]
                  }
                },
                "title": "OrderCommonReplaceItemParam"
              }
            }
          },
          "title": "OrderCommonReplaceParam"
        }
      }
    }
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
| modify_orders | array | Yes | Array of modify order objects |

### modify_orders items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| client_order_id | string | Yes | Unique client-defined identifier to identify the order to modify |
| time_in_force | string | No | DAY, GTD, GTC |
| quantity | string | No | New transaction quantity |
| expire_date | string | No | GTD expire date (yyyy-MM-dd) |
| limit_price | string | No | New limit price |
| stop_price | string | No | New stop price |
| trailing_type | string | No | AMOUNT or PERCENTAGE |
| trailing_stop_step | string | No | Trailing stop spread |
| trailing_limit_price | string | No | Trailing limit price |
| trigger_price_type | string | No | PRICE, PRICE_BID, PRICE_ASK |

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
