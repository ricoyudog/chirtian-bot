---
title: "Account Positions"
method: GET
endpoint: /openapi/assets/positions
rate_limit: "N/A"
source: https://developer.webull.hk/apis/docs/reference/query-account-position
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Account Positions

- Function description: Query positions according to the account ID.

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
  "path": "/openapi/assets/positions",
  "method": "get",
  "tags": [
    "Assets"
  ],
  "description": "Query positions according to the account ID.",
  "operationId": "queryAccountPosition",
  "parameters": [
    {
      "name": "account_id",
      "in": "query",
      "description": "Account identifier",
      "required": true,
      "schema": { "type": "String" },
      "example": "LOJOQITOD49R6G9BPQM489CISA"
    },
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
              "required": [
                "cost_price",
                "currency",
                "instrument_type",
                "last_price",
                "option_strategy",
                "position_id",
                "quantity",
                "symbol",
                "unrealized_profit_loss"
              ],
              "type": "object",
              "properties": {
                "position_id": {
                  "type": "string",
                  "description": "Position ID",
                  "example": "N4I4SIM8TJF38KN2TAA0QVVNE9"
                },
                "currency": {
                  "type": "string",
                  "description": "Currency",
                  "example": "USD",
                  "enum": ["CNH", "HKD", "USD"]
                },
                "quantity": {
                  "type": "string",
                  "description": "Quantity of the order. Specifies the number of shares or units to transact. For US stocks, fractional quantities are allowed.",
                  "example": "1"
                },
                "symbol": {
                  "type": "string",
                  "description": "Trading symbol of the financial instrument.",
                  "example": "AAPL"
                },
                "option_strategy": {
                  "type": "string",
                  "description": "Type of options strategy. SINGLE: Indicates a single-leg options order",
                  "example": "SINGLE",
                  "enum": ["SINGLE"]
                },
                "instrument_type": {
                  "type": "string",
                  "description": "Type of financial instrument associated with the request.",
                  "example": "EQUITY",
                  "enum": ["EQUITY", "OPTION", "FUTURES"]
                },
                "last_price": {
                  "type": "string",
                  "description": "Last Price",
                  "example": "10.0"
                },
                "cost_price": {
                  "type": "string",
                  "description": "Cost Basis",
                  "example": "11.12"
                },
                "unrealized_profit_loss": {
                  "type": "string",
                  "description": "Open P&L",
                  "example": "0.08"
                },
                "legs": {
                  "type": "array",
                  "description": "Legs details for option positions",
                  "items": {
                    "required": ["symbol"],
                    "type": "object",
                    "properties": {
                      "symbol": {
                        "type": "string",
                        "description": "Trading symbol of the financial instrument.",
                        "example": "AAPL"
                      },
                      "quantity": {
                        "type": "string",
                        "description": "Quantity of the order.",
                        "example": "4"
                      },
                      "option_type": {
                        "type": "string",
                        "description": "Type of the option. CALL: Right to buy. PUT: Right to sell.",
                        "example": "CALL",
                        "enum": ["CALL", "PUT"]
                      },
                      "option_expire_date": {
                        "type": "string",
                        "description": "Option expiration date. Format: yyyy-MM-dd",
                        "example": "2019-09-20"
                      },
                      "option_exercise_price": {
                        "type": "string",
                        "description": "Exercise Price",
                        "example": "11.0"
                      },
                      "option_contract_multiplier": {
                        "type": "string",
                        "description": "The number of shares corresponding to each option contract",
                        "example": "100"
                      },
                      "option_contract_deliverable": {
                        "type": "string",
                        "description": "The number of shares required to exercise each contract",
                        "example": "100"
                      },
                      "expiration_type": {
                        "type": "string",
                        "description": "Option expiration types",
                        "example": "AM"
                      }
                    },
                    "title": "PositionItem"
                  }
                }
              },
              "title": "AssetsPositionResult"
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

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | String | Yes | Account identifier. Example: `LOJOQITOD49R6G9BPQM489CISA` |

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

Returns an array of position objects:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| position_id | string | Position ID | N4I4SIM8TJF38KN2TAA0QVVNE9 |
| currency | string | Currency (CNH, HKD, USD) | USD |
| quantity | string | Quantity of the order | 1 |
| symbol | string | Trading symbol | AAPL |
| option_strategy | string | Options strategy type (SINGLE) | SINGLE |
| instrument_type | string | Financial instrument type (EQUITY, OPTION, FUTURES) | EQUITY |
| last_price | string | Last Price | 10.0 |
| cost_price | string | Cost Basis | 11.12 |
| unrealized_profit_loss | string | Open P&L | 0.08 |
| legs | array | Legs details for option positions | (see below) |

#### legs items (for option positions)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| symbol | string | Trading symbol | AAPL |
| quantity | string | Quantity | 4 |
| option_type | string | Option type (CALL, PUT) | CALL |
| option_expire_date | string | Expiration date (yyyy-MM-dd) | 2019-09-20 |
| option_exercise_price | string | Exercise Price | 11.0 |
| option_contract_multiplier | string | Shares per option contract | 100 |
| option_contract_deliverable | string | Shares required to exercise | 100 |
| expiration_type | string | Option expiration types | AM |

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized: Authentication required |
| 417 | Business logic error (invalid parameters, etc.) |
| 500 | Internal Server Error |
