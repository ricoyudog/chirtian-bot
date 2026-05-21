---
title: News Summary
method: POST (SSE stream)
endpoint: Not specified
rate_limit: 10 call/min per user
source: https://developer.webull.hk/apis/docs/reference/market-display-solution-data-api/watchlist-summary-using-post
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - display-solution
---

# News Summary

```
POST (SSE stream)

## /openapi/news/watchlist-summary
```

Invoke LLM to generate news summaries for watchlist. Server-Sent Events stream. Each message contains JSON data.

- Frequency limit: 10 call/min per user

## Response Types

- `text`: Markdown text
- `table`: `{ headers: {text: '<Title>'}[], rows: {text: 'Row Text'}[][] }`

## Request

## Responses

- 200 OK
