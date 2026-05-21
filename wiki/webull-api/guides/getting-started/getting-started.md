---
title: Getting Started
source: https://developer.webull.hk/apis/docs/getting-started
updated: 2026-05-17
tags:
  - webull
  - guide
---

> This guide uses the Trading API as an example to help you get started quickly.

This page walks you through the complete path from zero to your first successful API call. Each step links to the relevant page for details — follow them in order and you'll be up and running quickly.

## Step 1: Apply for API Access

Before you can use the Webull OpenAPI, you need to apply for access and get your credentials approved.

- Apply through the Webull website. See Trading API Application.

> **Caution:** The review process typically takes 1–2 business days. You can proceed to Step 2 while waiting.

## Step 2: Install the SDK

Install the official Webull SDK for your language. The SDK handles authentication, signature generation, and protocol details automatically.

| Language | Install Command |
| --- | --- |
| Python | `pip3 install --upgrade webull-openapi-python-sdk` |
| Java | Add `webull-openapi-java-sdk` to your Maven dependencies |

For full installation details and environment setup, see SDKs and Tools.

## Step 3: Get Your Credentials

Once your application is approved, generate your App Key and App Secret from the Webull website or Portal.

Want to start coding right away? Use the shared test accounts — no application needed for the sandbox environment.

## Step 4: Make Your First API Call

With the SDK installed and credentials ready, you can make your first call. Here's a quick example using the sandbox environment:

**Python:**

```python
from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient

api_client = ApiClient("<your_app_key>", "<your_app_secret>", "hk")
api_client.add_endpoint("hk", "api.sandbox.webull.hk")

trade_client = TradeClient(api_client)
res = trade_client.get_account_list()
print(res.json())
```

If you see your account list returned, you're all set.

### API Endpoints

- Production: `api.webull.hk`
- Sandbox: `api.sandbox.webull.hk`

## Step 5: Explore the APIs

Now that you're connected, dive into the API that fits your use case:

| API | Best For | Guide |
| --- | --- | --- |
| Trading API | Placing orders, managing positions and accounts | Trading API Getting Started |
| Market Data API | Real-time and historical market data | Market Data API Getting Started |

## Learn More

- Authentication Overview — How request signing and token-based 2FA work
- SDKs and Tools — API environments, test accounts, and management tools
- Additional Resources — SDK source code, support channels, and learning materials
