---
title: "Get Corporate Actions Detail"
method: "GET"
endpoint: "/openapi/broker/instrument/corporate-actions/detail"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-corporate-actions-detail"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Get Corporate Actions Detail

**Method:** `GET`  
**Endpoint:** `/openapi/broker/instrument/corporate-actions/detail`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-corporate-actions-detail](https://developer.webull.hk/apis/docs/reference/broker-api/broker-corporate-actions-detail)

Broker APIInstrumentGet Corporate Actions Detail
Get Corporate Actions Detail
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/instrument/corporate_actions/detail

• Function description: Retrieve details information for corporate action events.

Request​
QUERY PARAMETERS
event_id
string
REQUIRED

Corporate Event Action ID

Example: CA123456789
HEADER PARAMETERS
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
event_id
string

Company Event ID

Example: 1234567890
event_type
string

Corporate Event Type
IDENTIFIER_CHANGE - Identifier-related changes to a security without economic impact, including symbol, exchange, ISIN, CUSIP, or instrument name changes
DIVIDEND - Dividend and distribution events, including cash dividend, stock dividend, optional dividend, and return of capital
REVERSE_SPLIT - Reverse stock split that consolidates shares and reduces the number of outstanding shares
FORWARD_SPLIT - Forward stock split that increases the number of outstanding shares
BONUS_ISSUE - Bonus issue of additional shares distributed to existing shareholders at no cost
RIGHTS_OFFERING - Rights offering allowing shareholders to subscribe for additional shares
DISTRIBUTION - Distribution of cash, securities, or other assets to shareholders
SPIN_OFF - Spin-off event where shares of a subsidiary or new entity are distributed to existing shareholders
UNIT_SPLIT - Unit split event affecting composite or unit-based securities
MERGER - Merger or acquisition event involving the combination of two or more entities
FULL_CALL - Full call redemption of the entire outstanding security issue
PARTIAL_CALL - Partial call redemption affecting only a portion of the outstanding issue
EXCHANGE - Exchange event where existing securities are exchanged for new securities or other consideration
DTC_EXIT - Event indicating a security is no longer eligible for DTC settlement or custody
LIQUIDATION - Liquidation event involving the winding up of an issuer and asset distribution
WORTHLESS - Worthless security event indicating the security has no residual value
ADR_GDR_TERMINATION - Termination of an ADR or GDR program
MATURITY - Maturity event where a security reaches its contractual maturity date
ADR_FEE - ADR fee charged to holders of American Depositary Receipts
CONVERSION - Conversion event where securities are converted into another class or form
OPEN_OFFER - Open offer allowing shareholders to subscribe for additional securities
PREFERENTIAL_OFFER - Preferential offer made to selected shareholders under specific terms
PERFORMANCE_COMPENSATION - Performance compensation event related to performance commitments, commonly in A-share markets
DELISTING - Delisting event where a security is removed from exchange trading

Possible values: [IDENTIFIER_CHANGE, DIVIDEND, REVERSE_SPLIT, FORWARD_SPLIT, BONUS_ISSUE, RIGHTS_OFFERING, DISTRIBUTION, SPIN_OFF, UNIT_SPLIT, MERGER, FULL_CALL, PARTIAL_CALL, EXCHANGE, DTC_EXIT, LIQUIDATION, WORTHLESS, ADR_GDR_TERMINATION, MATURITY, ADR_FEE, CONVERSION, OPEN_OFFER, PREFERENTIAL_OFFER, PERFORMANCE_COMPENSATION, DELISTING]

Example: DIVIDEND
event_version
string

Event Version

Example: 1
instrument_id
string

Instrument ID

Example: 943a9802f6c14983b3b4755c69c01717
category
string

Instrument Stock Category
US_STOCK - US stock,
HK_STOCK - HK stock,
CN_STOCK - China A share


Possible values: [US_STOCK, HK_STOCK, CN_STOCK]

Example: HK_STOCK
record_date
string

Record Date (YYYY-MM-DD)

Example: 2024-12-31
ex_date
string

Ex Date (YYYY-MM-DD)

Example: 2024-12-30
payment_date
string

Payment Date (YYYY-MM-DD)

Example: 2025-01-15
final_pay_date
string

Final Payment Date (YYYY-MM-DD)

Example: 2025-02-15
country_code
string

Country Code, ISO 3166-1 alpha-2 format

Example: HK
listing_country_of_code
string

Listing Country Code, ISO 3166-1 alpha-2 format

Example: HK
issuer_country_code
string

Issuer Country Code, ISO 3166-1 alpha-2 format

Example: HK
from
object

Event From Info. Position's instrument information

symbol
string

Symbol of the instrument

Example: 01029
cusip
string

CUSIP of the distributed security.

Example: 037833100
isin
string

ISIN of the distributed security.

Example: US0378331005
name
string

Name of the instrument

Example: IRC Limited
exchange
string

Exchange code

Example: CCC
to
object[]

Event To Info. Corporate action's target instrument information

option_number
string

Option Number. Identifier for the payout option

Example: 1
description
string

Description of the payout option

Example: Securities
default_option_flag
string

Default Option Flag. Indicates if the default payout option is exposed

Example: true
payouts
object[]

Payouts associated with this option

type
string

Payout Nature Type
DV - Dividend: Cash or stock distribution paid to shareholders
FR - Franked Dividend: Dividend paid with franking credits attached
IN - Interest: Interest income distribution
L2 - Long Term Capital Gains: Gains from disposal of assets held longer than one year
OT - Other: Other types of income or entitlement (see extended terms)
C - Cash: Cash payment (only applicable to events created prior to release 2)
PC - Cash/Principal/Return of Capital: Cash returned as principal or capital
PM - Premium: Additional amount paid over base entitlement
S - Securities: Distribution of securities instead of cash
ST - Short Term Capital Gains: Gains from disposal of assets held less than one year
SI - Sundry Income: Miscellaneous income distributions
UF - Unfranked Dividend: Dividend paid without franking credits
PI - Property Income Distribution: Income derived from property assets
TD - Tax Deferred: Income deferred for tax purposes
TE - Tax Exempted: Income exempted from taxation
FI - Foreign Income: Income sourced from foreign jurisdictions
CD - Capital gain on disposal of taxable property - Discounted
CO - Capital gain on disposal of taxable property - Other
CC - Capital gain on disposal of taxable property - Concessional
CN - Capital gain on disposal of non-taxable property
RT - Royalties: Payment received for intellectual property usage
TX - Tax Credit: Credit applied against tax liability
BP - Buy Permitted: Security is eligible for purchase under corporate action
CL - Cash in Lieu of Fractional Share: Cash payment for fractional share entitlement
DF - Drop Fraction: Fractional shares are dropped without compensation
EX - Extend and Retain Fractions: Fractional shares are retained and adjusted
NC - Round to Nearest Cent: Monetary amounts rounded to the nearest cent
NW - Round to Nearest Whole Number if .5 or above: Rounding rule for fractional shares
PR - Purchase Required: Mandatory purchase of securities as part of corporate action
RD - Round Down to Nearest Whole Number: Fractional shares rounded down
RU - Round Up to Nearest Whole Number: Fractional shares rounded up
SR - Sale Required: Mandatory sale of securities as part of corporate action
BU - Round up: Generic rounding up rule
BC - Beneficial Owner Cash in Lieu: Cash payment to beneficial owner for fractional share
BD - Beneficial Owner Round Down: Fractional shares of beneficial owner rounded down
CT - Security Convert To Cash: Conversion of security into cash (used for tokenized assets)

Possible values: [DV, FR, IN, L2, OT, C, PC, PM, S, ST, SI, UF, PI, TD, TE, FI, CD, CO, CC, CN, RT, TX, BP, CL, DF, EX, NC, NW, PR, RD, RU, SR, BU, BC, BD, CT]

Example: DV
pay_type
string

Payout Delivery Type
CASH - Cash settlement
SECURITY - Security settlement (stock, right, warrant, etc.)
SCRIP - Scrip dividend (dividend paid in shares instead of cash)
SECURITY_AND_CASH - Combination of security and cash (logical type, not for persistence)

Possible values: [CASH, SECURITY, SCRIP, SECURITY_AND_CASH]

Example: CASH
payout_number
int32

Sequence number of the payout within the same option. Used for ordering and identification.

Example: 1
adr_fee_rate
string

ADR fee rate applied to this payout, if applicable.

Example: 0.02
fraction_share_rule
string

Fraction Share Rule
NONE - No special handling for fractional shares
ROUND_DOWN - Round down fractional shares
ROUND_UP - Round up fractional shares
CASH_IN_LIEU - Cash in lieu for fractional shares
DISTRIBUTION - Fractional share distribution
STANDARD - Standard rounding for fractional shares

Possible values: [NONE, ROUND_DOWN, ROUND_UP, CASH_IN_LIEU, DISTRIBUTION, STANDARD]

Example: ROUND_DOWN
cancellation_fee
string

Cancellation fee rate applied if the corporate action is cancelled.

Example: 0
issuance_fee
string

Issuance fee rate applied for newly issued securities.

Example: 0
tax_status
string

IRS income classification for tax reporting purposes.

Example: 0001
currency
string

Currency of the cash payout. Applicable only when payType involves CASH.

Example: USD
amount
string

Cash amount paid per share held. Applicable only when payType involves CASH.

Example: 0.85
withholding_tax_rate
string

Withholding tax rate applied to the cash payout.

Example: 0.15
symbol
string

Trading symbol of the distributed security.

Example: AAPL
cusip
string

CUSIP of the distributed security.

Example: 037833100
isin
string

ISIN of the distributed security.

Example: US0378331005
name
string

Name of the distributed security.

Example: Apple Inc.
exchange
string

Exchange where the distributed security is listed.

Example: CCC
from_ratio
string

Original holding quantity used as the base for ratio calculation.

Example: 10
to_ratio
string

Distributed quantity received for the given base holding.

Example: 1
cash_in_lieu_price
string

Cash-in-lieu price used to settle fractional shares.

Example: 125.3
reinvest_price
string

Reinvestment price used for scrip dividend calculation.

Example: 132.5
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

	  'x-timestamp': '2026-05-17T14:38:06Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '11800669941621604151172890',

	  'x-version': 'v2',

	  'x-signature': '84120985435864122628460684'

	}

	conn.request("GET", "/openapi/broker/instrument/corporate_actions/detail?event_id=CA123456789", payload, headers)

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
event_id — queryREQUIRED
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
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/instrument/corporate_actions/detail
```

```json
{  "event_id": "1234567890",  "event_type": "DIVIDEND",  "event_version": "1",  "instrument_id": "943a9802f6c14983b3b4755c69c01717",  "category": "HK_STOCK",  "record_date": "2024-12-31",  "ex_date": "2024-12-30",  "payment_date": "2025-01-15",  "final_pay_date": "2025-02-15",  "country_code": "HK",  "listing_country_of_code": "HK",  "issuer_country_code": "HK",  "from": {    "symbol": "01029",    "cusip": "037833100",    "isin": "US0378331005",    "name": "IRC Limited",    "exchange": "CCC"  },  "to": [    {      "option_number": "1",      "description": "Securities",      "default_option_flag": "true",      "payouts": [        {          "type": "DV",          "pay_type": "CASH",          "payout_number": 1,          "adr_fee_rate": "0.02",          "fraction_share_rule": "ROUND_DOWN",          "cancellation_fee": "0",          "issuance_fee": "0",          "tax_status": "0001",          "currency": "USD",          "amount": "0.85",          "withholding_tax_rate": "0.15",          "symbol": "AAPL",          "cusip": "037833100",          "isin": "US0378331005",          "name": "Apple Inc.",          "exchange": "CCC",          "from_ratio": "10",          "to_ratio": "1",          "cash_in_lieu_price": "125.3",          "reinvest_price": "132.5"        }      ]    }  ]}
```

```json
{  "event_id": "1234567890",  "event_type": "DIVIDEND",  "event_version": "1",  "instrument_id": "943a9802f6c14983b3b4755c69c01717",  "category": "HK_STOCK",  "record_date": "2024-12-31",  "ex_date": "2024-12-30",  "payment_date": "2025-01-15",  "final_pay_date": "2025-02-15",  "country_code": "HK",  "listing_country_of_code": "HK",  "issuer_country_code": "HK",  "from": {    "symbol": "01029",    "cusip": "037833100",    "isin": "US0378331005",    "name": "IRC Limited",    "exchange": "CCC"  },  "to": [    {      "option_number": "1",      "description": "Securities",      "default_option_flag": "true",      "payouts": [        {          "type": "DV",          "pay_type": "CASH",          "payout_number": 1,          "adr_fee_rate": "0.02",          "fraction_share_rule": "ROUND_DOWN",          "cancellation_fee": "0",          "issuance_fee": "0",          "tax_status": "0001",          "currency": "USD",          "amount": "0.85",          "withholding_tax_rate": "0.15",          "symbol": "AAPL",          "cusip": "037833100",          "isin": "US0378331005",          "name": "Apple Inc.",          "exchange": "CCC",          "from_ratio": "10",          "to_ratio": "1",          "cash_in_lieu_price": "125.3",          "reinvest_price": "132.5"        }      ]    }  ]}
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:06Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '11800669941621604151172890',  'x-version': 'v2',  'x-signature': '84120985435864122628460684'}conn.request("GET", "/openapi/broker/instrument/corporate_actions/detail?event_id=CA123456789", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:06Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '11800669941621604151172890',  'x-version': 'v2',  'x-signature': '84120985435864122628460684'}conn.request("GET", "/openapi/broker/instrument/corporate_actions/detail?event_id=CA123456789", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-corporate-actions-detail](https://developer.webull.hk/apis/docs/reference/broker-api/broker-corporate-actions-detail)
