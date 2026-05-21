---
title: Market Data API Getting Started
source: https://developer.webull.hk/apis/docs/market-data-api/getting-started
updated: 2026-05-17
tags: [webull, guide, market-data, sdk]
---

# Market Data API Getting Started

A quick guide to get you from zero to your first market data request. We'll install the SDK, set up authentication, and run two examples: fetching historical bars and subscribing to real-time quotes.

## Historical Bars Example

```python
from webull.data.common.category import Category
from webull.data.common.timespan import Timespan
from webull.core.client import ApiClient
from webull.data.data_client import DataClient

api_client = ApiClient("<your_app_key>", "<your_app_secret>", "hk")
api_client.add_endpoint("hk", "<api_endpoint>")

data_client = DataClient(api_client)

# Single symbol
res = data_client.market_data.get_history_bar("AAPL", Category.US_STOCK.name, Timespan.M1.name)
if res.status_code == 200:
    print("History bar:", res.json())

# Batch query (multiple symbols)
res = data_client.market_data.get_batch_history_bar(
    ["AAPL", "TSLA"], Category.US_STOCK.name, Timespan.M1.name, 1
)
if res.status_code == 200:
    print("Batch history bar:", res.json())
```

## Real-Time Streaming Example

This example connects to the MQTT streaming service and subscribes to real-time quote, snapshot, and tick data for AAPL:

```python
from webull.data.common.category import Category
from webull.data.common.subscribe_type import SubscribeType
from webull.data.data_streaming_client import DataStreamingClient

data_streaming_client = DataStreamingClient(
    "<your_app_key>",
    "<your_app_secret>",
    "hk",
    "demo_session_1",
    http_host="<api_endpoint>",
    mqtt_host="<data_api_endpoint>",
)

def on_connect(client, api_client, session_id):
    print("Connected:", client.get_session_id())
    client.subscribe(
        ["AAPL"],
        Category.US_STOCK.name,
        [SubscribeType.QUOTE.name, SubscribeType.SNAPSHOT.name, SubscribeType.TICK.name],
    )

def on_message(client, topic, quotes):
    print("Topic:", topic, "Data:", quotes)

def on_subscribe(client, api_client, session_id):
    print("Subscribed:", client.get_session_id())

data_streaming_client.on_connect_success = on_connect
data_streaming_client.on_quotes_message = on_message
data_streaming_client.on_subscribe_success = on_subscribe
data_streaming_client.connect_and_loop_forever()
```

If you prefer not to use the SDK for streaming, see Data Streaming API for the raw MQTT integration guide.
