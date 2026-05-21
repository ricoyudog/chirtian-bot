---
title: "Get FX Rate"
method: "GET"
endpoint: "/openapi/broker/funding/fx/rate"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-funding-query-rate"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Get FX Rate

**Method:** `GET`  
**Endpoint:** `/openapi/broker/funding/fx/rate`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-funding-query-rate](https://developer.webull.hk/apis/docs/reference/broker-api/broker-funding-query-rate)

Broker APIFundingFXGet FX Rate
Get FX Rate
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/funding/fx/query_rate

• Function description: Get currency exchange rate based on currency pair.

Request​
QUERY PARAMETERS
from_currency
string
REQUIRED

Possible values: [CNH, HKD, USD]

Which currency you use for exchange.

to_currency
string
REQUIRED

Possible values: [CNH, HKD, USD]

Target currency you plan to get for exchange.

HEADER PARAMETERS
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
from_currency
string
REQUIRED

Currency

Possible values: [CNH, HKD, USD]

Example: HKD
to_currency
string
REQUIRED

Currency

Possible values: [CNH, HKD, USD]

Example: USD
fx_rate
string
REQUIRED

FX rate

Example: 8.01
rate_effective_time
string
REQUIRED

Effective time of the FX rate (ISO 8601 format, UTC time zone).

Example: 2025-11-11T05:44:35.385Z
rate_expire_time
string
REQUIRED

Expiration time of the FX rate (ISO 8601 format, UTC time zone).

Example: 2025-11-11T05:44:35.385Z
PYTHON
CURL
CSHARP
GO
NODEJS
RUBY
PHP
JAVA
POWERSHELL
DART
JAVASCRIPT
C
OBJECTIVE-C
OCAML
R
SWIFT
KOTLIN
RUST
HTTP.CLIENT
REQUESTS
	import http.client

	

	conn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")

	payload = ''

	headers = {

	  'Accept': 'application/json',

	  'x-timestamp': '2026-05-17T14:38:45Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '03474331188222897121228584',

	  'x-version': 'v2',

	  'x-signature': '47415391931651286847608717'

	}

	conn.request("GET", "/openapi/broker/funding/fx/query_rate", payload, headers)

	res = conn.getresponse()

	data = res.read()

	print(data.decode("utf-8"))

REQUEST
COLLAPSE ALL
Base URL
https://hk-broker-api.uat.webullbroker.com
Parameters
Individual users, please click here to obtain the sandbox key:Get Key for Individuals
Institutional users, please click here to obtain the sandbox key:Get Key for Institutions
from_currency — queryREQUIRED
---
CNH
HKD
USD
to_currency — queryREQUIRED
---
CNH
HKD
USD
x-app-key — headerREQUIRED
x-app-secret — headerREQUIRED
x-timestamp — headerREQUIRED
x-signature-version — headerREQUIRED
x-signature-algorithm — headerREQUIRED
x-signature-nonce — headerREQUIRED
x-version — headerREQUIRED
x-signature — headerREQUIRED
SEND API REQUEST
RESPONSE
CLEAR

Click the Send API Request button above and see the response here!

## Code Examples

```
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/funding/fx/query_rate
```

```json
{  "from_currency": "HKD",  "to_currency": "USD",  "fx_rate": "8.01",  "rate_effective_time": "2025-11-11T05:44:35.385Z",  "rate_expire_time": "2025-11-11T05:44:35.385Z"}
```

```json
{  "from_currency": "HKD",  "to_currency": "USD",  "fx_rate": "8.01",  "rate_effective_time": "2025-11-11T05:44:35.385Z",  "rate_expire_time": "2025-11-11T05:44:35.385Z"}
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:45Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '03474331188222897121228584',  'x-version': 'v2',  'x-signature': '47415391931651286847608717'}conn.request("GET", "/openapi/broker/funding/fx/query_rate", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:45Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '03474331188222897121228584',  'x-version': 'v2',  'x-signature': '47415391931651286847608717'}conn.request("GET", "/openapi/broker/funding/fx/query_rate", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-funding-query-rate](https://developer.webull.hk/apis/docs/reference/broker-api/broker-funding-query-rate)
