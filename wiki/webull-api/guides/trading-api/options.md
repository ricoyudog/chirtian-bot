---
title: Options Trading
source: https://developer.webull.hk/apis/docs/trade-api/options
updated: 2026-05-17
tags: [webull, guide, trading, options]
---

# Options Trading

The Options API lets you trade options through the same unified order endpoints as stocks. Options are differentiated by setting `instrument_type: OPTION` and providing the `legs` array with option-specific parameters.

## Supported Order Types

Options support a subset of order types:

| Order Type | Description |
| --- | --- |
| `LIMIT` | Execute at the specified price or better |
| `STOP_LOSS` | Trigger a market order when the stop price is reached |
| `STOP_LOSS_LIMIT` | Trigger a limit order when the stop price is reached |

> **Caution:** `MARKET` order type is not supported for options. Only `BUY` and `SELL` sides are supported (no `SHORT`).

> **Time in Force for Sell-Side Orders:** Options sell-side orders (`SELL`) only support `DAY` as `time_in_force`. `GTC` is only available for buy-side orders.

### Time in Force

| Value | Description |
| --- | --- |
| `DAY` | Valid for the current trading day only |
| `GTC` | Good till cancelled |

## Key Parameters

| Parameter | Required | Description |
| --- | --- | --- |
| `option_strategy` | Yes | `SINGLE` for single-leg orders |
| `legs` | Yes | Array of leg definitions |
| `legs[].symbol` | Yes | Underlying symbol (e.g., `AAPL`) |
| `legs[].strike_price` | Yes | Strike price of the option |
| `legs[].option_expire_date` | Yes | Expiration date in `YYYY-MM-DD` format |
| `legs[].instrument_type` | Yes | `OPTION` |
| `legs[].option_type` | Yes | `CALL` or `PUT` |
| `legs[].market` | Yes | `US` |
| `legs[].side` | Yes | `BUY` or `SELL` |
| `legs[].quantity` | Yes | Number of contracts |

## API Endpoints

Options use the same endpoints as stock orders. See API Endpoints for the full list.

## Request Examples

### Buy Call (Limit)

Buy 1 AAPL call option at a limit price of $11.25, strike price $220, expiring 2025-11-19.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "order_type": "LIMIT",
      "limit_price": "11.25",
      "quantity": "1",
      "option_strategy": "SINGLE",
      "side": "BUY",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "instrument_type": "OPTION",
      "market": "US",
      "symbol": "AAPL",
      "legs": [
        {
          "side": "BUY",
          "quantity": "1",
          "symbol": "AAPL",
          "strike_price": "220.00",
          "option_expire_date": "2025-11-19",
          "instrument_type": "OPTION",
          "option_type": "CALL",
          "market": "US"
        }
      ]
    }
  ]
}
```

### Buy Put (Limit)

Buy 2 TSLA put options at a limit price of $8.50, strike price $250, expiring 2025-12-19.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "order_type": "LIMIT",
      "limit_price": "8.50",
      "quantity": "2",
      "option_strategy": "SINGLE",
      "side": "BUY",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "instrument_type": "OPTION",
      "market": "US",
      "symbol": "TSLA",
      "legs": [
        {
          "side": "BUY",
          "quantity": "2",
          "symbol": "TSLA",
          "strike_price": "250.00",
          "option_expire_date": "2025-12-19",
          "instrument_type": "OPTION",
          "option_type": "PUT",
          "market": "US"
        }
      ]
    }
  ]
}
```

### Sell Call (Limit)

Sell 1 AAPL call option (covered call) at a limit price of $5.00, strike price $230, expiring 2025-11-19.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "order_type": "LIMIT",
      "limit_price": "5.00",
      "quantity": "1",
      "option_strategy": "SINGLE",
      "side": "SELL",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "instrument_type": "OPTION",
      "market": "US",
      "symbol": "AAPL",
      "legs": [
        {
          "side": "SELL",
          "quantity": "1",
          "symbol": "AAPL",
          "strike_price": "230.00",
          "option_expire_date": "2025-11-19",
          "instrument_type": "OPTION",
          "option_type": "CALL",
          "market": "US"
        }
      ]
    }
  ]
}
```

### Sell Put (Limit)

Sell 1 NVDA put option (cash-secured put) at a limit price of $6.00, strike price $100, expiring 2025-12-19.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "order_type": "LIMIT",
      "limit_price": "6.00",
      "quantity": "1",
      "option_strategy": "SINGLE",
      "side": "SELL",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "instrument_type": "OPTION",
      "market": "US",
      "symbol": "NVDA",
      "legs": [
        {
          "side": "SELL",
          "quantity": "1",
          "symbol": "NVDA",
          "strike_price": "100.00",
          "option_expire_date": "2025-12-19",
          "instrument_type": "OPTION",
          "option_type": "PUT",
          "market": "US"
        }
      ]
    }
  ]
}
```

### Stop Loss

Sell 1 AAPL call option when the option price drops to $3.00 (triggers a market order). Useful for protecting an existing long option position.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "order_type": "STOP_LOSS",
      "stop_price": "3.00",
      "quantity": "1",
      "option_strategy": "SINGLE",
      "side": "SELL",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "instrument_type": "OPTION",
      "market": "US",
      "symbol": "AAPL",
      "legs": [
        {
          "side": "SELL",
          "quantity": "1",
          "symbol": "AAPL",
          "strike_price": "220.00",
          "option_expire_date": "2025-11-19",
          "instrument_type": "OPTION",
          "option_type": "CALL",
          "market": "US"
        }
      ]
    }
  ]
}
```

### Stop Loss Limit

Sell 1 TSLA put option when the price drops to $4.00 (stop price), then place a limit order at $3.80.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "order_type": "STOP_LOSS_LIMIT",
      "stop_price": "4.00",
      "limit_price": "3.80",
      "quantity": "1",
      "option_strategy": "SINGLE",
      "side": "SELL",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "instrument_type": "OPTION",
      "market": "US",
      "symbol": "TSLA",
      "legs": [
        {
          "side": "SELL",
          "quantity": "1",
          "symbol": "TSLA",
          "strike_price": "250.00",
          "option_expire_date": "2025-12-19",
          "instrument_type": "OPTION",
          "option_type": "PUT",
          "market": "US"
        }
      ]
    }
  ]
}
```

## What's Next

- Stock Trading -- Stock and ETF order management
- Trading API Overview -- Full feature matrix by market
- Accounts -- Query balances and positions
- Trading API FAQ -- Common questions and troubleshooting
