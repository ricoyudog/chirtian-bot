---
title: "Cancel Order"
method: "POST"
endpoint: "/openapi/broker/trade/order/cancel"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-cancel"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Cancel Order

**Method:** `POST`  
**Endpoint:** `/openapi/broker/trade/order/cancel`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-cancel](https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-cancel)

Broker APIOrderTradingOrder Cancel
Order Cancel
Ask AI
POST
https://hk-broker-api.uat.webullbroker.com/openapi/broker/trade/order/cancel

• Function description: Cancel order submitted which is still under open status.

Request​
HEADER PARAMETERS
APPLICATION/JSON
BODYREQUIRED
account_id
string
REQUIRED

Account identifier

Example: 93IUJ28O9VO2KBGHDHR4H9
client_order_id
string
REQUIRED

Unique client-defined identifier for the order.
Maximum length is 32 characters.
Allowed characters: letters (A–Z, a–z), digits (0–9), hyphen (-), underscore (_).

Example: 0KGOHL4PR2SLC0DKIND4TI0002
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

	  "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002"

	})

	headers = {

	  'Content-Type': 'application/json',

	  'Accept': 'application/json',

	  'x-timestamp': '2026-05-17T14:38:30Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '41891150066074872684954136',

	  'x-version': 'v2',

	  'x-signature': '72687590724278782049126205'

	}

	conn.request("POST", "/openapi/broker/trade/order/cancel", payload, headers)

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
  "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002"
}

SEND API REQUEST
RESPONSE
CLEAR

Click the Send API Request button above and see the response here!

## Code Examples

```
POST https://hk-broker-api.uat.webullbroker.com/openapi/broker/trade/order/cancel
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
import http.clientimport jsonconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = json.dumps({  "account_id": "93IUJ28O9VO2KBGHDHR4H9",  "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002"})headers = {  'Content-Type': 'application/json',  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:30Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '41891150066074872684954136',  'x-version': 'v2',  'x-signature': '72687590724278782049126205'}conn.request("POST", "/openapi/broker/trade/order/cancel", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientimport jsonconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = json.dumps({  "account_id": "93IUJ28O9VO2KBGHDHR4H9",  "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002"})headers = {  'Content-Type': 'application/json',  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:30Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '41891150066074872684954136',  'x-version': 'v2',  'x-signature': '72687590724278782049126205'}conn.request("POST", "/openapi/broker/trade/order/cancel", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
{
  "account_id": "93IUJ28O9VO2KBGHDHR4H9",
  "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002"
}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-cancel](https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-cancel)
