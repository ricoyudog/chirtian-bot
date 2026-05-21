---
title: "Account Positions"
method: "GET"
endpoint: "/openapi/broker/assets/positions"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-positions"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Account Positions

**Method:** `GET`  
**Endpoint:** `/openapi/broker/assets/positions`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-positions](https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-positions)

Broker APIAssetsAccount Positions
Account Positions
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/assets/positions

• Function description: Get position details for a specific account.

Request​
QUERY PARAMETERS
account_id
String
REQUIRED

Account identifier.

Example: LOJOQITOD49R6G9BPQM489CISA
HEADER PARAMETERS
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
position_id
string
REQUIRED

Position ID

Example: N4I4SIM8TJF38KN2TAA0QVVNE9
currency
string
REQUIRED

Currency

Possible values: [CNH, HKD, USD]

Example: USD
quantity
string
REQUIRED

Quantity of the order. Specifies the number of shares or units to transact.
For US stocks, fractional quantities are allowed and can include decimals.

Example: 1
symbol
string
REQUIRED

Trading symbol of the financial instrument.Represents the unique identifier of the security in the specified market (e.g., ticker symbol for equities or option symbol code for derivatives).

Example: AAPL
instrument_type
string
REQUIRED

Type of financial instrument associated with the request.

Possible values: [EQUITY]

Example: EQUITY
last_price
string
REQUIRED

Last Price

Example: 10.0
cost_price
string
REQUIRED

Cost Basis

Example: 11.12
unrealized_profit_loss
string
REQUIRED

Open P&L

Example: 0.08
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

	  'x-timestamp': '2026-05-17T14:38:15Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '08912159225821070553882395',

	  'x-version': 'v2',

	  'x-signature': '66684706226921325268655437'

	}

	conn.request("GET", "/openapi/broker/assets/positions?account_id=LOJOQITOD49R6G9BPQM489CISA", payload, headers)

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
account_id — queryREQUIRED
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
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/assets/positions
```

```json
[  {    "position_id": "N4I4SIM8TJF38KN2TAA0QVVNE9",    "currency": "USD",    "quantity": "1",    "symbol": "AAPL",    "instrument_type": "EQUITY",    "last_price": "10.0",    "cost_price": "11.12",    "unrealized_profit_loss": "0.08"  }]
```

```json
[  {    "position_id": "N4I4SIM8TJF38KN2TAA0QVVNE9",    "currency": "USD",    "quantity": "1",    "symbol": "AAPL",    "instrument_type": "EQUITY",    "last_price": "10.0",    "cost_price": "11.12",    "unrealized_profit_loss": "0.08"  }]
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:15Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '08912159225821070553882395',  'x-version': 'v2',  'x-signature': '66684706226921325268655437'}conn.request("GET", "/openapi/broker/assets/positions?account_id=LOJOQITOD49R6G9BPQM489CISA", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:15Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '08912159225821070553882395',  'x-version': 'v2',  'x-signature': '66684706226921325268655437'}conn.request("GET", "/openapi/broker/assets/positions?account_id=LOJOQITOD49R6G9BPQM489CISA", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-positions](https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-positions)
