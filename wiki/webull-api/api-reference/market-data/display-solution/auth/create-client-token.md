---
title: Create Client Token
method: POST
endpoint: /openapi/auth/client/token/create
rate_limit: 600 requests per minute
source: https://developer.webull.hk/apis/docs/reference/market-display-solution-data-api/create-client-token
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - display-solution
---

# Create Client Token

```
POST

## /openapi/auth/client/token/create
```

Generates an access token and refresh token pair for end-user applications to directly access Webull services. This endpoint must be called from your institution's backend service with valid AK/SK credentials. The access token authorizes API calls, while the refresh token enables token renewal. Creating a new token pair for an existing customer immediately invalidates any previously issued tokens for that customer.

- Access token expires in approximately 2 hours (may vary slightly)
- Refresh token expires in 15 days
- Frequency limit: Rate limit 600 requests per minute
- **Note**: This access_token is used to access Market Data API

## Request

## Responses

- 200 OK
