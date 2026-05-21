---
title: Market Data API FAQ
source: https://developer.webull.hk/apis/docs/market-data-api/faq
updated: 2026-05-17
tags: [webull, guide, market-data, faq]
---

# Market Data API FAQ

### 1. Why am I receiving an HTTP 403 error (Forbidden)?

A 403 error is returned when:

- The request is missing authentication headers
- The authentication credentials are invalid
- Your account does not have sufficient permissions for the requested data

Make sure your request includes all required headers. See Authentication Overview for details.

### 2. Do I need to handle signatures when using the Webull SDK?

No. The SDK handles signature generation automatically. You only need to provide your App Key and App Secret when initializing the client.

### 3. How do I get market data permissions? Are subscriptions from the Webull App valid?

Subscriptions purchased through the Webull mobile app or desktop platform (QT) are independent of OpenAPI. You need a separate subscription specifically enabled for OpenAPI usage. See Subscribe Advanced Quotes for a step-by-step guide.

### 4. What is the rate limit for Market Data API?

The Data API (HTTP) has a rate limit of 600 requests per minute. The Data Streaming API (MQTT) does not have a rate limit for subscribe/unsubscribe operations. See Market Data API Overview for more details.

### 5. Why was my MQTT connection disconnected?

Common causes:

- You used the same `session_id` for multiple connections -- the new connection replaces the previous one
- You exceeded the maximum of 5 concurrent connections per App Key (error code `105`)
- Heartbeat timeout -- the server didn't receive a response in time

See Data Streaming API for connection rules and error codes.

### 6. Why am I not receiving data after reconnecting?

MQTT subscriptions are not automatically restored after a disconnection. You must call the Subscribe API again after reconnecting to resume data streaming.

### 7. Why are MQTT messages in binary format?

Streaming payloads are serialized using Protocol Buffers, not JSON. You need to parse them using the proto definitions provided in the Data Streaming API documentation. The only exception is the `notice` topic, which uses JSON.

### 8. Can I access LV1/LV2 data from multiple devices at the same time?

No. Only one device may access Level 1 and Level 2 market data at any given time per subscription.
