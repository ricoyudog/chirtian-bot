---
title: "Account Events"
method: "gRPC"
endpoint: "broker-account-events"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/custom/broker-account-events"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Account Events

**Protocol:** gRPC Stream  
**Event:** `broker-account-events`  
**Host:** `events-api.webull.hk` (production) / `events-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-account-events](https://developer.webull.hk/apis/docs/reference/custom/broker-account-events)

Broker APIEventsAccount Events
Account Events
Ask AI

Receive notifications for account-related events, including:

Account restrictions and status changes
Virtual Account (VA) BCAN code approval status changes
Account closure processing
Account Update Event​

This event is triggered when an Omni-level account's restrictions or status changes.

Account Update
Event Structure​
{
    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",
    "event_type": "ACCOUNT",
    "position": "CJO1fxACGAAgADAB",
    "timestamp": "2025-03-29T07:02:33.200Z",
    "payload": {
        "account_id": "036UUF6TQA8CD0KHJPEC000000",
        "account_number": "5KT05001",
        "account_type": "CASH",
        "restrictions": [
            "HK_STOCK_NO_TRADE",
            "HK_STOCK_LIQUIDATE_ONLY",
            "US_STOCK_NO_TRADE",
            "US_STOCK_LIQUIDATE_ONLY",
            "CN_STOCK_LIQUIDATE_ONLY",
            "CN_STOCK_NO_TRADE"
        ],
        "update_time": "2025-03-29T07:02:33.200Z",
        "biz_type": "ACCOUNT_UPDATE"
    }
}

Response Fields​
Field	Type	Description
id	string	Unique event identifier
position	string	Cursor for event replay; re-pushes subsequent events within the current business type.
event_type	string	Event type, fixed as ACCOUNT
timestamp	string	Event timestamp in ISO 8601 format
payload	object	Event payload data
Payload Fields​
Field	Type	Description
account_id	string	Account id
account_number	string	Account number
account_type	string	Account type: CASH / MARGIN
restrictions	array	Array of current account restrictions (full snapshot)
update_time	string	Update timestamp in ISO 8601 format
biz_type	string	Business type, fixed as ACCOUNT_UPDATE
Restriction Types​

The restrictions array contains current account restrictions. Each push provides a complete snapshot of all active restrictions:

Restriction Code	Description
HK_STOCK_NO_TRADE	Hong Kong stocks - No trading allowed
HK_STOCK_LIQUIDATE_ONLY	Hong Kong stocks - Liquidate only (can only close positions)
US_STOCK_NO_TRADE	US stocks - No trading allowed
US_STOCK_LIQUIDATE_ONLY	US stocks - Liquidate only (can only close positions)
CN_STOCK_NO_TRADE	China A-shares - No trading allowed
CN_STOCK_LIQUIDATE_ONLY	China A-shares - Liquidate only (can only close positions)
INFO
Each event push contains a full snapshot of current restrictions, not incremental changes
An empty restrictions array means no restrictions are currently active on the account
Virtual Account BCAN Update Event​

This event is triggered when a Virtual Account's (VA) BCAN code approval status changes at the exchange.

BCAN Approved
BCAN Rejected
Event Structure - Approval Success​

When the exchange approves the BCAN code, the corresponding category trading permission is granted for the VA account.

{
    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",
    "event_type": "ACCOUNT",
    "position": "CJO1fxACGAAgADAB",
    "timestamp": "2025-03-29T07:02:33.200Z",
    "payload": {
       "account_id": "O3I8NNB882S2BK7MF1ACJ5UTK9",
       "account_number": "VA0000001",
        "account_type": "MARGIN",
        "type": "CN",
        "status": "SUCCESS",
        "update_time": "2025-03-29T07:02:33.200Z",
        "biz_type": "VIRTUAL_ACCOUNT_BCAN_UPDATE"
    }
}

Response Fields​
Field	Type	Description
id	string	Unique event identifier
position	string	Cursor for event replay; re-pushes subsequent events within the current business type.
event_type	string	Event type, fixed as ACCOUNT
timestamp	string	Event timestamp in ISO 8601 format
payload	object	Event payload data
Payload Fields​
Field	Type	Description
account_id	string	Virtual Account id
account_number	string	Virtual Account number
account_type	string	Account type: CASH / MARGIN
type	string	BCAN type, currently only CN (China A-share) is supported
status	string	BCAN status: SUCCESS / FAILED
update_time	string	Update timestamp in ISO 8601 format
biz_type	string	Business type, fixed as VIRTUAL_ACCOUNT_BCAN_UPDATE
BCAN Status Values​
Status	Description
SUCCESS	BCAN code approved by exchange - Trading permission granted
FAILED	BCAN code rejected by exchange - Trading permission denied
Use Cases​

Listening to these events can be used for:

Account Status Monitoring: Track real-time account restriction changes and update UI/access controls accordingly
Trading Permission Management: Automatically enable or disable trading features based on account restrictions
BCAN Status Tracking: Monitor Virtual Account BCAN approval status for China A-share trading
Risk Management: Adjust risk controls and position management when liquidate-only restrictions are applied
Client Notification: Alert clients about account status changes requiring attention or action
Compliance Monitoring: Track account restrictions for regulatory and compliance purposes

## Extracted Tables

### Table 1

| Field | Type | Description |
| --- | --- | --- |
| id | string | Unique event identifier |
| position | string | Cursor for event replay; re-pushes subsequent events within the current business type. |
| event_type | string | Event type, fixed as ACCOUNT |
| timestamp | string | Event timestamp in ISO 8601 format |
| payload | object | Event payload data |

### Table 2

| Field | Type | Description |
| --- | --- | --- |
| account_id | string | Account id |
| account_number | string | Account number |
| account_type | string | Account type: CASH / MARGIN |
| restrictions | array | Array of current account restrictions (full snapshot) |
| update_time | string | Update timestamp in ISO 8601 format |
| biz_type | string | Business type, fixed as ACCOUNT_UPDATE |

### Table 3

| Restriction Code | Description |
| --- | --- |
| HK_STOCK_NO_TRADE | Hong Kong stocks - No trading allowed |
| HK_STOCK_LIQUIDATE_ONLY | Hong Kong stocks - Liquidate only (can only close positions) |
| US_STOCK_NO_TRADE | US stocks - No trading allowed |
| US_STOCK_LIQUIDATE_ONLY | US stocks - Liquidate only (can only close positions) |
| CN_STOCK_NO_TRADE | China A-shares - No trading allowed |
| CN_STOCK_LIQUIDATE_ONLY | China A-shares - Liquidate only (can only close positions) |

### Table 4

| Field | Type | Description |
| --- | --- | --- |
| id | string | Unique event identifier |
| position | string | Cursor for event replay; re-pushes subsequent events within the current business type. |
| event_type | string | Event type, fixed as ACCOUNT |
| timestamp | string | Event timestamp in ISO 8601 format |
| payload | object | Event payload data |

### Table 5

| Field | Type | Description |
| --- | --- | --- |
| account_id | string | Virtual Account id |
| account_number | string | Virtual Account number |
| account_type | string | Account type: CASH / MARGIN |
| type | string | BCAN type, currently only CN (China A-share) is supported |
| status | string | BCAN status: SUCCESS / FAILED |
| update_time | string | Update timestamp in ISO 8601 format |
| biz_type | string | Business type, fixed as VIRTUAL_ACCOUNT_BCAN_UPDATE |

### Table 6

| Status | Description |
| --- | --- |
| SUCCESS | BCAN code approved by exchange - Trading permission granted |
| FAILED | BCAN code rejected by exchange - Trading permission denied |

## Code Examples

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "ACCOUNT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {        "account_id": "036UUF6TQA8CD0KHJPEC000000",        "account_number": "5KT05001",        "account_type": "CASH",        "restrictions": [            "HK_STOCK_NO_TRADE",            "HK_STOCK_LIQUIDATE_ONLY",            "US_STOCK_NO_TRADE",            "US_STOCK_LIQUIDATE_ONLY",            "CN_STOCK_LIQUIDATE_ONLY",            "CN_STOCK_NO_TRADE"        ],        "update_time": "2025-03-29T07:02:33.200Z",        "biz_type": "ACCOUNT_UPDATE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "ACCOUNT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {        "account_id": "036UUF6TQA8CD0KHJPEC000000",        "account_number": "5KT05001",        "account_type": "CASH",        "restrictions": [            "HK_STOCK_NO_TRADE",            "HK_STOCK_LIQUIDATE_ONLY",            "US_STOCK_NO_TRADE",            "US_STOCK_LIQUIDATE_ONLY",            "CN_STOCK_LIQUIDATE_ONLY",            "CN_STOCK_NO_TRADE"        ],        "update_time": "2025-03-29T07:02:33.200Z",        "biz_type": "ACCOUNT_UPDATE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "ACCOUNT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {       "account_id": "O3I8NNB882S2BK7MF1ACJ5UTK9",       "account_number": "VA0000001",        "account_type": "MARGIN",        "type": "CN",        "status": "SUCCESS",        "update_time": "2025-03-29T07:02:33.200Z",        "biz_type": "VIRTUAL_ACCOUNT_BCAN_UPDATE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "ACCOUNT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {       "account_id": "O3I8NNB882S2BK7MF1ACJ5UTK9",       "account_number": "VA0000001",        "account_type": "MARGIN",        "type": "CN",        "status": "SUCCESS",        "update_time": "2025-03-29T07:02:33.200Z",        "biz_type": "VIRTUAL_ACCOUNT_BCAN_UPDATE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "ACCOUNT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {        "account_id": "O3I8NNB882S2BK7MF1ACJ5UTK9",        "account_number": "VA0000001",        "account_type": "MARGIN",        "type": "CN",        "status": "FAILED",        "update_time": "2025-03-29T07:02:33.200Z",        "biz_type": "VIRTUAL_ACCOUNT_BCAN_UPDATE"    }}
```

```json
{    "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",    "event_type": "ACCOUNT",    "position": "CJO1fxACGAAgADAB",    "timestamp": "2025-03-29T07:02:33.200Z",    "payload": {        "account_id": "O3I8NNB882S2BK7MF1ACJ5UTK9",        "account_number": "VA0000001",        "account_type": "MARGIN",        "type": "CN",        "status": "FAILED",        "update_time": "2025-03-29T07:02:33.200Z",        "biz_type": "VIRTUAL_ACCOUNT_BCAN_UPDATE"    }}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-account-events](https://developer.webull.hk/apis/docs/reference/custom/broker-account-events)
