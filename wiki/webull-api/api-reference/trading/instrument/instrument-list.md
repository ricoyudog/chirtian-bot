---
title: "Get Stock Instrument"
method: GET
endpoint: /openapi/instrument/stock/list
rate_limit: "60 req/60s"
source: https://developer.webull.hk/apis/docs/reference/instrument-list
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Get Stock Instrument

- Function description: Get profile information for one or more instruments.
- Frequency limit: Rate limit 60 requests every 60 seconds

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
  "path": "/openapi/instrument/stock/list",
  "method": "get",
  "tags": [
    "Instrument"
  ],
  "description": "Get profile information for one or more instruments. Rate limit 60 requests every 60 seconds",
  "operationId": "instrumentList",
  "parameters": [
    {
      "name": "symbols",
      "in": "query",
      "description": "List of security symbols, maximum 100 symbols per query.",
      "required": false,
      "schema": {
        "type": "string"
      },
      "example": "AAPL,TSLA"
    },
    {
      "name": "category",
      "in": "query",
      "description": "Security type.",
      "required": true,
      "schema": {
        "type": "string",
        "enum": [
          "US_STOCK",
          "US_ETF",
          "HK_STOCK",
          "CN_STOCK"
        ]
      },
      "example": "US_STOCK"
    },
    {
      "name": "status",
      "in": "query",
      "description": "Tradable status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable)",
      "required": false,
      "schema": {
        "type": "string",
        "description": "Tradable status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable)",
        "enum": [
          "OC",
          "CO",
          "NT"
        ]
      },
      "example": "CO"
    },
    {
      "name": "last_instrument_id",
      "in": "query",
      "description": "Last instrument id for pagination",
      "required": false,
      "schema": {
        "type": "string"
      },
      "example": 951007842
    },
    {
      "name": "page_size",
      "in": "query",
      "description": "Page size, default 1000",
      "required": false,
      "schema": {
        "type": "integer",
        "format": "int32",
        "default": 1000
      },
      "example": 1000
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
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": {
                  "type": "string",
                  "description": "Symbol name, e.g. Apple",
                  "example": "APPLE INC"
                },
                "instrument_id": {
                  "type": "string",
                  "description": "Unique identifier of the security",
                  "example": "10152734329"
                },
                "exchange_code": {
                  "type": "string",
                  "description": "Exchange code, e.g. CCC",
                  "example": "NSQ"
                },
                "category": {
                  "type": "string",
                  "description": "Instrument type, e.g. US_STOCK",
                  "example": "US_STOCK",
                  "enum": [
                    "US_STOCK",
                    "US_ETF",
                    "HK_STOCK",
                    "CN_STOCK"
                  ]
                },
                "symbol": {
                  "type": "string",
                  "description": "Symbol of the instrument",
                  "example": "AAPL"
                },
                "status": {
                  "type": "string",
                  "description": "Tradable status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable)",
                  "example": "OC",
                  "enum": [
                    "OC",
                    "CO",
                    "NT"
                  ]
                },
                "shortable": {
                  "type": "boolean",
                  "description": "Instrument is shortable or not",
                  "example": false
                },
                "fractionable": {
                  "type": "boolean",
                  "description": "Instrument is fractionable or not",
                  "example": false
                },
                "marginable": {
                  "type": "boolean",
                  "description": "Instrument is marginable or not",
                  "example": false
                },
                "overnight_trading_supported": {
                  "type": "boolean",
                  "description": "Instrument support overnight trading or not",
                  "example": false
                },
                "margin_requirement_long": {
                  "type": "string",
                  "description": "Margin requirement ratio for long position",
                  "example": "0.5"
                },
                "margin_requirement_short": {
                  "type": "string",
                  "description": "Margin requirement ratio for short position",
                  "example": "0.5"
                },
                "easy_to_borrow": {
                  "type": "boolean",
                  "description": "Instrument is easy to borrow or not",
                  "example": false
                },
                "lot_size": {
                  "type": "string",
                  "description": "Lot size",
                  "example": "1.0"
                },
                "currency": {
                  "type": "string",
                  "description": "Currency",
                  "example": "USD"
                }
              },
              "description": "Instrument Information",
              "title": "InstrumentStockDetailVO"
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
    "name": "Get Stock Instrument",
    "description": {
      "content": "Get profile information for one or more instruments. Rate limit 60 requests every 60 seconds",
      "type": "text/plain"
    },
    "url": {
      "path": [
        "openapi",
        "instrument",
        "stock",
        "list"
      ],
      "host": [
        "{{baseUrl}}"
      ],
      "query": [
        {
          "disabled": false,
          "description": {
            "content": "List of security symbols, maximum 100 symbols per query.",
            "type": "text/plain"
          },
          "key": "symbols",
          "value": ""
        },
        {
          "disabled": false,
          "description": {
            "content": "(Required) Security type.",
            "type": "text/plain"
          },
          "key": "category",
          "value": ""
        },
        {
          "disabled": false,
          "description": {
            "content": "Tradable status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable)",
            "type": "text/plain"
          },
          "key": "status",
          "value": ""
        },
        {
          "disabled": false,
          "description": {
            "content": "Last instrument id for pagination",
            "type": "text/plain"
          },
          "key": "last_instrument_id",
          "value": ""
        },
        {
          "disabled": false,
          "description": {
            "content": "Page size, default 1000",
            "type": "text/plain"
          },
          "key": "page_size",
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
| symbols | string | No | List of security symbols, maximum 100 symbols per query. Example: `AAPL,TSLA` |
| category | string | Yes | Security type. Enum: `US_STOCK`, `US_ETF`, `HK_STOCK`, `CN_STOCK` |
| status | string | No | Tradable status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable) |
| last_instrument_id | string | No | Last instrument id for pagination |
| page_size | integer | No | Page size, default 1000 |

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

Returns an array of instrument objects:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| name | string | Symbol name | APPLE INC |
| instrument_id | string | Unique identifier of the security | 10152734329 |
| exchange_code | string | Exchange code | NSQ |
| category | string | Instrument type | US_STOCK |
| symbol | string | Symbol of the instrument | AAPL |
| status | string | Tradable status | OC |
| shortable | boolean | Instrument is shortable or not | false |
| fractionable | boolean | Instrument is fractionable or not | false |
| marginable | boolean | Instrument is marginable or not | false |
| overnight_trading_supported | boolean | Instrument support overnight trading or not | false |
| margin_requirement_long | string | Margin requirement ratio for long position | 0.5 |
| margin_requirement_short | string | Margin requirement ratio for short position | 0.5 |
| easy_to_borrow | boolean | Instrument is easy to borrow or not | false |
| lot_size | string | Lot size | 1.0 |
| currency | string | Currency | USD |

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized: Authentication required |
| 417 | Business logic error (invalid parameters, etc.) |
| 500 | Internal Server Error |
