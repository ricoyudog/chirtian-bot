---
title: "Trade Calendar"
method: "POST"
endpoint: "/openapi/broker/master-data/trade-calendar"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-trade-calendar"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Trade Calendar

**Method:** `POST`  
**Endpoint:** `/openapi/broker/master-data/trade-calendar`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-trade-calendar](https://developer.webull.hk/apis/docs/reference/broker-api/broker-trade-calendar)

Broker APIMaster DataQuery Trade Calendar
Query Trade Calendar
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/master-data/calendar

• Function description: Query trading & settlement calendar based on markets & product types.

Request​
QUERY PARAMETERS
market
string
REQUIRED

Possible values: [US, HK, CN]

Country code, US,HK,etc.

instrument_type
string
REQUIRED

Possible values: [EQUITY]

Type of financial instrument associated with the request.

year
String
REQUIRED

Query Year in YYYY format

Example: 2025
HEADER PARAMETERS
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
date
string
REQUIRED

Date string in YYYY-MM-DD format.

Example: 2025-01-06
settlement_date
string

Settlement Date string in YYYY-MM-DD format.

Example: 2025-01-08
is_trading_day
boolean
REQUIRED

Is Trading Day

Example: true
is_early_close
boolean

Whether it is a half-day trading session

Example: true
is_settlement_day
boolean
REQUIRED

Is Settlement Day

Example: true
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

	  'x-timestamp': '2026-05-17T14:39:32Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '34263597174166066341956207',

	  'x-version': 'v2',

	  'x-signature': '45029378581339110067358048'

	}

	conn.request("GET", "/openapi/broker/master-data/calendar?year=2025", payload, headers)

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
market — queryREQUIRED
---
US
HK
CN
instrument_type — queryREQUIRED
---
EQUITY
year — queryREQUIRED
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
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/master-data/calendar
```

```json
[  {    "date": "2025-01-06",    "settlement_date": "2025-01-08",    "is_trading_day": true,    "is_early_close": true,    "is_settlement_day": true  }]
```

```json
[  {    "date": "2025-01-06",    "settlement_date": "2025-01-08",    "is_trading_day": true,    "is_early_close": true,    "is_settlement_day": true  }]
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:39:32Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '34263597174166066341956207',  'x-version': 'v2',  'x-signature': '45029378581339110067358048'}conn.request("GET", "/openapi/broker/master-data/calendar?year=2025", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:39:32Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '34263597174166066341956207',  'x-version': 'v2',  'x-signature': '45029378581339110067358048'}conn.request("GET", "/openapi/broker/master-data/calendar?year=2025", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-trade-calendar](https://developer.webull.hk/apis/docs/reference/broker-api/broker-trade-calendar)
