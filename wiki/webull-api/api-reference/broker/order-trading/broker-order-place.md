---
title: "Place Order"
method: "POST"
endpoint: "/openapi/broker/trade/order/place"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-place"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Place Order

**Method:** `POST`  
**Endpoint:** `/openapi/broker/trade/order/place`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-place](https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-place)

Broker APIOrderTradingOrder Place
Order Place
Ask AI
POST
https://hk-broker-api.uat.webullbroker.com/openapi/broker/trade/order/place

• Function description: Place order for a specific account. For order execution of accounts with Omnibus with VA model, please submit virtual account number instead of omnibus master account number.

Request​
HEADER PARAMETERS
APPLICATION/JSON
BODYREQUIRED
account_id
string
REQUIRED

Account identifier

Example: 93IUJ28O9VO2KBGHDHR4H9
new_orders
object[]
REQUIRED

Order Details

combo_type
string
REQUIRED

Type of order combination.
• NORMAL: Indicates a standard single order.

Example: NORMAL
client_order_id
string
REQUIRED

Unique client-defined identifier for the order.
Maximum length is 32 characters.
Allowed characters: letters (A–Z, a–z), digits (0–9), hyphen (-), underscore (_).

Example: 0KGOHL4PR2SLC0DKIND4TI0002
instrument_type
string
REQUIRED

Type of financial instrument associated with the request.

Possible values: [EQUITY]

Example: EQUITY
market
string
REQUIRED

Market code indicating the trading venue or regulatory region of the financial instrument. Used together with symbol and instrument_type to uniquely identify a tradable instrument.

Possible values: [US, HK, CN]

Example: US
symbol
string
REQUIRED

Trading symbol of the financial instrument. Represents the unique identifier of the security in the specified market.

Example: BULL
order_type
string
REQUIRED

Specifies the type of order to be placed. Determines how the order will be executed in the market.
Available order types depend on the market and instrument type.
Options trading Only LIMIT,STOP_LOSS,STOP_LOSS_LIMIT are supported.
U.S. Stock
  • LIMIT: Limit Order
  • MARKET: Market Order
  • STOP_LOSS: Stop Order
  • STOP_LOSS_LIMIT: Stop Limit Order
  • MARKET_ON_OPEN: Opening market order
  • MARKET_ON_CLOSE: Closing market order
Hong Kong Stock
  • ENHANCED_LIMIT: Enhanced Limit Order
  • AT_AUCTION: At-auction order
  • AT_AUCTION_LIMIT: At-auction limit order
  • STOP_LOSS: Stop Order
  • STOP_LOSS_LIMIT: Stop Limit Order
  • TRAILING_STOP_LOSS: Trailing Stop Order
  • TRAILING_STOP_LOSS_LIMIT: Trailing Stop Limit Order
  • TOUCH_MKT: Touch Market Order
  • TOUCH_LMT: Touch Limit Order
  • MARKET: Market Order
China Connect
  • LIMIT: Limit Order


Possible values: [LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, ENHANCED_LIMIT, AT_AUCTION, AT_AUCTION_LIMIT, MARKET_ON_OPEN, MARKET_ON_CLOSE, TRAILING_STOP_LOSS, TRAILING_STOP_LOSS_LIMIT, TOUCH_MKT, TOUCH_LMT]

Example: MARKET
entrust_type
string
REQUIRED

Specifies the method for placing the order.
• QTY: Order specified by quantity of shares or units.
• AMOUNT: Order specified by total cash amount, applicable for fractional share trading of US stocks.

Possible values: [QTY, AMOUNT]

Example: QTY
support_trading_session
string

Specifies the trading session for the order. Applicable to U.S. stock market orders only.
Deprecated values:
• Y: [Deprecated]Include extended trading hours.
• N: [Deprecated]Only support regular trading hours.
Active values:
• NIGHT: Only supports night trading.
• ALL: Include extended trading hours.
• CORE: Only support regular trading hours.
• ALL_DAY: Included Overnight Hours, 8:00 p.m.ET - 8:00 p.m.ET(the next day)

Possible values: [Y, N, NIGHT, ALL, CORE, ALL_DAY]

Example: CORE
time_in_force
string
REQUIRED

Specifies the duration for which the order remains active in the market (Time-In-Force).
• DAY: The order is valid only for the current trading day and expires at the end of the day.
• GTC: Good-Till-Canceled, the order remains active until it is executed, explicitly canceled, or reaches the maximum allowed duration (typically 90 days).

Possible values: [DAY, GTC]

Example: DAY
side
string
REQUIRED

The order side indicating the intended trading direction of the transaction. The meaning of side may vary depending on the instrument_type and account type (e.g., margin vs. cash).

Possible values: [BUY, SELL, SHORT]

Example: BUY
quantity
string

Transaction quantity. You can specify decimals when placing fractional lot orders for US stocks.
Crypto trading supports quantities with up to 8 decimal places.

Example: 1
total_cash_amount
string

The total order amount is currently only applicable to US stock fractional share transactions and when the order is placed by amount.

Example: 100.4
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
sender_sub_id
string

Identifier for the firm or sub-account in third-party transactions.
For brokers, this field should contain the UUID of the broker user. Used to distinguish different entities or users within the same firm.

no_party_ids
object[]

List of party identifiers. Applicable only for Hong Kong stock orders.

party_id
string
REQUIRED

ID of the broker client submitting the order. Format examples:
• CE Number Format: ABC123
• BCAN Format: 2568
Combined format example: ABC123.2568
Must be certified by the BCAN system of the Hong Kong Stock Exchange.

Example: ABC123.2568
party_id_source
string
REQUIRED

Source of the party ID. Value must be "D" (Proprietary/Custom Code).

Example: D
party_role
string
REQUIRED

Role of the party. Value must be "3" (Client ID, BCAN Field).

Example: 3
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

	  "new_orders": [

	    {

	      "combo_type": "NORMAL",

	      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",

	      "instrument_type": "EQUITY",

	      "market": "US",

	      "symbol": "BULL",

	      "order_type": "MARKET",

	      "entrust_type": "QTY",

	      "support_trading_session": "CORE",

	      "time_in_force": "DAY",

	      "side": "BUY",

	      "quantity": "1",

	      "total_cash_amount": "100.4",

	      "limit_price": "11.0",

	      "stop_price": "11.0",

	      "trailing_type": "AMOUNT",

	      "trailing_stop_step": "1",

	      "trailing_limit_price": "11.0",

	      "trigger_price_type": "PRICE",

	      "sender_sub_id": "string",

	      "no_party_ids": [

	        {

	          "party_id": "ABC123.2568",

	          "party_id_source": "D",

	          "party_role": "3"

	        }

	      ]

	    }

	  ]

	})

	headers = {

	  'Content-Type': 'application/json',

	  'Accept': 'application/json',

	  'x-timestamp': '2026-05-17T14:38:24Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '73549493371597536396170552',

	  'x-version': 'v2',

	  'x-signature': '79227350046433967183163338'

	}

	conn.request("POST", "/openapi/broker/trade/order/place", payload, headers)

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
  "new_orders": [
    {
      "combo_type": "NORMAL",
      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",
      "instrument_type": "EQUITY",
      "market": "US",
      "symbol": "BULL",
      "order_type": "MARKET",
      "entrust_type": "QTY",
      "support_trading_session": "CORE",
      "time_in_force": "DAY",
      "side": "BUY",
      "quantity": "1",
      "total_cash_amount": "100.4",
      "limit_price": "11.0",
      "stop_price": "11.0",
      "trailing_type": "AMOUNT",
      "trailing_stop_step": "1",
      "trailing_limit_price": "11.0",
      "trigger_price_type": "PRICE",
      "sender_sub_id": "string",
      "no_party_ids": [
        {
          "party_id": "ABC123.2568",
          "party_id_source": "D",
          "party_role": "3"
        }
      ]
    }
  ]
}

SEND API REQUEST
RESPONSE
CLEAR

Click the Send API Request button above and see the response here!

## Code Examples

```
POST https://hk-broker-api.uat.webullbroker.com/openapi/broker/trade/order/place
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
import http.clientimport jsonconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = json.dumps({  "account_id": "93IUJ28O9VO2KBGHDHR4H9",  "new_orders": [    {      "combo_type": "NORMAL",      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",      "instrument_type": "EQUITY",      "market": "US",      "symbol": "BULL",      "order_type": "MARKET",      "entrust_type": "QTY",      "support_trading_session": "CORE",      "time_in_force": "DAY",      "side": "BUY",      "quantity": "1",      "total_cash_amount": "100.4",      "limit_price": "11.0",      "stop_price": "11.0",      "trailing_type": "AMOUNT",      "trailing_stop_step": "1",      "trailing_limit_price": "11.0",      "trigger_price_type": "PRICE",      "sender_sub_id": "string",      "no_party_ids": [        {          "party_id": "ABC123.2568",          "party_id_source": "D",          "party_role": "3"        }      ]    }  ]})headers = {  'Content-Type': 'application/json',  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:24Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '73549493371597536396170552',  'x-version': 'v2',  'x-signature': '79227350046433967183163338'}conn.request("POST", "/openapi/broker/trade/order/place", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientimport jsonconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = json.dumps({  "account_id": "93IUJ28O9VO2KBGHDHR4H9",  "new_orders": [    {      "combo_type": "NORMAL",      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",      "instrument_type": "EQUITY",      "market": "US",      "symbol": "BULL",      "order_type": "MARKET",      "entrust_type": "QTY",      "support_trading_session": "CORE",      "time_in_force": "DAY",      "side": "BUY",      "quantity": "1",      "total_cash_amount": "100.4",      "limit_price": "11.0",      "stop_price": "11.0",      "trailing_type": "AMOUNT",      "trailing_stop_step": "1",      "trailing_limit_price": "11.0",      "trigger_price_type": "PRICE",      "sender_sub_id": "string",      "no_party_ids": [        {          "party_id": "ABC123.2568",          "party_id_source": "D",          "party_role": "3"        }      ]    }  ]})headers = {  'Content-Type': 'application/json',  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:24Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '73549493371597536396170552',  'x-version': 'v2',  'x-signature': '79227350046433967183163338'}conn.request("POST", "/openapi/broker/trade/order/place", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
{
  "account_id": "93IUJ28O9VO2KBGHDHR4H9",
  "new_orders": [
    {
      "combo_type": "NORMAL",
      "client_order_id": "0KGOHL4PR2SLC0DKIND4TI0002",
      "instrument_type": "EQUITY",
      "market": "US",
      "symbol": "BULL",
      "order_type": "MARKET",
      "entrust_type": "QTY",
      "support_trading_session": "CORE",
      "time_in_force": "DAY",
      "side": "BUY",
      "quantity": "1",
      "total_cash_amount": "100.4",
      "limit_price": "11.0",
      "stop_price": "11.0",
      "trailing_type": "AMOUNT",
      "trailing_stop_step": "1",
      "trailing_limit_price": "11.0",
      "trigger_price_type": "PRICE",
      "sender_sub_id": "string",
      "no_party_ids": [
        {
          "party_id": "ABC123.2568",
          "party_id_source": "D",
          "party_role": "3"
        }
      ]
    }
  ]
}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-place](https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-place)
