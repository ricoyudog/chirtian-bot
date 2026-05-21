---
title: "Replace Order"
method: "POST"
endpoint: "/openapi/broker/trade/order/replace"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-replace"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Replace Order

**Method:** `POST`  
**Endpoint:** `/openapi/broker/trade/order/replace`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-replace](https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-replace)

Broker APIOrderTradingOrder Replace
Order Replace
Ask AI
POST
https://hk-broker-api.uat.webullbroker.com/openapi/broker/trade/order/replace

• Function description: Modify order submitted with updated parameters.

Request​
HEADER PARAMETERS
APPLICATION/JSON
BODYREQUIRED
account_id
string
REQUIRED

Account identifier

Example: 93IUJ28O9VO2KBGHDHR4H9
modify_orders
object[]
REQUIRED

Order Details

client_order_id
string
REQUIRED

Unique client-defined identifier for the order.
Maximum length is 32 characters.
Allowed characters: letters (A–Z, a–z), digits (0–9), hyphen (-), underscore (_).

Example: 0KGOHL4PR2SLC0DKIND4TI0002
time_in_force
string

Specifies the duration for which the order remains active in the market (Time-In-Force).
• DAY: The order is valid only for the current trading day and expires at the end of the day.
• GTC: Good-Till-Canceled, the order remains active until it is executed, explicitly canceled, or reaches the maximum allowed duration (typically 90 days).

Possible values: [DAY, GTC]

Example: DAY
limit_price
string

Limit price of the order. Required when order_type is LIMIT, STOP_LOSS_LIMIT or TOUCH_LMT.
Specifies the maximum (for buy) or minimum (for sell) price at which the order can be executed.

Example: 11.0
stop_price
string

Stop price of the order. Required when order_type is STOP_LOSS, STOP_LOSS_LIMIT, TOUCH_MKT or TOUCH_LMT.
Specifies the trigger price at which the stop order becomes active.

Example: 11.0
trailing_type
string

When market continues to fall, the stop price to buy follows, or trails, the lowest price of a stock by a trail that you set. Required when order_type is TRAILING_STOP_LOSS or TRAILING_STOP_LOSS_LIMIT.
• AMOUNT: By amount.
• PERCENTAGE: By percentage.

Possible values: [AMOUNT, PERCENTAGE]

Example: AMOUNT
trailing_stop_step
string

Trailing Stop Spread. If the tracking type is percentage, the tracking spread can not exceed 1,0.01 means 1%. Required when order_type is TRAILING_STOP_LOSS or TRAILING_STOP_LOSS_LIMIT.

Example: 1
trailing_limit_price
string

Trailing limit price of the order. Required when order_type is TRAILING_STOP_LOSS_LIMIT.

Example: 11.0
trigger_price_type
string

Trigger price type of the order
• PRICE: Latest transaction price.
• PRICE_BID: Buy at one price.
• PRICE_ASK: Sell at one price.

Possible values: [PRICE, PRICE_BID, PRICE_ASK]

Example: PRICE
quantity
string

Transaction quantity. You can specify decimals when placing fractional lot orders for US stocks.

Example: 1
Responses​
200
417

OK

APPLICATION/JSON
Schema
Example
SCHEMA
client_order_id
string

Client-defined order identifier. Returned in the response for simple orders.
Represents the unique order ID assigned by the user when placing the order for NORMAL order.

Example: 0KGOHL4PR2SLC0DKIND4TI0002
order_id
string

System-generated order identifier. Returned in the response for simple orders.
Represents the unique Webull order ID assigned by the system when placing the order for NORMAL order.

Example: 80HG7CPSFDPCAL3TP66LKBAS69
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

	import json

	

	conn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")

	payload = json.dumps({

	  "account_id": "93IUJ28O9VO2KBGHDHR4H9",

	  "modify_orders": [

	    {

	      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",

	      "time_in_force": "DAY",

	      "limit_price": "11.0",

	      "stop_price": "11.0",

	      "trailing_type": "AMOUNT",

	      "trailing_stop_step": "1",

	      "trailing_limit_price": "11.0",

	      "trigger_price_type": "PRICE",

	      "quantity": "1"

	    }

	  ]

	})

	headers = {

	  'Content-Type': 'application/json',

	  'Accept': 'application/json',

	  'x-timestamp': '2026-05-17T14:38:27Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '53692603704006853353905650',

	  'x-version': 'v2',

	  'x-signature': '83166959328814675790976437'

	}

	conn.request("POST", "/openapi/broker/trade/order/replace", payload, headers)

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
x-app-key — headerREQUIRED
x-app-secret — headerREQUIRED
x-timestamp — headerREQUIRED
x-signature-version — headerREQUIRED
x-signature-algorithm — headerREQUIRED
x-signature-nonce — headerREQUIRED
x-version — headerREQUIRED
x-signature — headerREQUIRED
Body
 REQUIRED
{
  "account_id": "93IUJ28O9VO2KBGHDHR4H9",
  "modify_orders": [
    {
      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",
      "time_in_force": "DAY",
      "limit_price": "11.0",
      "stop_price": "11.0",
      "trailing_type": "AMOUNT",
      "trailing_stop_step": "1",
      "trailing_limit_price": "11.0",
      "trigger_price_type": "PRICE",
      "quantity": "1"
    }
  ]
}

SEND API REQUEST
RESPONSE
CLEAR

Click the Send API Request button above and see the response here!

## Code Examples

```
POST https://hk-broker-api.uat.webullbroker.com/openapi/broker/trade/order/replace
```

```json
{  "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",  "order_id": "80HG7CPSFDPCAL3TP66LKBAS69"}
```

```json
{  "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",  "order_id": "80HG7CPSFDPCAL3TP66LKBAS69"}
```

```json
{  "error_code": "OPENAPI_NO_NIGHT_TRADING_TIME",  "message": "The current period does not support placing night orders"}
```

```json
{  "error_code": "OPENAPI_NO_NIGHT_TRADING_TIME",  "message": "The current period does not support placing night orders"}
```

```json
import http.clientimport jsonconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = json.dumps({  "account_id": "93IUJ28O9VO2KBGHDHR4H9",  "modify_orders": [    {      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",      "time_in_force": "DAY",      "limit_price": "11.0",      "stop_price": "11.0",      "trailing_type": "AMOUNT",      "trailing_stop_step": "1",      "trailing_limit_price": "11.0",      "trigger_price_type": "PRICE",      "quantity": "1"    }  ]})headers = {  'Content-Type': 'application/json',  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:27Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '53692603704006853353905650',  'x-version': 'v2',  'x-signature': '83166959328814675790976437'}conn.request("POST", "/openapi/broker/trade/order/replace", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientimport jsonconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = json.dumps({  "account_id": "93IUJ28O9VO2KBGHDHR4H9",  "modify_orders": [    {      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",      "time_in_force": "DAY",      "limit_price": "11.0",      "stop_price": "11.0",      "trailing_type": "AMOUNT",      "trailing_stop_step": "1",      "trailing_limit_price": "11.0",      "trigger_price_type": "PRICE",      "quantity": "1"    }  ]})headers = {  'Content-Type': 'application/json',  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:27Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '53692603704006853353905650',  'x-version': 'v2',  'x-signature': '83166959328814675790976437'}conn.request("POST", "/openapi/broker/trade/order/replace", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
{
  "account_id": "93IUJ28O9VO2KBGHDHR4H9",
  "modify_orders": [
    {
      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",
      "time_in_force": "DAY",
      "limit_price": "11.0",
      "stop_price": "11.0",
      "trailing_type": "AMOUNT",
      "trailing_stop_step": "1",
      "trailing_limit_price": "11.0",
      "trigger_price_type": "PRICE",
      "quantity": "1"
    }
  ]
}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-replace](https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-replace)
