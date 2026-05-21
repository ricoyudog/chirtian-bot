---
title: Refresh Client Token
method: POST
endpoint: /openapi/auth/client/token/refresh
rate_limit: 600 requests per minute
source: https://developer.webull.hk/apis/docs/reference/market-display-solution-data-api/refresh-client-token
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - display-solution
---

# Refresh Client Token

```
POST

## /openapi/auth/client/token/refresh
```

Obtains a new access token and refresh token pair using a valid refresh token. This endpoint requires AK/SK signature authentication from your institution's backend service. Both the refresh token and request signature are validated before issuing new credentials. The old tokens will be invalidated after successful refresh.

- Access token expires in approximately 2 hours (may vary slightly)
- Refresh token expires in 15 days
- Frequency limit: Rate limit 600 requests per minute
- **Note**: This access_token is used to access Market Data API

## Request

## Responses

- 200 OK
