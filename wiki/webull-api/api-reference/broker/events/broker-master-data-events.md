---
title: "Master Data Events"
method: "gRPC"
endpoint: "broker-master-data-events"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/custom/broker-master-data-events"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Master Data Events

**Protocol:** gRPC Stream  
**Event:** `broker-master-data-events`  
**Host:** `events-api.webull.hk` (production) / `events-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-master-data-events](https://developer.webull.hk/apis/docs/reference/custom/broker-master-data-events)

Broker APIEventsMaster Data Events
Master Data Events
Ask AI
Trade Calendar​

To enable third-party systems to promptly obtain updates on changes to the trading and settlement calendar, Broker OpenAPI provides an asynchronous proactive event push mechanism for trading and settlement calendar events.

Clients can subscribe to receive these events, allowing them to monitor adjustments to trading days and settlement dates in real time, ensuring accurate time calculations in trading and fund management systems.

CALENDAR_UPDATE
{
    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",
    "event_type": "MASTER_DATA",
    "timestamp": "2025-03-29T07:02:33.200962333Z",
    "payload": {
        "request_id": "036LVV5P4I8BV0KHKN60000000",
        "market": "HK",
        "instrument_type": "EQUITY",
        "year": 2026,
        "biz_type": "CALENDAR_UPDATE"
    }
}

Response Fields​
Field	Type	Description
id	string	Unique event identifier
event_type	string	Event type, fixed as MASTER_DATA
timestamp	string	Event timestamp in ISO 8601 format
payload	object	Event payload data
Payload Fields​
Field	Type	Description
request_id	string	Request Id.
market	string	See the market field in the Query Trade Calendar API request for details.
instrument_type	string	See the instrument_type field in the Query Trade Calendar API request for details.
year	string	Year in YYYY format.
biz_type	string	Business type, fixed as CALENDAR_UPDATE

## Extracted Tables

### Table 1

| Field | Type | Description |
| --- | --- | --- |
| id | string | Unique event identifier |
| event_type | string | Event type, fixed as MASTER_DATA |
| timestamp | string | Event timestamp in ISO 8601 format |
| payload | object | Event payload data |

### Table 2

| Field | Type | Description |
| --- | --- | --- |
| request_id | string | Request Id. |
| market | string | See the market field in the Query Trade Calendar API request for details. |
| instrument_type | string | See the instrument_type field in the Query Trade Calendar API request for details. |
| year | string | Year in YYYY format. |
| biz_type | string | Business type, fixed as CALENDAR_UPDATE |

## Code Examples

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "MASTER_DATA",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {        "request_id": "036LVV5P4I8BV0KHKN60000000",        "market": "HK",        "instrument_type": "EQUITY",        "year": 2026,        "biz_type": "CALENDAR_UPDATE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "MASTER_DATA",    "timestamp": "2025-03-29T07:02:33.200962333Z",    "payload": {        "request_id": "036LVV5P4I8BV0KHKN60000000",        "market": "HK",        "instrument_type": "EQUITY",        "year": 2026,        "biz_type": "CALENDAR_UPDATE"    }}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-master-data-events](https://developer.webull.hk/apis/docs/reference/custom/broker-master-data-events)
