---
title: "Update Virtual Account"
method: "POST"
endpoint: "/openapi/broker/account/nd/update"
rate_limit: "See Webull API documentation"
source: "https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-update"
updated: "2026-05-17"
tags: [webull, api-reference, broker]
---

# Update Virtual Account

**Method:** `POST`  
**Endpoint:** `/openapi/broker/account/nd/update`  
**Host:** `broker-api.webull.hk` (production) / `broker-api.sandbox.webull.hk` (sandbox)  
**Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-update](https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-update)

Broker APIAccount (ND)Update Virtual Account
Update Virtual Account
Ask AI
POST
https://hk-broker-api.uat.webullbroker.com/openapi/broker/account/nd/update

• Function description: Update Virtual Account information for existing virtual account.

Request​
HEADER PARAMETERS
APPLICATION/JSON
BODYREQUIRED
client_request_id
string
REQUIRED

Client Request ID, unique for each request.
Maximum length is 32 characters.
Allowed characters: letters (A–Z, a–z), digits (0–9), hyphen (-), underscore (_).

Example: LJIS16BACHQG9LPP44L9IQHGAB
account_id
string
REQUIRED

VA Account ID to be updated

Example: 943a9802f6c14983b3b4755c69c01717
trading_permissions
string[]

Trading Permissions for the VA account, list of permission codes

Possible values: [US_STOCK_NORMAL, HK_STOCK_NORMAL, CN_STOCK_NORMAL]

Example: ["US_STOCK_NORMAL"]
commission_code
string

Commission Code for the VA account, determining the commission structure

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
Responses​
200

OK

APPLICATION/JSON
Schema
Example
SCHEMA
client_request_id
string
REQUIRED

Create VA Account Request ID

Example: LJIS16BACHQG9LPP44L9IQHGAB
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

	  "client_request_id": "LJIS16BACHQG9LPP44L9IQHGAB",

	  "account_id": "943a9802f6c14983b3b4755c69c01717",

	  "trading_permissions": [

	    "US_STOCK_NORMAL"

	  ],

	  "commission_code": "STANDARD_COMMISSION",

	  "w8ben_info": {

	    "treaty_country": "HK",

	    "tax_id": "123-45-6789",

	    "sign_date": "2026-01-01"

	  },

	  "china_connect_investor_info": {

	    "first_name": "John",

	    "last_name": "Doe",

	    "middle_name": "Michael",

	    "id_type": "ID_CARD",

	    "id_number": "X12345678",

	    "country_of_issuance": "HK"

	  }

	})

	headers = {

	  'Content-Type': 'application/json',

	  'Accept': 'application/json',

	  'x-timestamp': '2026-05-17T14:37:48Z',

	  'x-signature-version': '1.0',

	  'x-signature-algorithm': 'HMAC-SHA1',

	  'x-signature-nonce': '36640481529649198363378165',

	  'x-version': 'v2',

	  'x-signature': '04478027709342750176066248'

	}

	conn.request("POST", "/openapi/broker/account/nd/update", payload, headers)

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
  "client_request_id": "LJIS16BACHQG9LPP44L9IQHGAB",
  "account_id": "943a9802f6c14983b3b4755c69c01717",
  "trading_permissions": [
    "US_STOCK_NORMAL"
  ],
  "commission_code": "STANDARD_COMMISSION",
  "w8ben_info": {
    "treaty_country": "HK",
    "tax_id": "123-45-6789",
    "sign_date": "2026-01-01"
  },
  "china_connect_investor_info": {
    "first_name": "John",
    "last_name": "Doe",
    "middle_name": "Michael",
    "id_type": "ID_CARD",
    "id_number": "X12345678",
    "country_of_issuance": "HK"
  }
}

SEND API REQUEST
RESPONSE
CLEAR

Click the Send API Request button above and see the response here!

## Code Examples

```
POST https://hk-broker-api.uat.webullbroker.com/openapi/broker/account/nd/update
```

```json
{  "client_request_id": "LJIS16BACHQG9LPP44L9IQHGAB",  "account_number": "VA000000001",  "account_id": "943a9802f6c14983b3b4755c69c01717",  "account_status": "CREATED"}
```

```json
{  "client_request_id": "LJIS16BACHQG9LPP44L9IQHGAB",  "account_number": "VA000000001",  "account_id": "943a9802f6c14983b3b4755c69c01717",  "account_status": "CREATED"}
```

```json
import http.clientimport jsonconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = json.dumps({  "client_request_id": "LJIS16BACHQG9LPP44L9IQHGAB",  "account_id": "943a9802f6c14983b3b4755c69c01717",  "trading_permissions": [    "US_STOCK_NORMAL"  ],  "commission_code": "STANDARD_COMMISSION",  "w8ben_info": {    "treaty_country": "HK",    "tax_id": "123-45-6789",    "sign_date": "2026-01-01"  },  "china_connect_investor_info": {    "first_name": "John",    "last_name": "Doe",    "middle_name": "Michael",    "id_type": "ID_CARD",    "id_number": "X12345678",    "country_of_issuance": "HK"  }})headers = {  'Content-Type': 'application/json',  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:37:48Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '36640481529649198363378165',  'x-version': 'v2',  'x-signature': '04478027709342750176066248'}conn.request("POST", "/openapi/broker/account/nd/update", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
import http.clientimport jsonconn = http.client.HTTPSConnection("hk-broker-api.uat.webullbroker.com")payload = json.dumps({  "client_request_id": "LJIS16BACHQG9LPP44L9IQHGAB",  "account_id": "943a9802f6c14983b3b4755c69c01717",  "trading_permissions": [    "US_STOCK_NORMAL"  ],  "commission_code": "STANDARD_COMMISSION",  "w8ben_info": {    "treaty_country": "HK",    "tax_id": "123-45-6789",    "sign_date": "2026-01-01"  },  "china_connect_investor_info": {    "first_name": "John",    "last_name": "Doe",    "middle_name": "Michael",    "id_type": "ID_CARD",    "id_number": "X12345678",    "country_of_issuance": "HK"  }})headers = {  'Content-Type': 'application/json',  'Accept': 'application/json',  'x-timestamp': '2026-05-17T14:37:48Z',  'x-signature-version': '1.0',  'x-signature-algorithm': 'HMAC-SHA1',  'x-signature-nonce': '36640481529649198363378165',  'x-version': 'v2',  'x-signature': '04478027709342750176066248'}conn.request("POST", "/openapi/broker/account/nd/update", payload, headers)res = conn.getresponse()data = res.read()print(data.decode("utf-8"))
```

```json
{
  "client_request_id": "LJIS16BACHQG9LPP44L9IQHGAB",
  "account_id": "943a9802f6c14983b3b4755c69c01717",
  "trading_permissions": [
    "US_STOCK_NORMAL"
  ],
  "commission_code": "STANDARD_COMMISSION",
  "w8ben_info": {
    "treaty_country": "HK",
    "tax_id": "123-45-6789",
    "sign_date": "2026-01-01"
  },
  "china_connect_investor_info": {
    "first_name": "John",
    "last_name": "Doe",
    "middle_name": "Michael",
    "id_type": "ID_CARD",
    "id_number": "X12345678",
    "country_of_issuance": "HK"
  }
}
```

> **Source:** [https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-update](https://developer.webull.hk/apis/docs/reference/broker-api/broker-account-update)
