---
title: Check Token
method: POST
endpoint: /openapi/auth/token/check
rate_limit: 10 requests every 30 seconds
source: https://developer.webull.hk/apis/docs/reference/check-token
updated: 2026-05-17
tags: [webull, api-reference, auth]
---

# Check Token

• Function description: Query Token Status.This API is used to check the validity of a given token. If the status is NORMAL, the token is active and can be used normally. If the status is PENDING, the token is pending verification and requires a mobile verification code via the Webull App. If the status is INVALID, the token is invalid and must be regenerated. If the status is EXPIRED, the token has expired and must be regenerated.

• Frequency limit: Rate limit 10 requests every 30 seconds

# OpenAPI definition

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
  "path": "/openapi/auth/token/check",
  "method": "post",
  "tags": [
    "Server-To-Server"
  ],
  "description": "• Function description: Query Token Status.This API is used to check the validity of a given token. If the status is NORMAL, the token is active and can be used normally. If the status is PENDING, the token is pending verification and requires a mobile verification code via the Webull App. If the status is INVALID, the token is invalid and must be regenerated. If the status is EXPIRED, the token has expired and must be regenerated.  \n• Frequency limit: Rate limit 10 requests every 30 seconds",
  "operationId": "checkToken",
  "parameters": [
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
  "requestBody": {
    "content": {
      "application/json": {
        "schema": {
          "required": [
            "token"
          ],
          "type": "object",
          "properties": {
            "token": {
              "type": "string",
              "description": "Access token, used for identity authentication and permission verification. This field is a unique identifier for token checking, refreshing, etc.",
              "example": "ccb071f764864b65a1fb48484e940a56"
            }
          },
          "description": "Token request parameters",
          "title": "TokenReq"
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
            "required": [
              "expires",
              "status",
              "token"
            ],
            "type": "object",
            "properties": {
              "token": {
                "type": "string",
                "description": "Access token string, used for authentication of subsequent API calls. Token is a 32-digit hexadecimal string that is unique and time-sensitive.",
                "example": "ccb071f764864b65a1fb48484e940a56"
              },
              "expires": {
                "type": "integer",
                "description": "Token expiration timestamp, a Unix timestamp in milliseconds. After this time, the token will become invalid and need to be recreated.",
                "format": "int64",
                "example": 1755486723000
              },
              "status": {
                "type": "string",
                "description": "Token validity status code, indicating the result of the token operation. PENDING indicates pending verification, NORMAL indicates valid, INVALID indicates the token is invalid, and EXPIRED indicates it has expired.",
                "example": "PENDING",
                "enum": [
                  "PENDING",
                  "NORMAL",
                  "INVALID",
                  "EXPIRED"
                ]
              }
            },
            "description": "Token response information",
            "title": "TokenRespVo"
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
  "jsonRequestBodyExample": {
    "token": "ccb071f764864b65a1fb48484e940a56"
  },
  "postman": {
    "name": "Check Token",
    "description": {
      "content": "• Function description: Query Token Status.This API is used to check the validity of a given token. If the status is NORMAL, the token is active and can be used normally. If the status is PENDING, the token is pending verification and requires a mobile verification code via the Webull App. If the status is INVALID, the token is invalid and must be regenerated. If the status is EXPIRED, the token has expired and must be regenerated.  \n• Frequency limit: Rate limit 10 requests every 30 seconds",
      "type": "text/plain"
    },
    "url": {
      "path": [
        "openapi",
        "auth",
        "token",
        "check"
      ],
      "host": [
        "{{baseUrl}}"
      ],
      "query": [],
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
        "key": "Content-Type",
        "value": "application/json"
      },
      {
        "key": "Accept",
        "value": "application/json"
      }
    ],
    "method": "POST",
    "body": {
      "mode": "raw",
      "raw": "",
      "options": {
        "raw": {
          "language": "json"
        }
      }
    }
  }
}
```
