---
title: General FAQ
source: https://developer.webull.hk/apis/docs/faq
updated: 2026-05-17
tags:
  - webull
  - guide
---

General questions about the Webull OpenAPI platform. For topic-specific questions, see Market Data API FAQ and Trading API FAQ.

### 1. How long does API application approval take?

API applications are typically reviewed within 1-2 business days. While waiting, you can install the SDK and start developing against the test environment immediately.

### 2. What can I build with the Webull OpenAPI?

Common use cases include:

- Automated trading strategies (e.g., algorithmic or quantitative trading)
- Custom trading dashboards and monitoring tools
- Market data analysis and backtesting pipelines

### 3. What programming languages are supported?

Webull provides official SDKs for Python (3.8-3.13) and Java (JDK 8+). If you're using another language, you can integrate directly via the REST API (HTTP), MQTT (market data streaming), and gRPC (order event streaming). See SDKs and Tools for details.

### 4. Can the market data I subscribed to in QT or the mobile app be used with OpenAPI?

No. Subscriptions in QT or the mobile app are independent of OpenAPI. You need a separate data subscription specifically enabled for OpenAPI usage. See Subscribe Advanced Quotes for details.

### 5. Why does the SDK enter a verification loop on first startup?

```
fetch_token_from_server status not verified, check_token loop will start, waiting 5 seconds... (elapsed 131s / 300s)
```

This means the SDK is waiting for you to complete the one-time token verification via the Webull App. The SDK polls every 5 seconds for up to 300 seconds. Open the Webull App and approve the verification request. If the 300-second window expires, restart the application to re-trigger the process. See Token Verification for the full flow.

### 6. Why do I need an App Key and App Secret?

The App Key and App Secret are your application-level credentials. Every API request is signed using these credentials to verify your identity. The SDK handles signature generation automatically -- you just need to provide them during initialization.

### 7. What is an IP whitelist and do I need one?

IP whitelisting is a security feature available to institutional clients. It restricts API access to specific IP addresses. Institutional clients can configure their whitelist in the Webull Portal under API Application Management. Individual developers do not need to set up an IP whitelist.

### 8. Can I trade A-shares via OpenAPI?

Only certain A-shares can be traded via Stock Connect. For details, see the Stock Connect Eligible List.

> **Note:** The A-Share Connect trading function is disabled by default. If you wish to enable it, please contact Customer Service at (852) 3852 8500. Currently, Webull OpenAPI does not support A-share trading for Mainland China clients.

### 9. Are there any additional fees for using the OpenAPI?

No. There are no extra charges for accessing the API. Trading fees are the same as those in the Webull App. Market data subscriptions for OpenAPI are purchased separately -- see Subscribe Advanced Quotes. For the full fee schedule, see Webull HK Pricing.

### 10. Where can I get help if I run into issues?

- Check the topic-specific FAQs: Market Data FAQ, Trading FAQ
- Review the Additional Resources page for support channels and learning materials
- Contact Customer Service at (852) 3852 8500
