---
title: "Instrument Events"
method: "gRPC"
endpoint: "broker-instrument-events"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/custom/broker-instrument-events"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Instrument Events

**Protocol:** gRPC Stream  
**Event:** `broker-instrument-events`  
**Host:** `events-api.webull.hk` (production) / `events-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-instrument-events](https://developer.webull.hk/apis/docs/reference/custom/broker-instrument-events)

Broker APIEventsInstrument Events
Instrument Events
Ask AI

Receive notifications for instrument property changes, including:

Trading permission changes (Tradable/Liquidate only/Non-Tradable)
Shortable status changes (Shortable/Non-Shortable)
Marginable status changes
ETF properties changes (crypto ETF, leveraged ETF, etc.)
Trading Property Change Event​

This event is triggered when an instrument's trading-related properties are updated.

Event Structure​
{
    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",
    "event_type": "INSTRUMENT",
    "position": "CJO1fxACGAAgADAB",
    "timestamp": "2025-03-29T07:02:33.200Z",
    "payload": {
        "instrument_id": "10152734329",
        "status": "NT",
        "shortable": "true",
        "marginable": "true",
        "biz_type": "PROPERTY_CHANGE"
    }
}

Response Fields​
Field	Type	Description
id	string	Unique event identifier
position	string	Cursor for event replay; re-pushes subsequent events within the current business type.
event_type	string	Event type, fixed as INSTRUMENT
timestamp	string	Event timestamp in ISO 8601 format
payload	object	Event payload data
Payload Fields​
Field	Type	Description
instrument_id	string	Unique instrument identifier
status	string	Trading status:
- OC: Tradable
- CO: Liquidate only
- NT: Non-Tradable
shortable	string	Whether shortable: true / false
marginable	string	Whether margin trading supported: true / false
biz_type	string	Business type, fixed as PROPERTY_CHANGE
Status Values​

Trading status (status) values:

Value	Description
OC	Tradable - Instrument can be bought and sold normally
CO	Liquidate only - Can only sell existing positions, cannot open new positions
NT	Non-Tradable - No trading operations allowed
Use Cases​

Listening to this event can be used for:

Trading Permission Monitoring: Get real-time updates on instrument trading permission changes and update UI displays accordingly
Short Status Tracking: Monitor changes in shortable status and adjust trading strategies
Risk Management: Adjust positions and risk controls based on margin requirement changes
Basic Property Change Event​

This event is triggered when an instrument's basic properties (such as ETF properties) are updated.

Event Structure​
{
    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",
    "event_type": "INSTRUMENT",
    "position": "CJO1fxACGAAgADAB",
    "timestamp": "2025-03-29T07:02:33.200Z",
    "payload": {
        "instrument_id": "10152734329",
        "crypto_etf": "false",
        "etf_leveraged_flag": "YES",
        "etf_leveraged_factor": "-1.0",
        "single_stock_etf": "false",
        "inverse_etf": "false",
        "biz_type": "BASIC_PROPERTY_CHANGE"
    }
}

Response Fields​
Field	Type	Description
id	string	Unique event identifier
position	string	Cursor for event replay; re-pushes subsequent events within the current business type.
event_type	string	Event type, fixed as INSTRUMENT
timestamp	string	Event timestamp in ISO 8601 format
payload	object	Event payload data
Payload Fields​
Field	Type	Description
instrument_id	string	Unique instrument identifier
crypto_etf	string	Whether crypto ETF: true / false. Empty if not ETF
etf_leveraged_flag	string	Whether leveraged ETF: YES / NO. Empty if not ETF
etf_leveraged_factor	string	ETF leverage factor. Empty if not ETF. Negative value for inverse ETF, positive value for regular leveraged ETF
single_stock_etf	string	Whether single stock ETF: true / false. Empty if not ETF
inverse_etf	string	Whether inverse ETF: true / false. Empty if not ETF
biz_type	string	Business type, fixed as BASIC_PROPERTY_CHANGE
Use Cases​

Listening to this event can be used for:

ETF Product Monitoring: Track updates to ETF-specific properties
Risk Classification: Identify high-risk products like leveraged or inverse ETFs
Product Filtering: Filter instruments based on ETF characteristics (crypto ETF, single stock ETF, etc.)
Investment Strategy: Adjust strategies based on leverage factors and ETF types

## Extracted Tables

### Table 1

| Field | Type | Description |
| --- | --- | --- |
| id | string | Unique event identifier |
| position | string | Cursor for event replay; re-pushes subsequent events within the current business type. |
| event_type | string | Event type, fixed as INSTRUMENT |
| timestamp | string | Event timestamp in ISO 8601 format |
| payload | object | Event payload data |

### Table 2

| Field | Type | Description |
| --- | --- | --- |
| instrument_id | string | Unique instrument identifier |
| status | string | Trading status:- OC: Tradable- CO: Liquidate only- NT: Non-Tradable |
| shortable | string | Whether shortable: true / false |
| marginable | string | Whether margin trading supported: true / false |
| biz_type | string | Business type, fixed as PROPERTY_CHANGE |

### Table 3

| Value | Description |
| --- | --- |
| OC | Tradable - Instrument can be bought and sold normally |
| CO | Liquidate only - Can only sell existing positions, cannot open new positions |
| NT | Non-Tradable - No trading operations allowed |

### Table 4

| Field | Type | Description |
| --- | --- | --- |
| id | string | Unique event identifier |
| position | string | Cursor for event replay; re-pushes subsequent events within the current business type. |
| event_type | string | Event type, fixed as INSTRUMENT |
| timestamp | string | Event timestamp in ISO 8601 format |
| payload | object | Event payload data |

### Table 5

| Field | Type | Description |
| --- | --- | --- |
| instrument_id | string | Unique instrument identifier |
| crypto_etf | string | Whether crypto ETF: true / false. Empty if not ETF |
| etf_leveraged_flag | string | Whether leveraged ETF: YES / NO. Empty if not ETF |
| etf_leveraged_factor | string | ETF leverage factor. Empty if not ETF. Negative value for inverse ETF, positive value for regular leveraged ETF |
| single_stock_etf | string | Whether single stock ETF: true / false. Empty if not ETF |
| inverse_etf | string | Whether inverse ETF: true / false. Empty if not ETF |
| biz_type | string | Business type, fixed as BASIC_PROPERTY_CHANGE |

## Code Examples

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "INSTRUMENT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {        "instrument_id": "10152734329",        "status": "NT",        "shortable": "true",        "marginable": "true",        "biz_type": "PROPERTY_CHANGE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "INSTRUMENT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {        "instrument_id": "10152734329",        "status": "NT",        "shortable": "true",        "marginable": "true",        "biz_type": "PROPERTY_CHANGE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "INSTRUMENT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {        "instrument_id": "10152734329",        "crypto_etf": "false",        "etf_leveraged_flag": "YES",        "etf_leveraged_factor": "-1.0",        "single_stock_etf": "false",        "inverse_etf": "false",        "biz_type": "BASIC_PROPERTY_CHANGE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "INSTRUMENT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {        "instrument_id": "10152734329",        "crypto_etf": "false",        "etf_leveraged_flag": "YES",        "etf_leveraged_factor": "-1.0",        "single_stock_etf": "false",        "inverse_etf": "false",        "biz_type": "BASIC_PROPERTY_CHANGE"    }}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-instrument-events](https://developer.webull.hk/apis/docs/reference/custom/broker-instrument-events)
