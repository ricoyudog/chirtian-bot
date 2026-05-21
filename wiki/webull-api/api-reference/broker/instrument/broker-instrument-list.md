---
title: "Get Stock Instrument"
method: "GET"
endpoint: "/openapi/broker/instrument/stock/list"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-instrument-list"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Get Stock Instrument

**Method:** `GET`  
**Endpoint:** `/openapi/broker/instrument/stock/list`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-instrument-list](https://developer.webull.hk/apis/docs/reference/broker-api/broker-instrument-list)

Broker APIInstrumentGet Stock Instrument
Get Stock Instrument
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/instrument/stock/list

• Function description: Get detail information of instruments associated to customer's account.

Request​
QUERY PARAMETERS
symbols
string

List of security symbols, maximum 100 symbols per query.

Example: AAPL,TSLA
category
string
REQUIRED

Possible values: [US_STOCK, HK_STOCK, CN_STOCK]

Security type.

Example: US_STOCK
status
string

Possible values: [OC, CO, NT]

Tradable status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable)

Example: CO
last_instrument_id
string

Last instrument id for pagination

Example: 951007842
page_size
int32

Number of records to return per page. Default is 1000. Supports integers in [1-10000].

Example: 1000
HEADER PARAMETERS
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
name
string

Symbol name, e.g. Apple

Example: APPLE INC
instrument_id
string

Unique identifier of the security

Example: 10152734329
exchange_code
string

Exchange code, e.g. CCC

Example: NSQ
category
string

Instrument Stock Category
US_STOCK - US stock,
HK_STOCK - HK stock,
CN_STOCK - China A share


Possible values: [US_STOCK, HK_STOCK, CN_STOCK]

Example: US_STOCK
symbol
string

Symbol of the instrument

Example: AAPL
status
string

Tradable Status
OC - Tradable: Security is available for trading
CO - Liquidate only: Security can only be sold, no purchases allowed
NT - Non-Tradable: Security cannot be traded

Possible values: [OC, CO, NT]

Example: OC
shortable
boolean

Instrument is shortable or not

Example: false
fractionable
boolean

Instrument is fractionable or not

Example: false
marginable
boolean

Instrument is marginable or not

Example: false
overnight_trading_supported
boolean

Instrument support overnight trading or not

Example: false
margin_requirement_long
string

Margin requirement ratio for long position

Example: 0.5
margin_requirement_short
string

Margin requirement ratio for short position

Example: 0.5
easy_to_borrow
boolean

Instrument is easy to borrow or not

Example: false
lot_size
string

Lot size

Example: 1.0
currency
string

currency

Example: USD
etf_leveraged_flag
string

Is Leveraged ETF. Allowed values: YES / NO. Null if not an ETF

Example: YES
etf_leveraged_factor
string

ETF Leveraged Factor. Numeric string, positive for bullish, negative for inverse. Null if not an ETF

Example: 2
inverse_etf
string

Is Inverse ETF. Allowed values: true / false. Null if not an ETF

Example: true
crypto_etf
string

Is Crypto ETF. Allowed values: true / false. Null if not an ETF

Example: true
single_stock_etf
string

Is Single Stock ETF. Allowed values: true / false. Null if not an ETF

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

	  'x-timestamp': '2026-05-17T14:37:57Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '88603761372859478065277798',

	  'x-version': 'v2',

	  'x-signature': '29114255044317305099982738'

	}

	conn.request("GET", "/openapi/broker/instrument/stock/list?symbols=AAPL,TSLA&last_instrument_id=951007842&page_size=1000", payload, headers)

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
category — queryREQUIRED
---
US_STOCK
HK_STOCK
CN_STOCK
x-app-key — headerREQUIRED
x-app-secret — headerREQUIRED
x-timestamp — headerREQUIRED
x-signature-version — headerREQUIRED
x-signature-algorithm — headerREQUIRED
x-signature-nonce — headerREQUIRED
x-version — headerREQUIRED
x-signature — headerREQUIRED
Show optional parameters
SEND API REQUEST
RESPONSE
CLEAR

Click the Send API Request button above and see the response here!

## Code Examples

```
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/instrument/stock/list
```

```json
[  {    "name": "APPLE INC",    "instrument_id": "10152734329",    "exchange_code": "NSQ",    "category": "US_STOCK",    "symbol": "AAPL",    "status": "OC",    "shortable": false,    "fractionable": false,    "marginable": false,    "overnight_trading_supported": false,    "margin_requirement_long": "0.5",    "margin_requirement_short": "0.5",    "easy_to_borrow": false,    "lot_size": "1.0",    "currency": "USD",    "etf_leveraged_flag": "YES",    "etf_leveraged_factor": "2",    "inverse_etf": "true",    "crypto_etf": "true",    "single_stock_etf": "true"  }]
```

```json
[  {    "name": "APPLE INC",    "instrument_id": "10152734329",    "exchange_code": "NSQ",    "category": "US_STOCK",    "symbol": "AAPL",    "status": "OC",    "shortable": false,    "fractionable": false,    "marginable": false,    "overnight_trading_supported": false,    "margin_requirement_long": "0.5",    "margin_requirement_short": "0.5",    "easy_to_borrow": false,    "lot_size": "1.0",    "currency": "USD",    "etf_leveraged_flag": "YES",    "etf_leveraged_factor": "2",    "inverse_etf": "true",    "crypto_etf": "true",    "single_stock_etf": "true"  }]
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:37:57Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '88603761372859478065277798',  'x-version': 'v2',  'x-signature': '29114255044317305099982738'}conn.request("GET", "/openapi/broker/instrument/stock/list?symbols=AAPL,TSLA&last_instrument_id=951007842&page_size=1000", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:37:57Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '88603761372859478065277798',  'x-version': 'v2',  'x-signature': '29114255044317305099982738'}conn.request("GET", "/openapi/broker/instrument/stock/list?symbols=AAPL,TSLA&last_instrument_id=951007842&page_size=1000", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-instrument-list](https://developer.webull.hk/apis/docs/reference/broker-api/broker-instrument-list)
