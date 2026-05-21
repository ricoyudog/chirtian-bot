---
title: "Get Account Activities"
method: "GET"
endpoint: "/openapi/broker/activities/cash"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-activity-by-type"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Get Account Activities

**Method:** `GET`  
**Endpoint:** `/openapi/broker/activities/cash`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-activity-by-type](https://developer.webull.hk/apis/docs/reference/broker-api/broker-activity-by-type)

Broker APIActivitiesGet Account Activities
Get Account Activities
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/activities/cash

• Function description: Return account transaction activities records with details.

Request​
QUERY PARAMETERS
account_id
String
REQUIRED

Provide the target account id

Example: 943a9802f6c14983b3b4755c69c01717
activity_types
string

Possible values: [ADJUSTMENT, ALLOCATION, DEPOSIT, DIVIDENDS, EXECUTION, FEES, INTERESTS, JOURNAL, OPTION_EA, REORGANIZATION, SUBSCRIBE, TAX, TRADE, TRANSFER, WITHDRAW]

Account activity types

Example: TRADE,TRANSFER
start_time
String

Activity query start time, formats: yyyy-MM-dd'T'HH:mm:ss.SSSZ

Example: 2025-01-05T22:59:11.591Z
end_time
String

Activity query end time, formats: yyyy-MM-dd'T'HH:mm:ss.SSSZ

Example: 2025-01-05T23:59:11.591Z
last_activity_id
String

Last activity ID from the previous page for pagination.

Example: a1b2c3d4e5f6g7h8i9j0
page_size
Integer

Number of records to return per page. Default is 10. Supports integers in [1-200].

Example: 100
HEADER PARAMETERS
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
id
string
REQUIRED

Unique ID

Example: a1b2c3d4e5f6g7h8i9j0
account_id
string
REQUIRED

Account ID

Example: 943a9802f6c14983b3b4755c69c01717
account_number
string
REQUIRED

Account Number

Example: VA000000001
activity_type
string
REQUIRED

Activity Type
ADJUSTMENT - Adjustment Activity Type
ALLOCATION - Allocation Activity Type
DEPOSIT - Deposit Activity Type
DIVIDENDS - Dividends Activity Type
EXECUTION - Execution Activity Type
FEES - Fees Activity Type
INTERESTS - Interests Activity Type
JOURNAL - Journal Activity Type
OPTION_EA - Option EA Activity Type
REORGANIZATION - Reorganization Activity Type
SUBSCRIBE - Subscribe Activity Type
TAX - Tax Activity Type
TRADE - Trade Activity Type
TRANSFER - Transfer Activity Type
WITHDRAW - Withdraw Activity Type

Possible values: [ADJUSTMENT, ALLOCATION, DEPOSIT, DIVIDENDS, EXECUTION, FEES, INTERESTS, JOURNAL, OPTION_EA, REORGANIZATION, SUBSCRIBE, TAX, TRADE, TRANSFER, WITHDRAW]

Example: TRADE
activity_sub_type
string
REQUIRED

Activity Sub Type. Provides detailed classification under each ActivityType.
Multiple sub-types may share the same enum value but belong to different parent types.
For example, FOREIGN_TAX_WITHHELD can appear under DIVIDENDS, FEES, or TAX types.
NOT_SET - No sub type
CASH_ADJUSTMENT - Cash Adjustment Sub Type, super type is ADJUSTMENT
WIRE - Wire Deposit Sub Type, super type is DEPOSIT or WITHDRAW
TAX_WITHHOLD - Tax Withhold Dividend Sub Type, super type is DIVIDENDS
COLLECTION_FEE - Collection Fee Dividend Sub Type, super type is DIVIDENDS or INTERESTS
INCOME - Income Dividend Sub Type, super type is DIVIDENDS
PAYMENT_IN_LIEU - Payment In Lieu Dividend Sub Type, super type is DIVIDENDS
SCRIP_FEE - Scrip Fee Dividend Sub Type, super type is DIVIDENDS or REORGANIZATION
US_TAX_WITHHOLDING - US Tax Withholding Dividend or Tax Sub Type, super type is DIVIDENDS or TAX
CA_HANDLING_FEE - CA Handling Fee Sub Type, super type is DIVIDENDS or REORGANIZATION
FOREIGN_TAX_WITHHELD - Foreign Tax Withheld Sub Type, super type is DIVIDENDS or FEES or TAX
CASH_IN_LIEU - Cash In Lieu Sub Type, super type is DIVIDENDS or REORGANIZATION
ADJUSTMENT - Adjustment Dividend Sub Type, super type is DIVIDENDS
ADR - ADR Fees Sub Type, super type is FEES
IPO_SUBSCRIPTION_FEE - IPO Subscription Fee Sub Type, super type is FEES
TRANSACTION_FEES - Transaction Fees Sub Type, super type is FEES
CCASS_SETTLEMENT_FEE - CCASS Settlement Fee Sub Type, super type is FEES
JOURNAL_BETWEEN_ACCOUNTS - Journal Between Accounts Sub Type, super type is FEES or JOURNAL
CUSTODIAN_FEE - Custodian Fee Sub Type, super type is FEES
SETTLEMENT_FEES - Settlement Fees Sub Type, super type is FEES
TRANSFER_FOP - Transfer FOP Fees Sub Type, super type is FEES
FTT - FTT Fees Sub Type, super type is FEES
COMMISSION - Commission Fees Sub Type, super type is FEES
SYSTEM_FEE - System Fee Sub Type, super type is FEES
CORRESPONDENT_BILLING - Correspondent Billing Fees Sub Type, super type is FEES
CUSTODY_FEE - Custody Fee Sub Type, super type is FEES
STOCK_BORROW_INTEREST - Stock Borrow Interest Sub Type, super type is INTERESTS
DEBIT_CASH - Debit Cash Sub Type, super type is INTERESTS
IPO_FINANCING - IPO Financing Interest Sub Type, super type is INTERESTS
PAYMENT - Payment Interests Sub Type, super type is INTERESTS
ACCOUNT_MIGRATION - Account Migration Sub Type, super type is JOURNAL
IPO_REFUND - IPO Refund Sub Type, super type is JOURNAL
JOURNAL_BETWEEN_TYPES - Journal Between Types Sub Type, super type is JOURNAL
GIFTING - Gifting Sub Type, super type is JOURNAL
BANK_TRANSFER - Bank Transfer Sub Type, super type is JOURNAL
FX_EXCHANGE - FX Exchange Sub Type, super type is JOURNAL
CA_BREAK_RESOLVING - CA Break Resolving Sub Type, super type is JOURNAL
MARK_TO_MARKET - Mark To Market Sub Type, super type is JOURNAL
INV_DEPOSIT - INV Deposit Sub Type, super type is JOURNAL
IPO_SUBSCRIPTION - IPO Subscription Sub Type, super type is JOURNAL
FIXED_INCOME_SPREAD - Fixed Income Spread Sub Type, super type is JOURNAL
HK_CBBC_EXERCISE - HK CBBC Exercise Sub Type, super type is OPTION_EA
HK_CBBC_EXPIRATION - HK CBBC Expiration Sub Type, super type is OPTION_EA
HK_WARRANT_EXERCISE - HK Warrant Exercise Sub Type, super type is OPTION_EA
OPTION_EXERCISE - Option Exercise Sub Type, super type is OPTION_EA or TRADE
HK_INLINE_WARRANT_EXERCISE - HK Inline Warrant Exercise Sub Type, super type is OPTION_EA
OPTION_ASSIGNMENT - Option Assignment Sub Type, super type is OPTION_EA or TRADE
MERGER - Merger Sub Type, super type is REORGANIZATION
RIGHT_SUBSCRIPTION - Right Subscription Sub Type, super type is REORGANIZATION
CORP_ACTION_FEE - Corp Action Fee Sub Type, super type is REORGANIZATION
LIQUIDATION - Liquidation Sub Type, super type is REORGANIZATION
REDEMPTION - Redemption Sub Type, super type is REORGANIZATION
REPURCHASE - Repurchase Sub Type, super type is REORGANIZATION
FEE - Subscribe Fee Sub Type, super type is SUBSCRIBE
FEE_RETURN - Subscribe Fee Return Sub Type, super type is SUBSCRIBE
INTERNAL_TRANSFER - Internal Transfer Sub Type, super type is TRANSFER
DTC_OUT - DTC Out Sub Type, super type is TRANSFER
WIRE_FEE_LOCAL - Wire Fee Local Sub Type, super type is WITHDRAW

Possible values: [NOT_SET, CASH_ADJUSTMENT, WIRE, TAX_WITHHOLD, COLLECTION_FEE, INCOME, PAYMENT_IN_LIEU, SCRIP_FEE, US_TAX_WITHHOLDING, CA_HANDLING_FEE, FOREIGN_TAX_WITHHELD, CASH_IN_LIEU, ADJUSTMENT, ADR, IPO_SUBSCRIPTION_FEE, TRANSACTION_FEES, CCASS_SETTLEMENT_FEE, JOURNAL_BETWEEN_ACCOUNTS, CUSTODIAN_FEE, SETTLEMENT_FEES, TRANSFER_FOP, FTT, COMMISSION, SYSTEM_FEE, CORRESPONDENT_BILLING, CUSTODY_FEE, STOCK_BORROW_INTEREST, DEBIT_CASH, IPO_FINANCING, PAYMENT, ACCOUNT_MIGRATION, IPO_REFUND, JOURNAL_BETWEEN_TYPES, GIFTING, BANK_TRANSFER, FX_EXCHANGE, CA_BREAK_RESOLVING, MARK_TO_MARKET, INV_DEPOSIT, IPO_SUBSCRIPTION, FIXED_INCOME_SPREAD, HK_CBBC_EXERCISE, HK_CBBC_EXPIRATION, HK_WARRANT_EXERCISE, OPTION_EXERCISE, HK_INLINE_WARRANT_EXERCISE, OPTION_ASSIGNMENT, MERGER, RIGHT_SUBSCRIPTION, CORP_ACTION_FEE, LIQUIDATION, REDEMPTION, REPURCHASE, FEE, FEE_RETURN, INTERNAL_TRANSFER, DTC_OUT, WIRE_FEE_LOCAL]

Example: NOT_SET
currency
string
REQUIRED

Currency
CNH - RMB
HKD - Hong Kong Dollar
USD - US Dollar

Possible values: [CNH, HKD, USD]

Example: USD
market
string

Market Code
HK - Hong Kong Market
US - US Market
CN - China Market

Possible values: [HK, US, CN]

Example: US
symbol
string

Activity Symbol

Example: AAPL
trade_date
string
REQUIRED

Accounting date of the transaction (trade date), format: yyyy-MM-dd

Example: 2024-05-01
net_amount
string
REQUIRED

Net change amount of the transaction (positive for credit, negative for debit)

Example: 1500.0
biz_time
string
REQUIRED

Business event time when the transaction occurred

Example: 2024-05-01T10:15:30Z
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

	  'x-timestamp': '2026-05-17T14:38:09Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '39891879222730217593718401',

	  'x-version': 'v2',

	  'x-signature': '16812619102736977248577798'

	}

	conn.request("GET", "/openapi/broker/activities/cash?account_id=943a9802f6c14983b3b4755c69c01717&start_time=2025-01-05T22:59:11.591Z&end_time=2025-01-05T23:59:11.591Z&last_activity_id=a1b2c3d4e5f6g7h8i9j0&page_size=100", payload, headers)

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
x-app-key — headerREQUIRED
x-app-secret — headerREQUIRED
x-timestamp — headerREQUIRED
x-signature-version — headerREQUIRED
x-signature-algorithm — headerREQUIRED
x-signature-nonce — headerREQUIRED
x-version — headerREQUIRED
x-signature — headerREQUIRED
Show optional parameters
SEND API REQUEST
RESPONSE
CLEAR

Click the Send API Request button above and see the response here!

## Code Examples

```
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/activities/cash
```

```json
[  {    "id": "a1b2c3d4e5f6g7h8i9j0",    "account_id": "943a9802f6c14983b3b4755c69c01717",    "account_number": "VA000000001",    "activity_type": "TRADE",    "activity_sub_type": "NOT_SET",    "currency": "USD",    "market": "US",    "symbol": "AAPL",    "trade_date": "2024-05-01",    "net_amount": "1500.0",    "biz_time": "2024-05-01T10:15:30Z"  }]
```

```json
[  {    "id": "a1b2c3d4e5f6g7h8i9j0",    "account_id": "943a9802f6c14983b3b4755c69c01717",    "account_number": "VA000000001",    "activity_type": "TRADE",    "activity_sub_type": "NOT_SET",    "currency": "USD",    "market": "US",    "symbol": "AAPL",    "trade_date": "2024-05-01",    "net_amount": "1500.0",    "biz_time": "2024-05-01T10:15:30Z"  }]
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:09Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '39891879222730217593718401',  'x-version': 'v2',  'x-signature': '16812619102736977248577798'}conn.request("GET", "/openapi/broker/activities/cash?account_id=943a9802f6c14983b3b4755c69c01717&start_time=2025-01-05T22:59:11.591Z&end_time=2025-01-05T23:59:11.591Z&last_activity_id=a1b2c3d4e5f6g7h8i9j0&page_size=100", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:38:09Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '39891879222730217593718401',  'x-version': 'v2',  'x-signature': '16812619102736977248577798'}conn.request("GET", "/openapi/broker/activities/cash?account_id=943a9802f6c14983b3b4755c69c01717&start_time=2025-01-05T22:59:11.591Z&end_time=2025-01-05T23:59:11.591Z&last_activity_id=a1b2c3d4e5f6g7h8i9j0&page_size=100", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-activity-by-type](https://developer.webull.hk/apis/docs/reference/broker-api/broker-activity-by-type)
