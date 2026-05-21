---
title: Token
source: https://developer.webull.hk/apis/docs/authentication/token
updated: 2026-05-17
tags:
  - webull
  - guide
  - authentication
---

To comply with Hong Kong regulatory standards and protect account security, a Token is required for all API authentication. The Token serves as an additional layer of security beyond the request signature.

## Token Creation Flow

Call the Create Token API to generate a new Token. The response returns a Token with status `PENDING`, and an SMS verification code is sent to the phone number bound to your account.

> **SDK Users:** If you're using the SDK, this step happens automatically when you make your first API call. Your program will loop and wait for verification.

## Token Verification

Open the Webull App and enter the SMS verification code to activate the Token. Once verified, the Token status changes to `NORMAL`.

The verification prompt appears automatically if the app is running with push notifications enabled.

## Token Reuse

A valid Token can be reused across multiple API calls. To avoid creating a new Token every time, store it securely and reuse it until it becomes invalid or expired.

## Using the Token in Requests

Include the Token in the `x-access-token` header with every API request:

```python
headers = {
    'x-app-key': '<your_app_key>',
    'x-timestamp': '2025-11-13T01:37:20Z',
    'x-signature-version': '1.0',
    'x-signature-algorithm': 'HMAC-SHA1',
    'x-signature-nonce': '<unique_nonce>',
    'x-version': 'v2',
    'x-signature': '<computed_signature>',
    'x-access-token': '<your_active_token>',
}
```
