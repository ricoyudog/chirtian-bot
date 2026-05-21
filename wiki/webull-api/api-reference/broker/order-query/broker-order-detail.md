---
title: "Order Detail"
method: "GET"
endpoint: "/openapi/broker/trade/order/detail"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-detail"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Order Detail

**Method:** `GET`  
**Endpoint:** `/openapi/broker/trade/order/detail`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-detail](https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-detail)

Broker APIOrderOrder QueryOrder Detail
Order Detail
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/trade/order/detail

• Function description: Query the order details for specific trade via the order ID.

Request​
QUERY PARAMETERS
account_id
String
REQUIRED

Account identifier.

Example: LOJOQITOD49R6G9BPQM489CISA
client_order_id
String
REQUIRED

Unique client-defined identifier for the order.
Maximum length is 32 characters and must be unique per user/account.
Used to track or reference the order when interacting with the system.

Example: 0KGOHL4PR2SLC0DKIND4TI0002
HEADER PARAMETERS
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
client_order_id
string
REQUIRED

Client-defined order identifier. Returned in the response for simple orders.
Represents the unique order ID assigned by the user when placing the order.

Example: THI82O5JB7MQ2K76LL5FSDS2CB
combo_type
string
REQUIRED

Type of order combination.
• NORMAL: Indicates a standard single order.

Possible values: [NORMAL]

Example: NORMAL
orders
object[]
REQUIRED

Order Details

client_order_id
string
REQUIRED

Client-defined order identifier. Returned in the response for simple orders.
Represents the unique order ID assigned by the user when placing the order.

Example: THI82O5JB7MQ2K76LL5FSDS2CB
order_id
string
REQUIRED

System-generated order identifier. Returned in the response for simple orders.
Represents the unique Webull order ID assigned by the system.

Example: 0352U72LQI6DT0KF41GK000000
symbol
string
REQUIRED

Trading symbol of the financial instrument.Represents the unique identifier of the security in the specified market (e.g., ticker symbol for equities or option symbol code for derivatives).

Example: AAPL
side
string
REQUIRED

The order side indicating the intended trading direction of the transaction. The meaning of side may vary depending on the instrument_type and account type (e.g., margin vs. cash).

Possible values: [BUY, SELL, SHORT]

Example: BUY
status
string
REQUIRED

• PENDING: Indicates that the order has been submitted to the exchange and is awaiting completion
• SUBMITTED: Indicates that the order has been submitted to the exchange and is awaiting completion

• CANCELLED: Indicates that the order has been successfully cancelled
• FILLED: Indicates that the order has been fully executed
• FAILED: Indicates a failed order, such as REJECTED
• PARTIAL_FILLED: Refers to the portion of the order that has been completed, but not all of it has been completed

Possible values: [PENDING, SUBMITTED, CANCELLED, FILLED, FAILED, PARTIAL_FILLED]

Example: SUBMITTED
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
instrument_type
string

Type of financial instrument associated with the request.

Possible values: [EQUITY]

Example: EQUITY
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
total_quantity
string
REQUIRED

Total order quantity. Represents the total number of units submitted for this order.

Example: 1
filled_quantity
string

Quantity that has been executed. Represents the number of units that have been filled so far.

Example: 1
filled_price
string

Average transaction price of the filled quantity. If the order has not been executed yet, this may be zero or null.

Example: 11.0
limit_price
string

Limit price of the order. Required when order_type is LIMIT, STOP_LOSS_LIMIT, ENHANCED_LIMIT, or AT_AUCTION_LIMIT or TOUCH_LMT.
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
place_time
string
REQUIRED

Order placement time in milliseconds since Unix epoch.

Example: 1726745361658
place_time_at
string
REQUIRED

Order placement time in ISO8601 format (UTC). Format: YYYY-MM-DDThh:mm:ssZ

Example: 2025-11-11T05:44:35.385Z
filled_time
string
REQUIRED

Time of the last executed trade in milliseconds since Unix epoch.

Example: 1726745361871
filled_time_at
string
REQUIRED

Time of the last executed trade in ISO8601 format (UTC). Format: YYYY-MM-DDThh:mm:ssZ

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

	  'x-timestamp': '2026-05-17T14:38:34Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '11221961684525157643099828',

	  'x-version': 'v2',

	  'x-signature': '50519493276229175141105186'

	}

	conn.request("GET", "/openapi/broker/trade/order/detail?account_id=LOJOQITOD49R6G9BPQM489CISA&client_order_id=0KGOHL4PR2SLC0DKIND4TI0002", payload, headers)

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
client_order_id — queryREQUIRED
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
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/trade/order/detail
```

```json
{  "client_order_id": "THI82O5JB7MQ2K76LL5FSDS2CB",  "combo_type": "NORMAL",  "orders": [    {      "client_order_id": "THI82O5JB7MQ2K76LL5FSDS2CB",      "order_id": "0352U72LQI6DT0KF41GK000000",      "symbol": "AAPL",      "side": "BUY",      "status": "SUBMITTED",      "order_type": "MARKET",      "instrument_type": "EQUITY",      "support_trading_session": "CORE",      "time_in_force": "DAY",      "total_quantity": "1",      "filled_quantity": "1",      "filled_price": "11.0",      "limit_price": "11.0",      "stop_price": "11.0",      "trailing_type": "AMOUNT",      "trailing_stop_step": "1",      "trailing_limit_price": "11.0",      "trigger_price_type": "PRICE",      "place_time": "1726745361658",      "place_time_at": "2025-11-11T05:44:35.385Z",      "filled_time": "1726745361871",      "filled_time_at": "2025-11-11T05:44:35.385Z"    }  ]}
```

```json
{  "client_order_id": "THI82O5JB7MQ2K76LL5FSDS2CB",  "combo_type": "NORMAL",  "orders": [    {      "client_order_id": "THI82O5JB7MQ2K76LL5FSDS2CB",      "order_id": "0352U72LQI6DT0KF41GK000000",      "symbol": "AAPL",      "side": "BUY",      "status": "SUBMITTED",      "order_type": "MARKET",      "instrument_type": "EQUITY",      "support_trading_session": "CORE",      "time_in_force": "DAY",      "total_quantity": "1",      "filled_quantity": "1",      "filled_price": "11.0",      "limit_price": "11.0",      "stop_price": "11.0",      "trailing_type": "AMOUNT",      "trailing_stop_step": "1",      "trailing_limit_price": "11.0",      "trigger_price_type": "PRICE",      "place_time": "1726745361658",      "place_time_at": "2025-11-11T05:44:35.385Z",      "filled_time": "1726745361871",      "filled_time_at": "2025-11-11T05:44:35.385Z"    }  ]}
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:34Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '11221961684525157643099828',  'x-version': 'v2',  'x-signature': '50519493276229175141105186'}conn.request("GET", "/openapi/broker/trade/order/detail?account_id=LOJOQITOD49R6G9BPQM489CISA&client_order_id=0KGOHL4PR2SLC0DKIND4TI0002", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:34Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '11221961684525157643099828',  'x-version': 'v2',  'x-signature': '50519493276229175141105186'}conn.request("GET", "/openapi/broker/trade/order/detail?account_id=LOJOQITOD49R6G9BPQM489CISA&client_order_id=0KGOHL4PR2SLC0DKIND4TI0002", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-detail](https://developer.webull.hk/apis/docs/reference/broker-api/broker-order-detail)
