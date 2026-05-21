---
title: "Account Balance"
method: GET
endpoint: /openapi/assets/balance
rate_limit: "N/A"
source: https://developer.webull.hk/apis/docs/reference/query-account-balance
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Account Balance

- Function description: Query account details by account ID.

## OpenAPI definition

```json
{
  "info": {
    "title": "Webull OpenAPI Documentation",
    "description": "The Webull OpenAPI enables integration of trading APIs, market data for building trading applications and brokerage solutions. It supports HTTP-based historical and real-time market data and MQTT streaming via WebSocket/TCP, along with SDKs, secure authentication, and APIs for orders, accounts, and event contract trading.",
    "contact": {
      "name": "Webull Developer Support",
      "url": "https://www.webull.hk/en/help",
      "email": "webull-api-support@webull.com"
    },
    "version": "2.0",
    "x-logo": {
      "url": "static/png/logo.png"
    }
  },
  "servers": [
    {
      "url": "https://api.sandbox.webull.hk"
    }
  ],
  "path": "/openapi/assets/balance",
  "method": "get",
  "tags": [
    "Assets"
  ],
  "description": "Query account details by account ID.",
  "operationId": "queryAccountBalance",
  "parameters": [
    {
      "name": "account_id",
      "in": "query",
      "description": "Account identifier",
      "required": true,
      "schema": {
        "type": "String"
      },
      "example": "LOJOQITOD49R6G9BPQM489CISA"
    },
    {
      "name": "x-app-key",
      "in": "header",
      "description": "A unique identifier issued to a developer for accessing an application's API.",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "x-app-secret",
      "in": "header",
      "description": "A unique key issued to developers to access the application's API.",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "x-timestamp",
      "in": "header",
      "description": "Timestamp of the request, follows ISO8601 format: YYYY-MM-DDThh:mm:ssZ, e.g. 2023-07-16T19:23:51Z, only supports UTC time zone.",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "x-signature-version",
      "in": "header",
      "description": "Signature algorithm version, default is 1.0.",
      "required": true,
      "schema": {
        "type": "string",
        "default": "1.0"
      },
      "examples": {
        "1.0": {
          "value": "1.0"
        }
      }
    },
    {
      "name": "x-signature-algorithm",
      "in": "header",
      "description": "Signature algorithm, default is HMAC-SHA1.",
      "required": true,
      "schema": {
        "type": "string",
        "default": "HMAC-SHA1"
      },
      "examples": {
        "HMAC-SHA1": {
          "value": "HMAC-SHA1"
        }
      }
    },
    {
      "name": "x-signature-nonce",
      "in": "header",
      "description": "Signature unique random number.",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "x-access-token",
      "in": "header",
      "description": "An access token is a credential that represents the authorization granted to a client (e.g., a user or an application) to access specific protected resources on behalf of a user, without needing to share their password.",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "x-version",
      "in": "header",
      "description": "Interface version, Accepts only the value v2.",
      "required": true,
      "schema": {
        "type": "string",
        "default": "v2"
      },
      "examples": {
        "v2": {
          "value": "v2"
        }
      }
    },
    {
      "name": "x-signature",
      "in": "header",
      "description": "A signature is a unique digital fingerprint, typically encrypted, that verifies the authenticity and integrity of a message or transaction, ensuring it has not been tampered with during transmission.",
      "required": true,
      "schema": {
        "type": "string"
      }
    }
  ],
  "responses": {
    "200": {
      "description": "OK",
      "content": {
        "application/json": {
          "schema": {
            "required": [
              "account_currency_assets",
              "total_asset_currency",
              "total_cash_balance",
              "total_market_value",
              "total_unrealized_profit_loss"
            ],
            "type": "object",
            "properties": {
              "total_asset_currency": {
                "type": "string",
                "description": "Currency",
                "example": "HKD",
                "enum": [
                  "CNH",
                  "HKD",
                  "USD"
                ]
              },
              "total_cash_balance": {
                "type": "string",
                "description": "Cash Balance",
                "example": "485705.0"
              },
              "total_market_value": {
                "type": "string",
                "description": "Total holding market value",
                "example": "995705.0"
              },
              "total_unrealized_profit_loss": {
                "type": "string",
                "description": "Open P&L",
                "example": "227689.0"
              },
              "account_currency_assets": {
                "type": "array",
                "description": "Currency assets Details",
                "items": {
                  "required": [
                    "available_withdrawal",
                    "buying_power",
                    "cash_balance",
                    "currency",
                    "interests_unpaid",
                    "market_value",
                    "settled_cash",
                    "unrealized_profit_loss",
                    "unsettled_cash"
                  ],
                  "type": "object",
                  "properties": {
                    "currency": {
                      "type": "string",
                      "description": "Currency",
                      "example": "HKD",
                      "enum": [
                        "CNH",
                        "HKD",
                        "USD"
                      ]
                    },
                    "cash_balance": {
                      "type": "string",
                      "description": "Cash Balance",
                      "example": "485705.95"
                    },
                    "settled_cash": {
                      "type": "string",
                      "description": "Settled Cash",
                      "example": "485705.95"
                    },
                    "unsettled_cash": {
                      "type": "string",
                      "description": "Unsettled Cash",
                      "example": "0.0"
                    },
                    "market_value": {
                      "type": "string",
                      "description": "Holding market value",
                      "example": "0.0"
                    },
                    "held_amount": {
                      "type": "string",
                      "description": "In-transit funds",
                      "example": "0.0"
                    },
                    "frozen_amount": {
                      "type": "string",
                      "description": "Frozen funds",
                      "example": "485705"
                    },
                    "buying_power": {
                      "type": "string",
                      "description": "Buying Power",
                      "example": "484551"
                    },
                    "unrealized_profit_loss": {
                      "type": "string",
                      "description": "Open P&L",
                      "example": "227689"
                    },
                    "available_withdrawal": {
                      "type": "string",
                      "description": "The withdrawable amount",
                      "example": "3.0558743194E8"
                    },
                    "interests_unpaid": {
                      "type": "string",
                      "description": "Interest to be paid",
                      "example": "0.0"
                    }
                  },
                  "description": "Currency assets Details",
                  "title": "AssetsCurrencyAssets"
                }
              }
            },
            "title": "AssetsBalanceResult"
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
              "error_code": {
                "type": "string",
                "description": "Internal logic error code",
                "example": "UNAUTHORIZED"
              },
              "message": {
                "type": "string",
                "description": "Error message",
                "example": "Insufficient permission"
              }
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
              "error_code": {
                "type": "string",
                "description": "Internal logic error code",
                "example": "INVALID_PARAMETER"
              },
              "message": {
                "type": "string",
                "description": "Error message",
                "example": "Parameter error, phone"
              }
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
              "error_code": {
                "type": "string",
                "description": "Internal logic error code",
                "example": "SYSTEM_ERROR"
              },
              "message": {
                "type": "string",
                "description": "Error message",
                "example": "Internal Server Error"
              }
            }
          }
        }
      }
    }
  },
  "postman": {
    "name": "Account Balance",
    "description": {
      "content": "Query account details by account ID.",
      "type": "text/plain"
    },
    "url": {
      "path": [
        "openapi",
        "assets",
        "balance"
      ],
      "host": [
        "{{baseUrl}}"
      ],
      "query": [
        {
          "disabled": false,
          "description": {
            "content": "(Required) Account identifier",
            "type": "text/plain"
          },
          "key": "account_id",
          "value": ""
        }
      ],
      "variable": []
    },
    "header": [
      {
        "disabled": false,
        "description": {
          "content": "(Required) A unique identifier issued to a developer for accessing an application's API.",
          "type": "text/plain"
        },
        "key": "x-app-key",
        "value": ""
      },
      {
        "disabled": false,
        "description": {
          "content": "(Required) A unique key issued to developers to access the application's API.",
          "type": "text/plain"
        },
        "key": "x-app-secret",
        "value": ""
      },
      {
        "disabled": false,
        "description": {
          "content": "(Required) Timestamp of the request, follows ISO8601 format: YYYY-MM-DDThh:mm:ssZ, e.g. 2023-07-16T19:23:51Z, only supports UTC time zone.",
          "type": "text/plain"
        },
        "key": "x-timestamp",
        "value": ""
      },
      {
        "disabled": false,
        "description": {
          "content": "(Required) Signature algorithm version, default is 1.0.",
          "type": "text/plain"
        },
        "key": "x-signature-version",
        "value": ""
      },
      {
        "disabled": false,
        "description": {
          "content": "(Required) Signature algorithm, default is HMAC-SHA1.",
          "type": "text/plain"
        },
        "key": "x-signature-algorithm",
        "value": ""
      },
      {
        "disabled": false,
        "description": {
          "content": "(Required) Signature unique random number.",
          "type": "text/plain"
        },
        "key": "x-signature-nonce",
        "value": ""
      },
      {
        "disabled": false,
        "description": {
          "content": "(Required) An access token is a credential that represents the authorization granted to a client (e.g., a user or an application) to access specific protected resources on behalf of a user, without needing to share their password.",
          "type": "text/plain"
        },
        "key": "x-access-token",
        "value": ""
      },
      {
        "disabled": false,
        "description": {
          "content": "(Required) Interface version, Accepts only the value v2.",
          "type": "text/plain"
        },
        "key": "x-version",
        "value": ""
      },
      {
        "disabled": false,
        "description": {
          "content": "(Required) A signature is a unique digital fingerprint, typically encrypted, that verifies the authenticity and integrity of a message or transaction, ensuring it has not been tampered with during transmission.",
          "type": "text/plain"
        },
        "key": "x-signature",
        "value": ""
      },
      {
        "key": "Accept",
        "value": "application/json"
      }
    ],
    "method": "GET"
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

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| total_asset_currency | string | Currency (CNH, HKD, USD) | HKD |
| total_cash_balance | string | Cash Balance | 485705.0 |
| total_market_value | string | Total holding market value | 995705.0 |
| total_unrealized_profit_loss | string | Open P&L | 227689.0 |
| account_currency_assets | array | Currency assets Details | (see below) |

#### account_currency_assets items

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| currency | string | Currency (CNH, HKD, USD) | HKD |
| cash_balance | string | Cash Balance | 485705.95 |
| settled_cash | string | Settled Cash | 485705.95 |
| unsettled_cash | string | Unsettled Cash | 0.0 |
| market_value | string | Holding market value | 0.0 |
| held_amount | string | In-transit funds | 0.0 |
| frozen_amount | string | Frozen funds | 485705 |
| buying_power | string | Buying Power | 484551 |
| unrealized_profit_loss | string | Open P&L | 227689 |
| available_withdrawal | string | The withdrawable amount | 3.0558743194E8 |
| interests_unpaid | string | Interest to be paid | 0.0 |

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized: Authentication required |
| 417 | Business logic error (invalid parameters, etc.) |
| 500 | Internal Server Error |
