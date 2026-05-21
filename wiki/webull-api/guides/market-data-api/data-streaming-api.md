---
title: Data Streaming API
source: https://developer.webull.hk/apis/docs/market-data-api/data-streaming-api
updated: 2026-05-17
tags: [webull, guide, market-data, streaming, mqtt]
---

# Data Streaming API

The Data Streaming API pushes real-time market data using the MQTT protocol (v3.1.1) over TCP/IP or WebSocket. Use it to receive live quotes, snapshots, and tick data as they happen.

For on-demand HTTP queries, see Data API.

> **SDK Users:** The Webull SDK handles MQTT connection, authentication, and message parsing automatically. See the real-time streaming example in Getting Started. The steps below are for manual integration without the SDK.

## Supported Data

| Market | Categories |
| --- | --- |
| Hong Kong | Stocks, ETFs |
| United States | Stocks, ETFs |
| China Mainland | A-Shares (Stock Connect) |

| Data Type | Description |
| --- | --- |
| QUOTE | Real-time order book |
| SNAPSHOT | Market snapshot |
| TICK | Tick-by-tick transaction details |

## Step 1: Establish an MQTT Connection

### Connection Endpoints

| Environment | Protocol | Endpoint |
| --- | --- | --- |
| Production | TCP/IP | `data-api.webull.hk:1883` |
| Production | WebSocket | `wss://data-api.webull.hk:8883/mqtt` |
| Sandbox | TCP/IP | `data-api.sandbox.webull.hk:1883` |
| Sandbox | WebSocket | `wss://data-api.sandbox.webull.hk:8883/mqtt` |

### MQTT Client Libraries

- Python
- Java
- JavaScript
- Golang
- More languages

### CONNECT Packet Fields

| Field | Value |
| --- | --- |
| ClientId | A unique `session_id` you create (also used for subscribe/unsubscribe calls) |
| User Name | Your `App Key` |
| Password | Any value |

**Connection Rules:**

- Do not reuse the same `session_id` across multiple connections under one App Key. A new connection with the same `session_id` will disconnect the previous one.
- Each App Key supports a maximum of 5 concurrent connections. Exceeding this returns error code `105`.
- After disconnecting, the server retains connection state for about 1 minute. If you've reached 5 connections, wait 1 minute before reconnecting.
- The server pushes messages at a maximum rate of 3 times per second per connection.

### Connection Error Codes

| Code | Description |
| --- | --- |
| 0 | Connection accepted |
| 1 | Unacceptable protocol version |
| 2 | Invalid ClientId |
| 3 | App Key is empty |
| 7 | Connection lost |
| 16 | Heartbeat timeout |
| 100 | Unknown error |
| 101 | Internal error |
| 102 | Connection already authenticated |
| 103 | Authentication failed |
| 104 | Invalid App Key |
| 105 | Exceeds connection limit |

## Step 2: Subscribe to Market Data

After establishing the MQTT connection, use the HTTP API to manage subscriptions:

- Subscribe — Start receiving real-time data for specified symbols
- Unsubscribe — Stop receiving data for specified symbols

> **Caution:** If the connection is dropped due to network issues, previous subscriptions are not automatically restored. You must re-subscribe after reconnecting.

## Step 3: Parse Incoming Messages

Each message pushed from the server contains:

- **Topic** — Identifies the data type
- **Payload** — The actual data, serialized using Protocol Buffers or JSON

### Topic-to-Payload Mapping

| Data Type | Topic | Payload Format | Description |
| --- | --- | --- | --- |
| QUOTE | `quote` | Protobuf | Real-time order book |
| SNAPSHOT | `snapshot` | Protobuf | Market snapshot |
| TICK | `tick` | Protobuf | Tick-by-tick details |
| NOTICE | `notice` | JSON | Server notifications |
| ECHO | `echo` | Null | Online check (heartbeat) |

## Protobuf Message Definitions

### Basic (shared by all types)

```protobuf
message Basic {
    string symbol = 1;
    string instrument_id = 2;
    string timestamp = 3;
}
```

### Quote (Real-time Order Book)

```protobuf
message Quote {
    Basic basic = 1;
    repeated AskBid asks = 2;
    repeated AskBid bids = 3;
}

message AskBid {
    string price = 1;
    string size = 2;
    repeated Order order = 3;
    repeated Broker broker = 4;
}

message Order {
    string mpid = 1;
    string size = 2;
}

message Broker {
    string bid = 1;
    string name = 2;
}
```

### Snapshot (Market Snapshot)

```protobuf
message Snapshot {
    Basic basic = 1;
    string trade_time = 2;
    string price = 3;
    string open = 4;
    string high = 5;
    string low = 6;
    string pre_close = 7;
    string volume = 8;
    string change = 9;
    string change_ratio = 10;
    string ext_trade_time = 11;
    string ext_price = 12;
    string ext_high = 13;
    string ext_low = 14;
    string ext_volume = 15;
    string ext_change = 16;
    string ext_change_ratio = 17;
    string ovn_trade_time = 18;
    string ovn_price = 19;
    string ovn_high = 20;
    string ovn_low = 21;
    string ovn_volume = 22;
    string ovn_change = 23;
    string ovn_change_ratio = 24;
}
```

### Tick (Tick-by-Tick Detail)

```protobuf
message Tick {
    Basic basic = 1;
    string time = 2;
    string price = 3;
    string volume = 4;
    string side = 5;
}
```

### Notification (JSON)

```json
{
  "type": "status",
  "rtt": 100,
  "drop": 0,
  "sent": 0
}
```

## What's Next

Once your MQTT connection is live and subscriptions are active, you'll receive real-time market data as it happens. For a complete working example using the SDK, check the Market Data API Getting Started guide.

If you run into issues with connections or data delivery, see Additional Resources for support channels.
