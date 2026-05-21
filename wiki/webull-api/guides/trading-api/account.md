---
title: Accounts
source: https://developer.webull.hk/apis/docs/trade-api/account
updated: 2026-05-17
tags: [webull, guide, trading, account]
---

# Accounts

The Account API lets you retrieve your account list, query balances, and check current positions. These are typically the first calls you make before placing any orders.

## Available Endpoints

| Endpoint | Description |
| --- | --- |
| Account List | Retrieve all accounts under your credentials |
| Account Balance | Query balance, buying power, and cash details for a specific account |
| Account Positions | Retrieve current holdings and positions for a specific account |

## Typical Workflow

1. Call **Account List** to get your `account_id`
2. Use the `account_id` to query **Balance** or **Positions**
3. Based on balance and positions, decide on your trading strategy

> **Tip:** The Account List response includes all accounts associated with your credentials. Stock and options accounts may have separate Account IDs.

## Code Examples

### Get Account List

```python
from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient

api_client = ApiClient("<your_app_key>", "<your_app_secret>", "hk")
api_client.add_endpoint("hk", "<api_endpoint>")

trade_client = TradeClient(api_client)
res = trade_client.get_account_list()
if res.status_code == 200:
    accounts = res.json()
    for account in accounts:
        print(f"Account ID: {account['account_id']}, Type: {account['account_type']}")
```

### Query Account Balance

```python
account_id = "<your_account_id>"
res = trade_client.get_account_balance(account_id=account_id)
if res.status_code == 200:
    print("Balance:", res.json())
```

### Query Account Positions

```python
res = trade_client.get_account_positions(account_id=account_id)
if res.status_code == 200:
    print("Positions:", res.json())
```

## What's Next

- Stock Trading -- Stock and ETF order management
- Options -- Options trading
