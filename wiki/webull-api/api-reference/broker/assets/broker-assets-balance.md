---
title: "Account Balance"
method: "POST"
endpoint: "/openapi/broker/assets/balance"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-balance"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Account Balance

**Method:** `POST`  
**Endpoint:** `/openapi/broker/assets/balance`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-balance](https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-balance)

Broker APIAssetsAccount Balance
Account Balance
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/assets/balance

• Function description: Query account asset related information, includes: cash balance, position market value, profit & loss, buying power, interest payable, etc.

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
total_asset_currency
string
REQUIRED

Currency

Possible values: [CNH, HKD, USD]

Example: HKD
total_cash_balance
string
REQUIRED

Cash Balance

Example: 485705.0
total_market_value
string
REQUIRED

Total holding market value

Example: 995705.0
total_unrealized_profit_loss
string
REQUIRED

Open P&L

Example: 227689.0
account_currency_assets
object[]
REQUIRED

Currency assets Details

currency
string
REQUIRED

Currency

Possible values: [CNH, HKD, USD]

Example: HKD
cash_balance
string
REQUIRED

Cash Balance

Example: 485705.95
settled_cash
string
REQUIRED

Settled Cash

Example: 485705.95
unsettled_cash
string
REQUIRED

Unsettled Cash

Example: 0.0
market_value
string
REQUIRED

holding market value

Example: 0.0
held_amount
string

In-transit funds

Example: 0.0
frozen_amount
string

Frozen funds

Example: 485705
buying_power
string
REQUIRED

Buying Power

Example: 484551
unrealized_profit_loss
string
REQUIRED

Open P&L

Example: 227689
available_withdrawal
string
REQUIRED

The withdrawable amount

Example: 3.0558743194E8
interests_unpaid
string
REQUIRED

Interest to be paid

Example: 0.0
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

	  'x-timestamp': '2026-05-17T14:38:12Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '36899900848750103379917658',

	  'x-version': 'v2',

	  'x-signature': '68863312931715376738861917'

	}

	conn.request("GET", "/openapi/broker/assets/balance?account_id=LOJOQITOD49R6G9BPQM489CISA", payload, headers)

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
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/assets/balance
```

```json
{  "total_asset_currency": "HKD",  "total_cash_balance": "485705.0",  "total_market_value": "995705.0",  "total_unrealized_profit_loss": "227689.0",  "account_currency_assets": [    {      "currency": "HKD",      "cash_balance": "485705.95",      "settled_cash": "485705.95",      "unsettled_cash": "0.0",      "market_value": "0.0",      "held_amount": "0.0",      "frozen_amount": "485705",      "buying_power": "484551",      "unrealized_profit_loss": "227689",      "available_withdrawal": "3.0558743194E8",      "interests_unpaid": "0.0"    }  ]}
```

```json
{  "total_asset_currency": "HKD",  "total_cash_balance": "485705.0",  "total_market_value": "995705.0",  "total_unrealized_profit_loss": "227689.0",  "account_currency_assets": [    {      "currency": "HKD",      "cash_balance": "485705.95",      "settled_cash": "485705.95",      "unsettled_cash": "0.0",      "market_value": "0.0",      "held_amount": "0.0",      "frozen_amount": "485705",      "buying_power": "484551",      "unrealized_profit_loss": "227689",      "available_withdrawal": "3.0558743194E8",      "interests_unpaid": "0.0"    }  ]}
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:12Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '36899900848750103379917658',  'x-version': 'v2',  'x-signature': '68863312931715376738861917'}conn.request("GET", "/openapi/broker/assets/balance?account_id=LOJOQITOD49R6G9BPQM489CISA", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:12Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '36899900848750103379917658',  'x-version': 'v2',  'x-signature': '68863312931715376738861917'}conn.request("GET", "/openapi/broker/assets/balance?account_id=LOJOQITOD49R6G9BPQM489CISA", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-balance](https://developer.webull.hk/apis/docs/reference/broker-api/broker-assets-balance)
