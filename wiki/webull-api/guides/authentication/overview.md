---
title: Authentication Overview
source: https://developer.webull.hk/apis/docs/authentication/overview
updated: 2026-05-17
tags:
  - webull
  - guide
  - authentication
---

Webull OpenAPI uses a signature-based authentication mechanism to ensure the security of every API call. This page explains the authentication model and how the components work together.

## How It Works

Every API request to Webull must include two things:

1. **Signature** -- A cryptographic signature (e.g. HMAC-SHA1) computed from the request content and your App Secret. This proves the request is authentic and hasn't been tampered with.
2. **Token** -- In accordance with Hong Kong security and compliance requirements, OpenAPI also requires Token authentication. A reusable access token verified via the Webull App is required for trading and account operations.

All API requests must be made over HTTPS. Calls made over HTTP will fail. Unauthenticated requests will also fail.

## Authentication Flow

| Step | Action | Details |
| --- | --- | --- |
| 1 | Obtain API credentials | Apply for API access and generate your App Key and App Secret |
| 2 | Sign each request | Compute a cryptographic signature from the request content using your App Secret. The SDK handles this automatically. |
| 3 | Create a Token | The SDK initiates Token creation automatically; you only need to complete verification in the Webull App |
| 4 | Include credentials in headers | Add `x-app-key`, `x-signature`, and `x-access-token` to every request |

### Required Headers

| Header | Required | Description |
| --- | --- | --- |
| `x-app-key` | Yes | A unique identifier issued to a developer for accessing the API |
| `x-timestamp` | Yes | Request timestamp in ISO 8601 format: `YYYY-MM-DDThh:mm:ssZ` (UTC only) |
| `x-signature` | Yes | Cryptographic signature verifying the authenticity and integrity of the request |
| `x-signature-algorithm` | Yes | Signature algorithm (e.g. `HMAC-SHA1`) |
| `x-signature-version` | Yes | Signature algorithm version (e.g. `1.0`) |
| `x-signature-nonce` | Yes | Unique random string, regenerated for each request |
| `x-version` | Yes | Interface version (accepts `v2`) |

> **About App Secret:** The `app_secret` is used solely on the client side for signature generation. It is **not** included as an HTTP request header.

> **SDK Users:** The Webull SDK handles both signature generation and Token creation/verification automatically. You only need to configure your App Key and App Secret -- the SDK takes care of the rest, including the 2FA flow.

## Managing Your Credentials

You can view and manage your App Key and App Secret on the Webull Official Website under **OpenAPI Management > App Management**.

> **Security Warning:** Your App Key and App Secret contain important access permissions. **Never** expose them in public places such as GitHub repositories, client-side code, or forums.

## Next Steps

- Trading API Application -- How to apply for Trading API access and generate credentials
- Broker API Application -- How to apply for Broker API access
- Signature -- Detailed signature generation algorithm and examples
- Token -- Token creation, verification, and lifecycle management
