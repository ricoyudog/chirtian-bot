---
title: Signature
source: https://developer.webull.hk/apis/docs/authentication/signature
updated: 2026-05-17
tags:
  - webull
  - guide
  - authentication
---

Every API request to Webull must include a cryptographic signature in the request header. The signature is computed from the request content and your App Secret, ensuring the integrity and authenticity of each request.

```
x-signature: <signature_value>
```

> **SDK Users:** The Webull SDK handles signature generation automatically. If you're using the SDK, you can skip this page -- it's here for those implementing signature logic manually.

Every API request must include the following headers:

| Header | Required | Description |
| --- | --- | --- |
| `x-app-key` | Yes | A unique identifier issued to a developer for accessing the API |
| `x-timestamp` | Yes | Request timestamp in ISO 8601 format: `YYYY-MM-DDThh:mm:ssZ` (UTC only) |
| `x-signature` | Yes | The computed signature value (output of the algorithm described below) |
| `x-signature-algorithm` | Yes | Signature algorithm (e.g. `HMAC-SHA1`) |
| `x-signature-version` | Yes | Signature algorithm version (e.g. `1.0`) |
| `x-signature-nonce` | Yes | Unique random string, regenerated for each request |
| `x-version` | Yes | Interface version (accepts `v2`) |

> **About App Secret:** The `app_secret` is a unique key issued to developers. It is **not** included in any HTTP request header -- it is used solely on the client side for signature generation. See Step 2: Construct the Key for details.

## What Gets Signed

The signature is computed from four parts of the HTTP request:

1. Request path
2. Query parameters
3. Request body
4. Signing headers -- the following headers participate in signature computation:
   - `x-app-key`
   - `x-signature-algorithm`
   - `x-signature-version`
   - `x-signature-nonce`
   - `x-timestamp`
   - `host`

> **Note:** `x-signature` and `x-version` do **not** participate in signing. `x-signature` carries the output of the signature itself; `x-version` is a required request header but is excluded from the signature computation.

> **Important:**
> - The content being signed does **not** require URL Encoding at this stage.
> - For POST requests, `Content-Type` must be `application/json`.

## Signature Algorithm

### Step 1: Construct the Signature String

1. Merge all query parameters and the signing headers (listed in What Gets Signed) into a single list.
2. Sort all parameter names in ascending alphabetical order.
3. Join them as `name1=value1&name2=value2&...` -> this is **`str1`**.
4. If the request has a body, compute its MD5 hash and convert to uppercase: `toUpper(MD5(body))` -> this is **`str2`**.
5. Concatenate: **`str3`** = `path` + `&` + `str1` + `&` + `str2`
   - If the body is empty: **`str3`** = `path` + `&` + `str1`
6. URL-encode `str3` -> this is **`encoded_string`**.

> **Caution:**
> - There must be **no** extra spaces between body parameter keys and values.
> - If the body is empty, omit `str2` entirely.

### Step 2: Construct the Key

Append `&` to the end of your App Secret:

```
app_secret = "<your_app_secret>&"
```

### Step 3: Generate the Signature

```
signature = base64(HMAC-SHA1(app_secret, encoded_string))
```

## Worked Example

Below is a complete example showing each step of the signature generation process.

### Request Details

**Path:** `/trade/place_order`

**Query Parameters:**

| Name | Value |
| --- | --- |
| a1 | webull |
| a2 | 123 |
| a3 | xxx |
| q1 | yyy |

**Request Headers:**

| Name | Value |
| --- | --- |
| x-app-key | 776da210ab4a452795d74e726ebd74b6 |
| x-timestamp | 2022-01-04T03:55:31Z |
| x-signature-version | 1.0 |
| x-signature-algorithm | HMAC-SHA1 |
| x-signature-nonce | 48ef5afed43d4d91ae514aaeafbc29ba |
| host | api.webull.com |

**Body:**

```json
{"k1":123,"k2":"this is the api request body","k3":true,"k4":{"foo":[1,2]}}
```

**App Secret:** `0f50a2e853334a9aae1a783bee120c1f`

### Step 1: Construct the Signature String

1. Merge query parameters and signing headers into a single list, then sort all parameter names in ascending alphabetical order:

   ```
   a1=webull, a2=123, a3=xxx,
   host=api.webull.com,
   q1=yyy,
   x-app-key=776da210ab4a452795d74e726ebd74b6,
   x-signature-algorithm=HMAC-SHA1,
   x-signature-nonce=48ef5afed43d4d91ae514aaeafbc29ba,
   x-signature-version=1.0,
   x-timestamp=2022-01-04T03:55:31Z
   ```

2. Join them as `key=value` pairs with `&` -> **str1**:

   ```
   a1=webull&a2=123&a3=xxx&host=api.webull.com&q1=yyy&x-app-key=776da210ab4a452795d74e726ebd74b6&x-signature-algorithm=HMAC-SHA1&x-signature-nonce=48ef5afed43d4d91ae514aaeafbc29ba&x-signature-version=1.0&x-timestamp=2022-01-04T03:55:31Z
   ```

3. Compute MD5 of the body and convert to uppercase -> **str2**:

   ```
   E296C96787E1A309691CEF3692F5EEDD
   ```

4. Concatenate path + `&` + str1 + `&` + str2 -> **str3**:

   ```
   /trade/place_order&a1=webull&a2=123&a3=xxx&host=api.webull.com&q1=yyy&x-app-key=776da210ab4a452795d74e726ebd74b6&x-signature-algorithm=HMAC-SHA1&x-signature-nonce=48ef5afed43d4d91ae514aaeafbc29ba&x-signature-version=1.0&x-timestamp=2022-01-04T03:55:31Z&E296C96787E1A309691CEF3692F5EEDD
   ```

5. URL-encode str3 -> **encoded_string**:

   ```
   %2Ftrade%2Fplace_order%26a1%3Dwebull%26a2%3D123%26a3%3Dxxx%26host%3Dapi.webull.com%26q1%3Dyyy%26x-app-key%3D776da210ab4a452795d74e726ebd74b6%26x-signature-algorithm%3DHMAC-SHA1%26x-signature-nonce%3D48ef5afed43d4d91ae514aaeafbc29ba%26x-signature-version%3D1.0%26x-timestamp%3D2022-01-04T03%3A55%3A31Z%26E296C96787E1A309691CEF3692F5EEDD
   ```

### Step 2: Construct the Key

```
app_secret = "0f50a2e853334a9aae1a783bee120c1f&"
```

### Step 3: Generate the Signature

```
signature = base64(HMAC-SHA1(app_secret, encoded_string))
```

**Result:** `kvlS6opdZDhEBo5jq40nHYXaLvM=`

## Edge Cases

### Duplicate Parameter Names

If a request contains multiple parameters with the same name, sort all values in ascending order and join them with commas, then use the combined value in `str1`:

```
# URL: /path?name1=value1&name1=value2&name1=value3
# After sorting values in ascending order:
name1 = value1&value2&value3

# This combined value participates in str1 as:
# name1=value1&value2&value3
```

In other words, the duplicate keys are merged into a single `name1=...` entry in the sorted parameter list, with all values joined by `&`.

### JSON Body Serialization

When computing the MD5 hash of the request body, ensure the JSON string has **no extra spaces** between keys and values (use compact serialization like `separators=(',', ':')` in Python or equivalent in your language).

### Language-Specific HTML Escaping

Some languages automatically escape special characters in JSON output. You must reverse these escapes before computing the body MD5. For example:

**Go** -- `json.Marshal` escapes `<`, `>`, and `&` by default (`escapeHtml = true`):

```go
func unescapeJSON(data []byte) []byte {
    data = bytes.Replace(data, []byte("\\u0026"), []byte("&"), -1)
    data = bytes.Replace(data, []byte("\\u003c"), []byte("<"), -1)
    data = bytes.Replace(data, []byte("\\u003e"), []byte(">"), -1)
    return data
}
```

If your language or framework has similar behavior, ensure the raw JSON (without HTML escaping) is used for signature computation.

## Common Pitfalls

**Signature Debugging Tips**

If you receive an `INVALID_TOKEN` or `SIGNATURE_INVALID` error, check the following:

1. **Body serialization mismatch** -- The JSON body used for MD5 computation must be exactly the same string sent in the HTTP request body. If you use `json=body` in Python's `requests.post()`, the library serializes the body internally and may produce a different string than what you computed the MD5 from. Always serialize the body yourself (e.g., `json.dumps(body, separators=(',', ':'))`) and pass it as `data=body_string` with `Content-Type: application/json`.

2. **Compact JSON** -- Use compact serialization with no spaces (e.g., `separators=(',', ':')` in Python). Extra spaces will change the MD5 hash and invalidate the signature.
