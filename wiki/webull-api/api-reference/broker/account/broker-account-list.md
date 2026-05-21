---
title: "List Virtual Accounts"
method: "GET"
endpoint: "/openapi/broker/account/nd/list"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-list"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# List Virtual Accounts

**Method:** `GET`  
**Endpoint:** `/openapi/broker/account/nd/list`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-list](https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-list)

Broker APIAccount (ND)List Virtual Accounts
List Virtual Accounts
Ask AI
GET
https://hk-broker-api.uat.webullbroker.com/openapi/broker/account/nd/list

• Function description: Return Virtual Account list with pagination support.

Request​
QUERY PARAMETERS
last_account_id
String

Last Virtual Account ID from the previous page for pagination. For the first page, this can be omitted or set to an empty string.

Example: 943a9802f6c14983b3b4755c69c01717
start_time
String

Inclusive start time for the query. formats: yyyy-MM-dd'T'HH:mm:ss.SSSZ

Example: 2025-01-05T22:59:11.591Z
end_time
String

Inclusive end time for the query, formats: yyyy-MM-dd'T'HH:mm:ss.SSSZ

Example: 2025-01-06T22:59:11.591Z
page_size
String

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
belong_account_number
string
REQUIRED

Belonging Account Number, the master account belong to

Example: FV000123
belong_account_id
string
REQUIRED

Belonging Account ID, the master account belong to

Example: 4942451778e14177b9ab066b9662bda9
account_number
string
REQUIRED

Account Number

Example: VA000000001
account_id
string
REQUIRED

Account ID

Example: 943a9802f6c14983b3b4755c69c01717
account_type
string
REQUIRED

Account Type
CASH: Cash Account
MARGIN: Margin Account

Possible values: [CASH, MARGIN]

Example: CASH
account_status
string
REQUIRED

Account Status
CREATED - Account is created but not yet active
ACTIVE - Account is active and operational
SUSPENDED - Account temporarily suspended
RESTRICTED - Account restricted, limited operations
FROZEN - Account frozen due to compliance or risk
CLOSED - Account permanently closed

Possible values: [CREATED, ACTIVE, SUSPENDED, RESTRICTED, FROZEN, CLOSED]

Example: CREATED
trading_permissions
string[]
REQUIRED

Trading Permissions

Possible values: [US_STOCK_NORMAL, HK_STOCK_NORMAL, CN_STOCK_NORMAL]

commission_code
string

Commission Code

Example: STANDARD_COMMISSION
w8ben_info
object

W-8BEN Information,When trading U.S. stocks in the account, this information needs to be supplemented.

treaty_country
string
REQUIRED

Country of Treaty, using ISO 3166-1 alpha-2 format

Example: HK
tax_id
string
REQUIRED

Tax Identification Number

Example: 123-45-6789
sign_date
string
REQUIRED

W-8BEN Form Sign Date, format: YYYY-MM-DD

Example: 2026-01-01
china_connect_investor_info
object

China Connect Investor Information,This information only needs to be supplemented when trading Chinese A-shares.

first_name
string
REQUIRED

First Name

Example: John
last_name
string
REQUIRED

Last Name

Example: Doe
middle_name
string

Middle Name

Example: Michael
id_type
string
REQUIRED

ID Type
ID_CARD: Identification Card
PASSPORT: Passport
CERT_INCORP: Certificate of Incorporation
LEI: Legal Entity Identifier
OTHER_OFFICIAL_ID_DOC: Other Official ID Document

Possible values: [ID_CARD, PASSPORT, CERT_INCORP, LEI, OTHER_OFFICIAL_ID_DOC]

Example: ID_CARD
id_number
string
REQUIRED

ID Number

Example: X12345678
country_of_issuance
string
REQUIRED

Country of Issuance, using ISO 3166-1 alpha-2 format

Example: HK
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

	  'x-timestamp': '2026-05-17T14:37:54Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '21149386912231922736928684',

	  'x-version': 'v2',

	  'x-signature': '96369035735393125465580262'

	}

	conn.request("GET", "/openapi/broker/account/nd/list?last_account_id=943a9802f6c14983b3b4755c69c01717&start_time=2025-01-05T22:59:11.591Z&end_time=2025-01-06T22:59:11.591Z&page_size=100", payload, headers)

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
Show optional parameters
SEND API REQUEST
RESPONSE
CLEAR

Click the Send API Request button above and see the response here!

## Code Examples

```
GET https://hk-broker-api.uat.webullbroker.com/openapi/broker/account/nd/list
```

```json
[  {    "belong_account_number": "FV000123",    "belong_account_id": "4942451778e14177b9ab066b9662bda9",    "account_number": "VA000000001",    "account_id": "943a9802f6c14983b3b4755c69c01717",    "account_type": "CASH",    "account_status": "CREATED",    "trading_permissions": [      "US_STOCK_NORMAL",      "US_STOCK_FRACTIONAL",      "US_STOCK_OVERNIGHT",      "HK_STOCK_NORMAL",      "HK_STOCK_FRACTIONAL"    ],    "commission_code": "STANDARD_COMMISSION",    "w8ben_info": {      "treaty_country": "HK",      "tax_id": "123-45-6789",      "sign_date": "2026-01-01"    },    "china_connect_investor_info": {      "first_name": "John",      "last_name": "Doe",      "middle_name": "Michael",      "id_type": "ID_CARD",      "id_number": "X12345678",      "country_of_issuance": "HK"    }  }]
```

```json
[  {    "belong_account_number": "FV000123",    "belong_account_id": "4942451778e14177b9ab066b9662bda9",    "account_number": "VA000000001",    "account_id": "943a9802f6c14983b3b4755c69c01717",    "account_type": "CASH",    "account_status": "CREATED",    "trading_permissions": [      "US_STOCK_NORMAL",      "US_STOCK_FRACTIONAL",      "US_STOCK_OVERNIGHT",      "HK_STOCK_NORMAL",      "HK_STOCK_FRACTIONAL"    ],    "commission_code": "STANDARD_COMMISSION",    "w8ben_info": {      "treaty_country": "HK",      "tax_id": "123-45-6789",      "sign_date": "2026-01-01"    },    "china_connect_investor_info": {      "first_name": "John",      "last_name": "Doe",      "middle_name": "Michael",      "id_type": "ID_CARD",      "id_number": "X12345678",      "country_of_issuance": "HK"    }  }]
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:37:54Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '21149386912231922736928684',  'x-version': 'v2',  'x-signature': '96369035735393125465580262'}conn.request("GET", "/openapi/broker/account/nd/list?last_account_id=943a9802f6c14983b3b4755c69c01717&start_time=2025-01-05T22:59:11.591Z&end_time=2025-01-06T22:59:11.591Z&page_size=100", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = ''headers = {  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:37:54Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '21149386912231922736928684',  'x-version': 'v2',  'x-signature': '96369035735393125465580262'}conn.request("GET", "/openapi/broker/account/nd/list?last_account_id=943a9802f6c14983b3b4755c69c01717&start_time=2025-01-05T22:59:11.591Z&end_time=2025-01-06T22:59:11.591Z&page_size=100", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-list](https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-list)
