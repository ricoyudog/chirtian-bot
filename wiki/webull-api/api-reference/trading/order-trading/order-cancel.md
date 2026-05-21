---
title: "Order Cancel"
method: POST
endpoint: /openapi/trade/order/cancel
rate_limit: "15 req/s (US), 1 req/s (HK/A-share)"
source: https://developer.webull.hk/apis/docs/reference/common-order-cancel
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Order Cancel

- Function description: Cancel orders for equities, options.
- Frequency limit: US stock order interface: 15 requests/second, HK/A-share order interface: 1 request/second

## OpenAPI definition

```json
{
  "path": "/openapi/trade/order/cancel",
  "method": "post",
  "tags": ["Trading"],
  "operationId": "Common Order Cancel",
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
          "required": ["account_id", "client_order_id"],
          "type": "object",
          "properties": {
            "account_id": {
              "type": "string",
              "description": "Account identifier",
              "example": "93IUJ28O9VO2KBGHDHR4H9"
            },
            "client_order_id": {
              "type": "string",
              "description": "Unique client-defined identifier for the order to cancel. Max 32 chars.",
              "example": "0KGOHL4PR2SLC0DKIND4TI0002"
            }
          },
          "title": "OrderCommonCancelParam"
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
| client_order_id | string | Yes | Unique client-defined identifier of the order to cancel |

### Request Example

```json
{
  "account_id": "93IUJ28O9VO2KBGHDHR4H9",
  "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002"
}
```

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
