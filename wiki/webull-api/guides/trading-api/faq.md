---
title: Trading API FAQ
source: https://developer.webull.hk/apis/docs/trade-api/faq
updated: 2026-05-17
tags: [webull, guide, trading, faq]
---

# Trading API FAQ

### 1. Why am I receiving an HTTP 403 error (Forbidden)?

A 403 error is returned when:

- The request is missing authentication headers
- The authentication credentials are invalid
- Your account does not have sufficient permissions

Make sure your request includes all required headers. See Authentication Overview for details.

### 2. Do I need to handle signatures when using the Webull SDK?

No. The SDK handles signature generation automatically. You only need to provide your App Key and App Secret when initializing the client.

### 3. How long does API application approval take?

The review and approval process typically takes 1-2 business days. You can install the SDK and explore the sandbox environment while waiting. See Getting Started for details.

### 4. What order types are supported?

Supported order types vary by market. US stocks support Market, Limit, Stop Loss, Stop Loss Limit, Market on Open/Close. HK stocks support Enhanced Limit, At-Auction, At-Auction Limit, Stop Loss, Stop Loss Limit, Trailing Stop Loss, Trailing Stop Loss Limit, Touch Market, and Touch Limit. A-shares support Limit orders only.

For the full order type comparison by market, see Trading API Overview -- Feature Matrix.

### 5. Why was my order rejected?

Common reasons:

- Insufficient buying power or margin
- The market is closed for the asset you're trading
- Invalid order parameters (e.g., price outside allowed range, unsupported order type)
- Token not in `NORMAL` status

Check the error message in the API response for specific details.

### 6. Can I modify a partially filled order?

Yes. Use the Order Replace endpoint to change the price or quantity. Only the unfilled portion is affected. If the order has been fully filled or cancelled, the replace request will be rejected.

### 7. How do I receive real-time order status updates?

Use the Trade Event Subscription via gRPC streaming. It pushes updates for fills, cancellations, modifications, and failures in real time. See Getting Started for a code example.

### 8. Are there different rate limits for different markets?

Yes. HK and A-share order operations have stricter rate limits:

| Operation | US Market | HK / A-Share Market |
| --- | --- | --- |
| Place / Replace / Cancel | 15 req/s | 1 req/s |

### 9. A-Share Trading Considerations

- Only Stock Connect eligible stocks can be traded
- T+1 settlement -- shares purchased today cannot be sold until the next trading day
- No short selling
- Trading hours follow China Mainland sessions (09:30-11:30, 13:00-15:00 CST)

### 10. How do I test trading without real money?

Use the sandbox environment (`api.sandbox.webull.hk`). Orders are simulated and do not execute on real markets. Tokens are set to `NORMAL` by default -- no 2FA needed. See SDKs and Tools for test account credentials.

### 11. Are there any fees for using the Trading API?

There are no additional charges for trading via the OpenAPI. Trading fees are the same as those in the Webull App. Use the Order Preview endpoint to estimate fees before placing.
