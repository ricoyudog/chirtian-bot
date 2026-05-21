---
title: "Account List"
method: GET
endpoint: /openapi/account/list
rate_limit: "N/A"
source: https://developer.webull.hk/apis/docs/reference/account-list
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Account List

- Function description: Query the account list and return account information.

## OpenAPI definition

```json
{
  "info": {
    "title": "Webull OpenAPI Documentation",
    "description": "The Webull OpenAPI enables integration of trading APIs, market data for building trading applications and brokerage solutions.",
    "version": "2.0"
  },
  "servers": [
    {
      "url": "https://api.sandbox.webull.hk"
    }
  ],
  "path": "/openapi/account/list",
  "method": "get",
  "tags": [
    "Account"
  ],
  "description": "Query the account list and return account information.",
  "operationId": "accountList",
  "parameters": [
    {
      "name": "x-app-key",
      "in": "header",
      "description": "A unique identifier issued to a developer for accessing an application's API.",
      "required": true,
      "schema": { "type": "string" }
    },
    {
      "name": "x-app-secret",
      "in": "header",
      "description": "A unique key issued to developers to access the application's API.",
      "required": true,
      "schema": { "type": "string" }
    },
    {
      "name": "x-timestamp",
      "in": "header",
      "description": "Timestamp of the request, follows ISO8601 format: YYYY-MM-DDThh:mm:ssZ, e.g. 2023-07-16T19:23:51Z, only supports UTC time zone.",
      "required": true,
      "schema": { "type": "string" }
    },
    {
      "name": "x-signature-version",
      "in": "header",
      "description": "Signature algorithm version, default is 1.0.",
      "required": true,
      "schema": { "type": "string", "default": "1.0" },
      "examples": { "1.0": { "value": "1.0" } }
    },
    {
      "name": "x-signature-algorithm",
      "in": "header",
      "description": "Signature algorithm, default is HMAC-SHA1.",
      "required": true,
      "schema": { "type": "string", "default": "HMAC-SHA1" },
      "examples": { "HMAC-SHA1": { "value": "HMAC-SHA1" } }
    },
    {
      "name": "x-signature-nonce",
      "in": "header",
      "description": "Signature unique random number.",
      "required": true,
      "schema": { "type": "string" }
    },
    {
      "name": "x-access-token",
      "in": "header",
      "description": "An access token is a credential that represents the authorization granted to a client to access specific protected resources on behalf of a user.",
      "required": true,
      "schema": { "type": "string" }
    },
    {
      "name": "x-version",
      "in": "header",
      "description": "Interface version, Accepts only the value v2.",
      "required": true,
      "schema": { "type": "string", "default": "v2" },
      "examples": { "v2": { "value": "v2" } }
    },
    {
      "name": "x-signature",
      "in": "header",
      "description": "A signature is a unique digital fingerprint that verifies the authenticity and integrity of a message or transaction.",
      "required": true,
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
              "type": "object",
              "properties": {
                "account_id": {
                  "type": "string",
                  "description": "Account identifier",
                  "example": "LOJOQITOD49R6G9BPQM489CISA"
                },
                "account_number": {
                  "type": "string",
                  "description": "Brokerage account",
                  "example": "10010048"
                },
                "account_type": {
                  "type": "string",
                  "description": "Account type",
                  "example": "CASH",
                  "enum": ["MARGIN", "CASH"]
                },
                "account_class": {
                  "type": "string",
                  "description": "Account Class",
                  "example": "INDIVIDUAL_CASH",
                  "enum": [
                    "INDIVIDUAL_CASH",
                    "INDIVIDUAL_MRGN",
                    "FUTURES_MRGN",
                    "INSTITUTIONAL_CASH",
                    "INSTITUTIONAL_MRGN",
                    "INSTITUTIONAL_FUTURES_MRGN"
                  ]
                }
              },
              "title": "AccountListResult"
            }
          }
        }
      }
    },
    "401": {
      "description": "Unauthorized: Authentication required",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "error_code": { "type": "string", "example": "UNAUTHORIZED" },
              "message": { "type": "string", "example": "Insufficient permission" }
            }
          }
        }
      }
    },
    "417": {
      "description": "A business logic error triggered when the request cannot be processed due to domain-specific constraints.",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "error_code": { "type": "string", "example": "INVALID_PARAMETER" },
              "message": { "type": "string", "example": "Parameter error, phone" }
            }
          }
        }
      }
    },
    "500": {
      "description": "Internal Server Error.",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "error_code": { "type": "string", "example": "SYSTEM_ERROR" },
              "message": { "type": "string", "example": "Internal Server Error" }
            }
          }
        }
      }
    }
  }
}
```

## Parameters

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

Returns an array of account objects:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| account_id | string | Account identifier | LOJOQITOD49R6G9BPQM489CISA |
| account_number | string | Brokerage account | 10010048 |
| account_type | string | Account type (MARGIN, CASH) | CASH |
| account_class | string | Account Class | INDIVIDUAL_CASH |

#### account_class Enum Values

| Value | Description |
|-------|-------------|
| INDIVIDUAL_CASH | Individual cash account |
| INDIVIDUAL_MRGN | Individual margin account |
| FUTURES_MRGN | Futures margin account |
| INSTITUTIONAL_CASH | Institutional cash account |
| INSTITUTIONAL_MRGN | Institutional margin account |
| INSTITUTIONAL_FUTURES_MRGN | Institutional futures margin account |

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized: Authentication required |
| 417 | Business logic error (invalid parameters, etc.) |
| 500 | Internal Server Error |
