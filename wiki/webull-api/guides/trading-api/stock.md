---
title: Stock Trading
source: https://developer.webull.hk/apis/docs/trade-api/stock
updated: 2026-05-17
tags: [webull, guide, trading, stock]
---

# Stock Trading

The Stock Orders API supports placing, modifying, and cancelling orders for stocks and ETFs across US, HK, and A-share markets. The unified order interface handles market-specific rules automatically based on the `market` parameter you specify.

For options trading, see the dedicated Options page. For the full list of supported order types and features by market, see the Feature Matrix in the Trading API Overview.

## Order Lifecycle

Every order follows this lifecycle:

1. **Preview** -- Estimate costs and fees before committing
2. **Place** -- Submit the order
3. **Replace** -- Modify price or quantity while the order is open
4. **Cancel** -- Cancel a pending order
5. **Query** -- Check order status, history, or details at any time

## Key Parameters

| Parameter | Required | Description |
| --- | --- | --- |
| `account_id` | Yes | Trading account identifier |
| `client_order_id` | Yes | Unique client-defined order ID (max 32 chars, must be unique per account) |
| `combo_type` | Yes | `NORMAL` for standard single orders |
| `symbol` | Yes | Trading symbol (e.g., `AAPL`, `00700`, `600519`) |
| `instrument_type` | Yes | `EQUITY` for stock orders |
| `market` | Yes | `US`, `HK`, or `CN` |
| `order_type` | Yes | Order type -- varies by market (see below) |
| `side` | Yes | `BUY`, `SELL`, or `SHORT` |
| `quantity` | Yes | Number of shares |
| `entrust_type` | Yes | `QTY` (by quantity) or `AMOUNT` (by cash amount, US fractional shares only) |
| `time_in_force` | Yes | `DAY`, `GTC`, or `GTD` (US only) |
| `limit_price` | Conditional | Required for `LIMIT`, `STOP_LOSS_LIMIT`, `ENHANCED_LIMIT`, `AT_AUCTION_LIMIT` |
| `stop_price` | Conditional | Required for `STOP_LOSS`, `STOP_LOSS_LIMIT` |
| `support_trading_session` | US only | `CORE`, `ALL`, `NIGHT`, or `ALL_DAY` |
| `no_party_ids` | HK only | BCAN party identifiers for regulatory compliance |

## Supported Order Types by Market

| Market | Order Types |
| --- | --- |
| US | `LIMIT`, `MARKET`, `STOP_LOSS`, `STOP_LOSS_LIMIT`, `MARKET_ON_OPEN`, `MARKET_ON_CLOSE` |
| HK | `ENHANCED_LIMIT`, `AT_AUCTION`, `AT_AUCTION_LIMIT` |
| CN (A-Share) | `LIMIT` |

## Request Examples -- US Stock

### Limit Order

Buy 10 shares of AAPL at a limit price of $180, valid for the current trading day during regular hours.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "180.00",
      "quantity": "10",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "CORE",
      "entrust_type": "QTY"
    }
  ]
}
```

### Market Order

Buy 5 shares of TSLA at market price, valid for the current trading day.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "TSLA",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "MARKET",
      "quantity": "5",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "CORE",
      "entrust_type": "QTY"
    }
  ]
}
```

### Stop Loss

Sell 20 shares of NVDA when the price drops to $100 (triggers a market order).

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "NVDA",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "STOP_LOSS",
      "stop_price": "100.00",
      "quantity": "20",
      "side": "SELL",
      "time_in_force": "GTC",
      "support_trading_session": "CORE",
      "entrust_type": "QTY"
    }
  ]
}
```

### Stop Loss Limit

Sell 10 shares of AMZN when the price drops to $180 (stop price), then place a limit order at $178.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "AMZN",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "STOP_LOSS_LIMIT",
      "stop_price": "180.00",
      "limit_price": "178.00",
      "quantity": "10",
      "side": "SELL",
      "time_in_force": "GTC",
      "support_trading_session": "CORE",
      "entrust_type": "QTY"
    }
  ]
}
```

### Market on Open

Buy 50 shares of MSFT at the opening price.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "MSFT",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "MARKET_ON_OPEN",
      "quantity": "50",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "CORE",
      "entrust_type": "QTY"
    }
  ]
}
```

### Market on Close

Sell 30 shares of GOOG at the closing price.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "GOOG",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "MARKET_ON_CLOSE",
      "quantity": "30",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "CORE",
      "entrust_type": "QTY"
    }
  ]
}
```

### Fractional Shares

Buy $500 worth of AAPL (fractional share order by amount).

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "MARKET",
      "total_cash_amount": "500.00",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "CORE",
      "entrust_type": "AMOUNT"
    }
  ]
}
```

### Extended Hours

Buy 10 shares of AAPL with a limit order, valid across all trading sessions including pre-market and after-hours.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "178.00",
      "quantity": "10",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    }
  ]
}
```

## Request Examples -- HK Stock

> **HK Lot Sizes:** HK stocks are traded in board lots. The lot size varies by stock (e.g., Tencent 00700 = 100 shares, HSBC 00005 = 400 shares, AIA 01299 = 200 shares). Orders must be placed in multiples of the board lot. You can query the lot size via the instrument data API.

### Enhanced Limit

Buy 100 shares of Tencent (00700) with an enhanced limit order. HK orders require BCAN party identifiers.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "00700",
      "instrument_type": "EQUITY",
      "market": "HK",
      "order_type": "ENHANCED_LIMIT",
      "limit_price": "380.00",
      "quantity": "100",
      "side": "BUY",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "no_party_ids": [
        {
          "party_id": "ABC123.2568",
          "party_id_source": "D",
          "party_role": "3"
        }
      ]
    }
  ]
}
```

### At-Auction

Buy 200 shares of HSBC (00005) at the auction price. At-auction orders do not require a limit price.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "00005",
      "instrument_type": "EQUITY",
      "market": "HK",
      "order_type": "AT_AUCTION",
      "quantity": "200",
      "side": "BUY",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "no_party_ids": [
        {
          "party_id": "ABC123.2568",
          "party_id_source": "D",
          "party_role": "3"
        }
      ]
    }
  ]
}
```

### At-Auction Limit

Buy 500 shares of AIA (01299) at auction with a limit price of HK$60.00.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "01299",
      "instrument_type": "EQUITY",
      "market": "HK",
      "order_type": "AT_AUCTION_LIMIT",
      "limit_price": "60.00",
      "quantity": "500",
      "side": "BUY",
      "time_in_force": "DAY",
      "entrust_type": "QTY",
      "no_party_ids": [
        {
          "party_id": "ABC123.2568",
          "party_id_source": "D",
          "party_role": "3"
        }
      ]
    }
  ]
}
```

## Request Examples -- A-Share (China Connect)

A-share trading via Stock Connect only supports `LIMIT` orders.

```json
{
  "account_id": "<your_account_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id>",
      "combo_type": "NORMAL",
      "symbol": "600519",
      "instrument_type": "EQUITY",
      "market": "CN",
      "order_type": "LIMIT",
      "limit_price": "1800.00",
      "quantity": "100",
      "side": "BUY",
      "time_in_force": "DAY",
      "entrust_type": "QTY"
    }
  ]
}
```

> **Note:** A-share trading is disabled by default. Contact Webull support to enable it for your account.

> **A-Share Price Limits:** A-share prices are subject to daily limit-up / limit-down rules (typically +/-10%, or +/-20% for ChiNext / STAR Market stocks). Orders with a `limit_price` outside the allowed range will be rejected. Check the current price range before placing orders.

## Combo Orders (US Only)

In addition to standard single orders (`combo_type: NORMAL`), the API supports combination order types for more advanced execution strategies. Combo orders let you link multiple legs together so they execute as a coordinated group.

> **Note:** Combo orders are currently available for US stock orders only.

### Take Profit / Stop Loss

Attach a take-profit and/or stop-loss leg to a master order. The master order executes first; the TP/SL legs activate once the master is filled.

| `combo_type` | Supported Order Types | Leg Count | Description |
| --- | --- | --- | --- |
| `MASTER` | `MARKET`, `LIMIT` | 1 | Master order |
| `STOP_PROFIT` | `LIMIT` | 0-1 | Take-profit leg |
| `STOP_LOSS` | `STOP_LOSS` | 0-1 | Stop-loss leg |

### OTO (One Triggers Other)

A master order that, once filled, automatically triggers one or more dependent orders.

| `combo_type` | Supported Order Types | Leg Count | Description |
| --- | --- | --- | --- |
| `MASTER` | `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TOUCH_LMT`, `TOUCH_MKT`, `TRAILING_STOP_LOSS`, `TRAILING_STOP_LOSS_LIMIT` | 1 | Master order |
| `OTO` | `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT` | 1-6 | Triggered order(s) |

### OCO (One Cancels Other)

A group of orders where filling any one leg automatically cancels the remaining legs.

| `combo_type` | Supported Order Types | Leg Count | Description |
| --- | --- | --- | --- |
| `OCO` | `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT` | 2-6 | OCO legs |

### OTOCO (One Triggers OCO)

A master order that, once filled, triggers an OCO group.

| `combo_type` | Supported Order Types | Leg Count | Description |
| --- | --- | --- | --- |
| `MASTER` | `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TOUCH_LMT`, `TOUCH_MKT`, `TRAILING_STOP_LOSS`, `TRAILING_STOP_LOSS_LIMIT` | 1 | Master order |
| `OTOCO` | `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT` | 1-6 | OCO legs triggered by master |

### Combo Order Examples

#### Take Profit / Stop Loss Example

Buy 1 share of AAPL at $176, with a stop-loss triggered at $169 (using bid price) and a take-profit limit at $279.

```json
{
  "account_id": "<your_account_id>",
  "client_combo_order_id": "<unique_combo_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id_master>",
      "combo_type": "MASTER",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "176.00",
      "quantity": "1",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    },
    {
      "client_order_id": "<unique_id_sl>",
      "combo_type": "STOP_LOSS",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "STOP_LOSS",
      "stop_price": "169.00",
      "trigger_price_type": "PRICE_BID",
      "quantity": "1",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    },
    {
      "client_order_id": "<unique_id_tp>",
      "combo_type": "STOP_PROFIT",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "279.00",
      "quantity": "1",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    }
  ]
}
```

#### OTO Example

Buy 1 share of AAPL at $176 (master), then automatically place two limit sell orders at $199 and $279 once the master is filled.

```json
{
  "account_id": "<your_account_id>",
  "client_combo_order_id": "<unique_combo_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id_master>",
      "combo_type": "MASTER",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "176.00",
      "quantity": "1",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    },
    {
      "client_order_id": "<unique_id_oto_1>",
      "combo_type": "OTO",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "199.00",
      "quantity": "1",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    },
    {
      "client_order_id": "<unique_id_oto_2>",
      "combo_type": "OTO",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "279.00",
      "quantity": "1",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    }
  ]
}
```

#### OCO Example

Place three OCO legs on AAPL: a limit buy at $176, a limit sell at $199, and a limit sell at $279. When any one leg fills, the others are automatically cancelled.

```json
{
  "account_id": "<your_account_id>",
  "client_combo_order_id": "<unique_combo_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id_oco_1>",
      "combo_type": "OCO",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "176.00",
      "quantity": "1",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    },
    {
      "client_order_id": "<unique_id_oco_2>",
      "combo_type": "OCO",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "199.00",
      "quantity": "1",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    },
    {
      "client_order_id": "<unique_id_oco_3>",
      "combo_type": "OCO",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "279.00",
      "quantity": "1",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    }
  ]
}
```

#### OTOCO Example

Buy 1 share of AAPL at $176 (master). Once filled, trigger an OCO group: a limit sell at $199 and a limit sell at $279 -- whichever fills first cancels the other.

```json
{
  "account_id": "<your_account_id>",
  "client_combo_order_id": "<unique_combo_id>",
  "new_orders": [
    {
      "client_order_id": "<unique_id_master>",
      "combo_type": "MASTER",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "176.00",
      "quantity": "1",
      "side": "BUY",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    },
    {
      "client_order_id": "<unique_id_otoco_1>",
      "combo_type": "OTOCO",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "199.00",
      "quantity": "1",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    },
    {
      "client_order_id": "<unique_id_otoco_2>",
      "combo_type": "OTOCO",
      "symbol": "AAPL",
      "instrument_type": "EQUITY",
      "market": "US",
      "order_type": "LIMIT",
      "limit_price": "279.00",
      "quantity": "1",
      "side": "SELL",
      "time_in_force": "DAY",
      "support_trading_session": "ALL",
      "entrust_type": "QTY"
    }
  ]
}
```

## What's Next

- Options -- Options trading
- Trading API Overview -- Full feature matrix by market
- Accounts -- Query balances and positions
- Trading API FAQ -- Common questions and troubleshooting
