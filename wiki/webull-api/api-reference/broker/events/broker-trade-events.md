---
title: "Trade Events"
method: "gRPC"
endpoint: "broker-trade-events"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/custom/broker-trade-events"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Trade Events

**Protocol:** gRPC Stream  
**Event:** `broker-trade-events`  
**Host:** `events-api.webull.hk` (production) / `events-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-trade-events](https://developer.webull.hk/apis/docs/reference/custom/broker-trade-events)

Broker APIEventsTrade Events
Trade Events
Ask AI

To enable third-party systems to promptly obtain order execution results and order status updates, Broker OpenAPI provides an asynchronous active push mechanism for order trading events.

Clients can subscribe to order-related events to receive notifications, allowing them to monitor order processing results and execution status changes in real time.

Order​

Order Event Notification

FILLED
FINAL_FILLED
PLACE_FAILED
MODIFY_SUCCESS
MODIFY_FAILED
CANCEL_SUCCESS
CANCEL_FAILED
{
"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    
"event_type": "TRADE",    
"timestamp": "2025-03-29T07:02:33.200962333Z",    
"payload": {  
   "request_id": "1045474398137483264",
    "account_id": "4MHSOMIJ88O7E80VBG0O4G6E9A",
    "client_order_id": "db74f19918054a7e9bb72067731c9ae4",
    "instrument_id": "913256135",
    "order_status": "PARTIAL_FILLED",
    "symbol": "AAPL",
    "qty": "10.00",
    "filled_price": "180.00",
    "filled_qty": "1.00",
    "filled_time": "2025-11-21T06:27:43.312+0000",
    "side": "BUY",
    "category": "US_STOCK",
    "order_type": "LIMIT",
    "scene_type": "FILLED",
    "biz_type":"TRADE"
    }
}

Response Fields​
Field	Type	Description
id	string	Unique event identifier
event_type	string	Event type, fixed as TRADE
timestamp	string	Event timestamp in ISO 8601 format
payload	object	Event payload data
Payload Fields​
Field	Type	Description
account_id	string	Account id
request_id	string	Request Id
order_id	string	System-generated order identifier.
client_order_id	array	Client-defined order identifier.
instrument_id	string	Instrument Id
order_status	string	Order Status, See the status field in the Order Detail API response.
symbol	string	Trading symbol of the financial instrument.Represents the unique identifier of the security in the specified market.
qty	string	Total order quantity. Represents the total number of units submitted for this order.
filled_qty	string	Quantity that has been executed. Represents the number of units that have been filled so far.
filled_price	string	Average transaction price of the filled quantity. If the order has not been executed yet, this may be zero or null.
filled_time	string	Time of the last executed trade in milliseconds since Unix epoch.
side	string	Order Side, See the side field in the Order Detail API response.
category	string	Category, HK_STOCK or US_STOCK .
order_type	string	Order Type, See the order_type field in the Order Detail API response.
scene_type	string	Indicates the order event scenario or execution result.
biz_type	string	Business type, fixed as TRADE
Scene Types​
scene_type	Description
FILLED	Partially filled
FINAL_FILLED	All filled
PLACE_FAILED	Order failed
MODIFY_SUCCESS	Change order successfully
MODIFY_FAILED	Change order failed
CANCEL_SUCCESS	Cancellation succeeded
CANCEL_FAILED	Cancellation failed

## Extracted Tables

### Table 1

| Field | Type | Description |
| --- | --- | --- |
| id | string | Unique event identifier |
| event_type | string | Event type, fixed as TRADE |
| timestamp | string | Event timestamp in ISO 8601 format |
| payload | object | Event payload data |

### Table 2

| Field | Type | Description |
| --- | --- | --- |
| account_id | string | Account id |
| request_id | string | Request Id |
| order_id | string | System-generated order identifier. |
| client_order_id | array | Client-defined order identifier. |
| instrument_id | string | Instrument Id |
| order_status | string | Order Status, See the status field in the Order Detail API response. |
| symbol | string | Trading symbol of the financial instrument.Represents the unique identifier of the security in the specified market. |
| qty | string | Total order quantity. Represents the total number of units submitted for this order. |
| filled_qty | string | Quantity that has been executed. Represents the number of units that have been filled so far. |
| filled_price | string | Average transaction price of the filled quantity. If the order has not been executed yet, this may be zero or null. |
| filled_time | string | Time of the last executed trade in milliseconds since Unix epoch. |
| side | string | Order Side, See the side field in the Order Detail API response. |
| category | string | Category, HK_STOCK  or US_STOCK . |
| order_type | string | Order Type, See the order_type  field in the Order Detail API response. |
| scene_type | string | Indicates the order event scenario or execution result. |
| biz_type | string | Business type, fixed as TRADE |

### Table 3

| scene_type | Description |
| --- | --- |
| FILLED | Partially filled |
| FINAL_FILLED | All filled |
| PLACE_FAILED | Order failed |
| MODIFY_SUCCESS | Change order successfully |
| MODIFY_FAILED | Change order failed |
| CANCEL_SUCCESS | Cancellation succeeded |
| CANCEL_FAILED | Cancellation failed |

## Code Examples

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {     "request_id": "1045474398137483264",    "account_id": "4MHSOMIJ88O7E80VBG0O4G6E9A",    "client_order_id": "db74f19918054a7e9bb72067731c9ae4",    "instrument_id": "913256135",    "order_status": "PARTIAL_FILLED",    "symbol": "AAPL",    "qty": "10.00",    "filled_price": "180.00",    "filled_qty": "1.00",    "filled_time": "2025-11-21T06:27:43.312+0000",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "FILLED",    "biz_type":"TRADE"    }}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {     "request_id": "1045474398137483264",    "account_id": "4MHSOMIJ88O7E80VBG0O4G6E9A",    "client_order_id": "db74f19918054a7e9bb72067731c9ae4",    "instrument_id": "913256135",    "order_status": "PARTIAL_FILLED",    "symbol": "AAPL",    "qty": "10.00",    "filled_price": "180.00",    "filled_qty": "1.00",    "filled_time": "2025-11-21T06:27:43.312+0000",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "FILLED",    "biz_type":"TRADE"    }}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {     "request_id": "1045474398137483264",    "account_id": "4MHSOMIJ88O7E80VBG0O4G6E9A",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "db74f19918054a7e9bb72067731c9ae4",    "instrument_id": "913256135",    "order_status": "FILLED",    "symbol": "AAPL",    "qty": "10.00",    "filled_price": "180.00",    "filled_qty": "10.00",    "filled_time": "2025-11-21T06:27:43.312+0000",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "FINAL_FILLED",    "biz_type":"TRADE"    }}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {     "request_id": "1045474398137483264",    "account_id": "4MHSOMIJ88O7E80VBG0O4G6E9A",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "db74f19918054a7e9bb72067731c9ae4",    "instrument_id": "913256135",    "order_status": "FILLED",    "symbol": "AAPL",    "qty": "10.00",    "filled_price": "180.00",    "filled_qty": "10.00",    "filled_time": "2025-11-21T06:27:43.312+0000",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "FINAL_FILLED",    "biz_type":"TRADE"    }}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "request_id": "1045474643156140032",    "account_id": "4MHSOMIJ88O7E80VBG0O4G6E9A",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "de2868b71c154bcaafd2baca61127966",    "instrument_id": "913256135",    "order_status": "FAILED",    "symbol": "AAPL",    "qty": "10.00",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "PLACE_FAILED",    "biz_type":"TRADE"    }}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "request_id": "1045474643156140032",    "account_id": "4MHSOMIJ88O7E80VBG0O4G6E9A",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "de2868b71c154bcaafd2baca61127966",    "instrument_id": "913256135",    "order_status": "FAILED",    "symbol": "AAPL",    "qty": "10.00",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "PLACE_FAILED",    "biz_type":"TRADE"    }}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",      "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",    "request_id": "036LVV5P4I8BV0KHKN60000000",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",    "instrument_id": "913256135",    "order_status": "SUBMITTED",    "symbol": "AAPL",    "qty": "4.0000000000",    "filled_price": "0E-10",    "filled_qty": "0E-10",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "MODIFY_SUCCESS",    "biz_type":"TRADE"}}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",      "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",    "request_id": "036LVV5P4I8BV0KHKN60000000",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",    "instrument_id": "913256135",    "order_status": "SUBMITTED",    "symbol": "AAPL",    "qty": "4.0000000000",    "filled_price": "0E-10",    "filled_qty": "0E-10",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "MODIFY_SUCCESS",    "biz_type":"TRADE"}}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",    "request_id": "036LVV5P4I8BV0KHKN60000000",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",    "instrument_id": "913256135",    "order_status": "SUBMITTED",    "symbol": "AAPL",    "qty": "4.0000000000",    "filled_price": "0E-10",    "filled_qty": "0E-10",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "MODIFY_FAILED",    "biz_type":"TRADE"}}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",    "request_id": "036LVV5P4I8BV0KHKN60000000",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",    "instrument_id": "913256135",    "order_status": "SUBMITTED",    "symbol": "AAPL",    "qty": "4.0000000000",    "filled_price": "0E-10",    "filled_qty": "0E-10",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "MODIFY_FAILED",    "biz_type":"TRADE"}}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",      "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",    "request_id": "036LVV5P4I8BV0KHKN60000000",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",    "instrument_id": "913256135",    "order_status": "CANCELLED",    "symbol": "AAPL",    "qty": "4.0000000000",    "filled_price": "0E-10",    "filled_qty": "0E-10",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "CANCEL_SUCCESS",    "biz_type":"TRADE"}}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",      "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",    "request_id": "036LVV5P4I8BV0KHKN60000000",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",    "instrument_id": "913256135",    "order_status": "CANCELLED",    "symbol": "AAPL",    "qty": "4.0000000000",    "filled_price": "0E-10",    "filled_qty": "0E-10",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "CANCEL_SUCCESS",    "biz_type":"TRADE"}}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",      "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",    "request_id": "036LVV5P4I8BV0KHKN60000000",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",    "instrument_id": "913256135",    "order_status": "SUBMITTED",    "symbol": "AAPL",    "qty": "4.0000000000",    "filled_price": "0E-10",    "filled_qty": "0E-10",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "CANCEL_FAILED",    "biz_type":"TRADE"}}
```

```json
{"id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "TRADE",      "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {    "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",    "request_id": "036LVV5P4I8BV0KHKN60000000",    "order_id": "036LVV5P4I8BV0KHKN60000000",    "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",    "instrument_id": "913256135",    "order_status": "SUBMITTED",    "symbol": "AAPL",    "qty": "4.0000000000",    "filled_price": "0E-10",    "filled_qty": "0E-10",    "side": "BUY",    "category": "US_STOCK",    "order_type": "LIMIT",    "scene_type": "CANCEL_FAILED",    "biz_type":"TRADE"}}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-trade-events](https://developer.webull.hk/apis/docs/reference/custom/broker-trade-events)
