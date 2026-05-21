---
title: "Get Stock Locate Detail"
method: "GET"
endpoint: "/openapi/broker/instrument/locate/detail"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-stock-locate-detail"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Get Stock Locate Detail

**Method:** `GET`  
**Endpoint:** `/openapi/broker/instrument/locate/detail`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-stock-locate-detail](https://developer.webull.hk/apis/docs/reference/broker-api/broker-stock-locate-detail)

Broker APIInstrumentGet Stock Locate Detail
Get Stock Locate Detail
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/instrument/locate/detail

• Function description: Get stock short trading related information, includes: stock borrow type (ETB/HTB), available short quantity, short interest rate, etc. (Reference use only).

Request​
QUERY PARAMETERS
symbols
string
REQUIRED

List of security symbols, maximum 100 symbols per query.

Example: AAPL,TSLA
category
string
REQUIRED

Possible values: [US_STOCK]

Security type.

Example: US_STOCK
HEADER PARAMETERS
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
symbol
string

Symbol of the instrument

Example: AAPL
shortable
string

Whether the security is shortable: Y = Yes, N = No

Example: Y
short_type
string

Short availability type: ETB (Easy To Borrow), HTB (Hard To Borrow)

Example: ETB
available_num
int32

remaining available shares for short selling (not returned for ETB)

Example: 1000
short_interest_rate
double

Annualized short interest rate

Example: 5.5
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

	  'x-timestamp': '2026-05-17T14:38:02Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '64339222133288268601662604',

	  'x-version': 'v2',

	  'x-signature': '52929609749249445620839258'

	}

	conn.request("GET", "/openapi/broker/instrument/locate/detail?symbols=AAPL,TSLA", payload, headers)

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
symbols — queryREQUIRED
category — queryREQUIRED
---
US_STOCK
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
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/instrument/locate/detail
```

```json
[  {    "symbol": "AAPL",    "shortable": "Y",    "short_type": "ETB",    "available_num": 1000,    "short_interest_rate": 5.5  }]
```

```json
[  {    "symbol": "AAPL",    "shortable": "Y",    "short_type": "ETB",    "available_num": 1000,    "short_interest_rate": 5.5  }]
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:02Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '64339222133288268601662604',  'x-version': 'v2',  'x-signature': '52929609749249445620839258'}conn.request("GET", "/openapi/broker/instrument/locate/detail?symbols=AAPL,TSLA", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:02Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '64339222133288268601662604',  'x-version': 'v2',  'x-signature': '52929609749249445620839258'}conn.request("GET", "/openapi/broker/instrument/locate/detail?symbols=AAPL,TSLA", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-stock-locate-detail](https://developer.webull.hk/apis/docs/reference/broker-api/broker-stock-locate-detail)
