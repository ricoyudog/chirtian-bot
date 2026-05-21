---
title: About Webull OpenAPI
source: https://developer.webull.hk/apis/docs/about-open-api
updated: 2026-05-17
tags:
  - webull
  - guide
---

## Overview

Webull OpenAPI is designed to provide convenient, fast, and secure quantitative trading services. It helps investors implement flexible and diverse trading or market data strategies through programmatic access to Hong Kong, US, and China Mainland markets.

## Interface Protocols

| Protocol | Description |
| --- | --- |
| HTTP | Trading operations, account management, and historical/snapshot market data queries |
| MQTT | Real-time market data streaming via WebSocket/TCP |
| gRPC | Real-time event push notifications (e.g., order status changes) |

## Supported Markets and Products

| Market | Trading Products | Market Data Coverage |
| --- | --- | --- |
| Hong Kong | Stocks, ETFs, Warrants, CBBCs | HK Stocks (HKEX) |
| United States | Stocks, Options (excluding Index Options) | US Stocks (NYSE, NASDAQ), Overnight Session |
| China Mainland | A-Shares (via Stock Connect) | A-Shares |

## Authentication

Webull OpenAPI uses a dual-layer security mechanism:

- **Signature** — Every API request includes an HMAC-SHA1 signature computed from your App Key and App Secret. The SDK handles this automatically.
- **Token** — A reusable access token verified via the Webull App for trading and account operations.

All API requests must be made over HTTPS. For details, see Authentication Overview.

## Official SDKs

To simplify integration, Webull provides official SDKs with built-in authentication and protocol handling:

| Language | Requirement |
| --- | --- |
| Python | Version 3.8–3.13 |
| Java | JDK 8+ (Maven) |

For installation instructions and code examples, see SDKs and Tools.

## AI-Assisted Development

Our documentation is published in machine-readable formats, making it easy to use with AI coding assistants like Cursor, Kiro, and other LLM-powered tools. Feed the Webull API reference directly into your AI workflow to generate integration code, debug issues, and explore endpoints faster.
