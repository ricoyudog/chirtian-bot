---
title: "Corporate Actions Events"
method: "gRPC"
endpoint: "broker-corporate-actions-events"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/custom/broker-ca-events"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Corporate Actions Events

**Protocol:** gRPC Stream  
**Event:** `broker-corporate-actions-events`  
**Host:** `events-api.webull.hk` (production) / `events-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-ca-events](https://developer.webull.hk/apis/docs/reference/custom/broker-ca-events)

Broker APIEventsCorporate Actions Events
Corporate Actions Events
Ask AI

Receive notifications for corporate action events, including:

Identifier changes (symbol, CUSIP, ISIN changes)
Dividends (cash dividends, stock dividends)
Stock splits and reverse splits
Mergers and acquisitions
Rights offerings
Other corporate action events
Corporate Action Event​

This event is triggered when a corporate action is announced or updated.

CA Event
Event Structure​
{
  "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",
  "event_type": "INSTRUMENT",
  "position": "CJO1fxACGAAgADAB",
  "timestamp": "2025-03-29T07:02:33.200Z",
  "payload": {
    "event_id": "925299289_1569116747",
    "event_type": "DIVIDEND",
    "event_version": "1768542619139",
    "instrument_id": "925299289",
    "category": "US_STOCK",
    "record_date": "2026-01-14",
    "ex_date": "2026-01-13",
    "payment_date": "2026-01-15",
    "final_pay_date": "2026-01-15",
    "country_code": "US",
    "listing_country_of_code": "US",
    "issuer_country_code": "CA",
    "from": {
      "symbol": "AFRRF",
      "cusip": "00111F102",
      "isin": "CA00111F1027",
      "name": "AFR NUVENTURE RESOURCES INC",
      "exchange": "PSGM"
    },
    "to": [
      {
        "option_number": "2",
        "description": "Cash",
        "default_option_flag": "true",
        "payouts": [
          {
            "type": "DV",
            "pay_type": "CASH",
            "payout_number": 1,
            "adr_fee_rate": "0.003",
            "fraction_share_rule": "NONE",
            "cancellation_fee": "0",
            "issuance_fee": "0",
            "currency": "USD",
            "amount": "0.176885",
            "withholding_tax_rate": "0.011"
          }
        ]
      }
    ],
    "biz_type": "CA_EVENT"
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
eventId	string	Unique corporate action event identifier
event_type	string	Corporate action type (e.g., IDENTIFIER_CHANGE, DIVIDEND, SPLIT)
event_version	string	Event version number, increments with updates. Higher numbers represent newer versions
instrument_id	string	Instrument identifier affected by the corporate action
category	string	Instrument category (e.g., US_STOCK)
record_date	string	Record date for the corporate action
ex_date	string	Ex-dividend or ex-date
payment_date	string	Payment date
final_pay_date	string	Final payment date
country_code	string	Country code
listing_country_of_code	string	Listing country code
issuer_country_code	string	Issuer country code
from	object	Original instrument information
to	array	Target payment options (multiple options may exist)
biz_type	string	Business type, fixed as CA_EVENT
From Object Fields​
Field	Type	Description
symbol	string	Original instrument symbol
cusip	string	Original CUSIP identifier
isin	string	Original ISIN identifier
name	string	Original instrument name
exchange	string	Original exchange code
To Array - Option Fields​

Each option represents a payment choice available to shareholders:

Field	Type	Description
option_number	string	Option number identifier
description	string	Option description
default_option_flag	string	Whether this is the default option: 1 (yes) / 0 (no)
payouts	array	Array of payout details for this option
INFO
Multiple payment options may be available, with one marked as the default option
Currently, only the default option is provided in the event
Payout Fields​

Each payout represents a specific payment type within an option. A single option may contain multiple payouts (e.g., cash + security).

Common Fields (All Payment Types)​

These fields are available for all payment types (CASH, SECURITY, SCRIP):

Field	Type	Description
type	string	Payment category code (e.g., DV, FR, IN)
pay_type	string	Payment type: CASH, SECURITY, or SCRIP
payout_number	string	Payout number within the option
adr_fee_rate	string	ADR fee rate
fraction_share_rule	string	Fractional share handling: ROUND_DOWN, ROUND_UP, CASH_IN_LIEU
cancellation_fee	string	Cancellation fee rate
issuance_fee	string	Issuance fee rate
tax_status	string	IRS income type code
Cash Payment Specific Fields (pay_type: CASH)​

Additional fields for cash payments:

Field	Type	Description
currency	string	Payment currency
amount	string	Payment amount per share
withholding_tax_rate	string	Withholding tax rate
Security/SCRIP Common Fields (pay_type: SECURITY or SCRIP)​

These fields are shared by both security and SCRIP payments:

Field	Type	Description
symbol	string	Payout instrument symbol
cusip	string	Payout instrument CUSIP
isin	string	Payout instrument ISIN
name	string	Payout instrument name
exchange	string	Payout instrument exchange
from_ratio	string	Original share ratio
to_ratio	string	Target share ratio
cash_in_lieu_price	string	Cash in lieu price for fractional shares
currency	string	Payment currency
Security Payment Specific Fields (pay_type: SECURITY)​

No additional security-specific fields beyond the common Security/SCRIP fields.

SCRIP Payment Specific Fields (pay_type: SCRIP)​

SCRIP dividends (dividend reinvestment) are primarily available for Hong Kong stocks.

Field	Type	Description
reinvest_price	string	Reinvestment price per share
amount	string	Payment amount per share
Payout Type Examples​
Example 1: Cash Dividend​
{
    "type": "DV",
    "pay_type": "CASH",
    "payout_number": "1",
    "currency": "USD",
    "amount": "0.25",
    "withholding_tax_rate": "0.15"
}

Example 2: Stock Dividend (10 shares → 1 share)​
{
    "type": "DV",
    "pay_type": "SECURITY",
    "payout_number": "1",
    "symbol": "AAPL",
    "from_ratio": "10",
    "to_ratio": "1",
    "fraction_share_rule": "CASH_IN_LIEU",
    "cash_in_lieu_price": "150.00"
}

Example 3: SCRIP Dividend (Reinvestment)​
{
    "type": "DV",
    "pay_type": "SCRIP",
    "payout_number": "1",
    "symbol": "0700.HK",
    "reinvest_price": "350.00",
    "from_ratio": "1",
    "to_ratio": "1"
}

Example 4: Mixed Payout (Cash + Security)​

An option may contain multiple payouts:

{
    "option_number": "1",
    "description": "Cash and Stock",
    "default_option_flag": "1",
    "payouts": [
        {
            "type": "DV",
            "pay_type": "CASH",
            "payout_number": "1",
            "currency": "USD",
            "amount": "0.10"
        },
        {
            "type": "DV",
            "pay_type": "SECURITY",
            "payout_number": "2",
            "symbol": "AAPL",
            "from_ratio": "20",
            "to_ratio": "1"
        }
    ]
}

Use Cases​

Listening to this event can be used for:

Corporate Action Tracking: Monitor all corporate actions affecting held positions
Dividend Processing: Automatically process dividend payments and reinvestments
Position Adjustment: Update positions based on stock splits, mergers, or conversions
Client Notification: Alert clients about upcoming corporate actions requiring action
Tax Reporting: Track withholding taxes and taxable events for reporting purposes
Symbol Changes: Update instrument identifiers when symbols, CUSIPs, or ISINs change

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
| eventId | string | Unique corporate action event identifier |
| event_type | string | Corporate action type (e.g., IDENTIFIER_CHANGE, DIVIDEND, SPLIT) |
| event_version | string | Event version number, increments with updates. Higher numbers represent newer versions |
| instrument_id | string | Instrument identifier affected by the corporate action |
| category | string | Instrument category (e.g., US_STOCK) |
| record_date | string | Record date for the corporate action |
| ex_date | string | Ex-dividend or ex-date |
| payment_date | string | Payment date |
| final_pay_date | string | Final payment date |
| country_code | string | Country code |
| listing_country_of_code | string | Listing country code |
| issuer_country_code | string | Issuer country code |
| from | object | Original instrument information |
| to | array | Target payment options (multiple options may exist) |
| biz_type | string | Business type, fixed as CA_EVENT |

### Table 3

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Original instrument symbol |
| cusip | string | Original CUSIP identifier |
| isin | string | Original ISIN identifier |
| name | string | Original instrument name |
| exchange | string | Original exchange code |

### Table 4

| Field | Type | Description |
| --- | --- | --- |
| option_number | string | Option number identifier |
| description | string | Option description |
| default_option_flag | string | Whether this is the default option: 1 (yes) / 0 (no) |
| payouts | array | Array of payout details for this option |

### Table 5

| Field | Type | Description |
| --- | --- | --- |
| type | string | Payment category code (e.g., DV, FR, IN) |
| pay_type | string | Payment type: CASH, SECURITY, or SCRIP |
| payout_number | string | Payout number within the option |
| adr_fee_rate | string | ADR fee rate |
| fraction_share_rule | string | Fractional share handling: ROUND_DOWN, ROUND_UP, CASH_IN_LIEU |
| cancellation_fee | string | Cancellation fee rate |
| issuance_fee | string | Issuance fee rate |
| tax_status | string | IRS income type code |

### Table 6

| Field | Type | Description |
| --- | --- | --- |
| currency | string | Payment currency |
| amount | string | Payment amount per share |
| withholding_tax_rate | string | Withholding tax rate |

### Table 7

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Payout instrument symbol |
| cusip | string | Payout instrument CUSIP |
| isin | string | Payout instrument ISIN |
| name | string | Payout instrument name |
| exchange | string | Payout instrument exchange |
| from_ratio | string | Original share ratio |
| to_ratio | string | Target share ratio |
| cash_in_lieu_price | string | Cash in lieu price for fractional shares |
| currency | string | Payment currency |

### Table 8

| Field | Type | Description |
| --- | --- | --- |
| reinvest_price | string | Reinvestment price per share |
| amount | string | Payment amount per share |

## Code Examples

```json
{  "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",  "event_type": "INSTRUMENT",  "position": "CJO1fxACGAAgADAB",  "timestamp": "2025-03-29T07:02:33.200Z",  "payload": {    "event_id": "925299289_1569116747",    "event_type": "DIVIDEND",    "event_version": "1768542619139",    "instrument_id": "925299289",    "category": "US_STOCK",    "record_date": "2026-01-14",    "ex_date": "2026-01-13",    "payment_date": "2026-01-15",    "final_pay_date": "2026-01-15",    "country_code": "US",    "listing_country_of_code": "US",    "issuer_country_code": "CA",    "from": {      "symbol": "AFRRF",      "cusip": "00111F102",      "isin": "CA00111F1027",      "name": "AFR NUVENTURE RESOURCES INC",      "exchange": "PSGM"    },    "to": [      {        "option_number": "2",        "description": "Cash",        "default_option_flag": "true",        "payouts": [          {            "type": "DV",            "pay_type": "CASH",            "payout_number": 1,            "adr_fee_rate": "0.003",            "fraction_share_rule": "NONE",            "cancellation_fee": "0",            "issuance_fee": "0",            "currency": "USD",            "amount": "0.176885",            "withholding_tax_rate": "0.011"          }        ]      }    ],    "biz_type": "CA_EVENT"  }}
```

```json
{  "id": "event_c4b2c210-ce32-41d4-a9a1-cfad4fdf191c",  "event_type": "INSTRUMENT",  "position": "CJO1fxACGAAgADAB",  "timestamp": "2025-03-29T07:02:33.200Z",  "payload": {    "event_id": "925299289_1569116747",    "event_type": "DIVIDEND",    "event_version": "1768542619139",    "instrument_id": "925299289",    "category": "US_STOCK",    "record_date": "2026-01-14",    "ex_date": "2026-01-13",    "payment_date": "2026-01-15",    "final_pay_date": "2026-01-15",    "country_code": "US",    "listing_country_of_code": "US",    "issuer_country_code": "CA",    "from": {      "symbol": "AFRRF",      "cusip": "00111F102",      "isin": "CA00111F1027",      "name": "AFR NUVENTURE RESOURCES INC",      "exchange": "PSGM"    },    "to": [      {        "option_number": "2",        "description": "Cash",        "default_option_flag": "true",        "payouts": [          {            "type": "DV",            "pay_type": "CASH",            "payout_number": 1,            "adr_fee_rate": "0.003",            "fraction_share_rule": "NONE",            "cancellation_fee": "0",            "issuance_fee": "0",            "currency": "USD",            "amount": "0.176885",            "withholding_tax_rate": "0.011"          }        ]      }    ],    "biz_type": "CA_EVENT"  }}
```

```json
{    "type": "DV",    "pay_type": "CASH",    "payout_number": "1",    "currency": "USD",    "amount": "0.25",    "withholding_tax_rate": "0.15"}
```

```json
{    "type": "DV",    "pay_type": "CASH",    "payout_number": "1",    "currency": "USD",    "amount": "0.25",    "withholding_tax_rate": "0.15"}
```

```json
{    "type": "DV",    "pay_type": "SECURITY",    "payout_number": "1",    "symbol": "AAPL",    "from_ratio": "10",    "to_ratio": "1",    "fraction_share_rule": "CASH_IN_LIEU",    "cash_in_lieu_price": "150.00"}
```

```json
{    "type": "DV",    "pay_type": "SECURITY",    "payout_number": "1",    "symbol": "AAPL",    "from_ratio": "10",    "to_ratio": "1",    "fraction_share_rule": "CASH_IN_LIEU",    "cash_in_lieu_price": "150.00"}
```

```json
{    "type": "DV",    "pay_type": "SCRIP",    "payout_number": "1",    "symbol": "0700.HK",    "reinvest_price": "350.00",    "from_ratio": "1",    "to_ratio": "1"}
```

```json
{    "type": "DV",    "pay_type": "SCRIP",    "payout_number": "1",    "symbol": "0700.HK",    "reinvest_price": "350.00",    "from_ratio": "1",    "to_ratio": "1"}
```

```json
{    "option_number": "1",    "description": "Cash and Stock",    "default_option_flag": "1",    "payouts": [        {            "type": "DV",            "pay_type": "CASH",            "payout_number": "1",            "currency": "USD",            "amount": "0.10"        },        {            "type": "DV",            "pay_type": "SECURITY",            "payout_number": "2",            "symbol": "AAPL",            "from_ratio": "20",            "to_ratio": "1"        }    ]}
```

```json
{    "option_number": "1",    "description": "Cash and Stock",    "default_option_flag": "1",    "payouts": [        {            "type": "DV",            "pay_type": "CASH",            "payout_number": "1",            "currency": "USD",            "amount": "0.10"        },        {            "type": "DV",            "pay_type": "SECURITY",            "payout_number": "2",            "symbol": "AAPL",            "from_ratio": "20",            "to_ratio": "1"        }    ]}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/custom/broker-ca-events](https://developer.webull.hk/apis/docs/reference/custom/broker-ca-events)
