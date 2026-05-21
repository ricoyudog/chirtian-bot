---
title: "Subscribe Trade Events"
method: gRPC
endpoint: Trade Events Subscription (server streaming)
rate_limit: "N/A"
source: https://developer.webull.hk/apis/docs/reference/custom/subscribe-trade-events
updated: 2026-05-17
tags:
  - webull
  - api-reference
  - trading
---

# Subscribe Trade Events

### Interface Description

Trade events subscription is a `server streaming` persistent connection implemented based on `gRPC`, which is suitable for connecting Webull customers through the OpenAPI development platform. The trade events subscription fully follows the `gRPC` open source protocol, and you can refer to the [gRPC open source](https://grpc.io/docs/) library when using it.

Currently, the interface supports order status change message push, and the supported scenarios are as follows:

| scene_type | Description |
|------------|-------------|
| FILLED | Partially filled |
| FINAL_FILLED | All filled |
| PLACE_FAILED | Order failed |
| MODIFY_SUCCESS | Change order successfully |
| MODIFY_FAILED | Change order failed |
| CANCEL_SUCCESS | Cancellation succeeded |
| CANCEL_FAILED | Cancellation failed |

## Trade events subscribe Proto protocol definition

**Request Proto**

```protobuf
message SubscribeRequest {
  uint32 subscribeType = 1; // Subscription type
  int64 timestamp = 2; // Timestamp
  string contentType = 3; // Content type
  string payload = 4; // Content
  repeated string accounts = 5; // Account ID
}
```

**Response Proto**

```protobuf
message SubscribeResponse {
  EventType eventType = 1; // Event type
  uint32 subscribeType = 2; // Subscription type
  string contentType = 3; // Subscription type
  string payload = 4; // Content
  string requestId = 5; // Request id
  int64 timestamp = 6; // Timestamp
}
```

**EventType enumeration**

```protobuf
enum EventType {
  SubscribeSuccess = 0; // Subscription succeeded
  Ping = 1; // Heartbeat information
  AuthError = 2; // Authentication error
  NumOfConnExceed = 3; // Connection limit exceeded
  SubscribeExpired = 4; // Subscription expired
}
```

## Request Example

When using sdk request, subscribeType, timestamp, contentType, and payload can be ignored. Just pass in the accounts. subscribeType currently only supports =1.

In the following case, the _on_log method is used to output the log. The my_on_events_message method is to receive order status change messages.

### Python SDK

```python
import logging
from webull.trade.events.types import ORDER_STATUS_CHANGED, EVENT_TYPE_ORDER
from webull.trade.trade_events_client import TradeEventsClient

your_app_key = ""
your_app_secret = ""
account_id = ""
region_id = "hk"
# PRD env host: events-api.webull.hk
# Test env host: events-api.sandbox.webull.hk
optional_api_endpoint = ""

def _on_log(level, log_content):
    print(logging.getLevelName(level), log_content)

def my_on_events_message(event_type, subscribe_type, payload, raw_message):
    if EVENT_TYPE_ORDER == event_type and ORDER_STATUS_CHANGED == subscribe_type:
        print('%s' % payload)

if __name__ == '__main__':
    # Create EventsClient instance
    trade_events_client = TradeEventsClient(your_app_key, your_app_secret, region_id)
    # For non production environment, you need to set the domain name of the subscription service through eventsclient.
    # trade_events_client = TradeEventsClient(your_app_key, your_app_secret, region_id, host=optional_api_endpoint)
    trade_events_client.on_log = _on_log
    # Set the callback function when the event data is received.
    trade_events_client.on_events_message = my_on_events_message
    # Set the account ID to be subscribed and initiate the subscription. This method is synchronous
    trade_events_client.do_subscribe([account_id])
```

### Java SDK

The handleEventMessage method is to receive order status change messages.

```java
import com.google.gson.reflect.TypeToken;
import com.webull.openapi.core.execption.ClientException;
import com.webull.openapi.core.execption.ServerException;
import com.webull.openapi.core.logger.Logger;
import com.webull.openapi.core.logger.LoggerFactory;
import com.webull.openapi.core.serialize.JsonSerializer;
import com.webull.openapi.samples.config.Env;
import com.webull.openapi.trade.events.subscribe.ISubscription;
import com.webull.openapi.trade.events.subscribe.ITradeEventClient;
import com.webull.openapi.trade.events.subscribe.message.EventType;
import com.webull.openapi.trade.events.subscribe.message.SubscribeRequest;
import com.webull.openapi.trade.events.subscribe.message.SubscribeResponse;
import java.util.Map;

public class TradeEventsClient {
    private static final Logger logger = LoggerFactory.getLogger(TradeEventsClient.class);

    public static void main(String[] args) {
        try (ITradeEventClient client = ITradeEventClient.builder()
                .appKey(Env.APP_KEY)
                .appSecret(Env.APP_SECRET)
                .regionId(Env.REGION_ID)
                // .host("")
                .onMessage(TradeEventsClient::handleEventMessage)
                .build()) {
            SubscribeRequest request = new SubscribeRequest("");
            ISubscription subscription = client.subscribe(request);
            subscription.blockingAwait();
        } catch (ClientException ex) {
            logger.error("Client error", ex);
        } catch (ServerException ex) {
            logger.error("Sever error", ex);
        } catch (Exception ex) {
            logger.error("Unknown error", ex);
        }
    }

    private static void handleEventMessage(SubscribeResponse response) {
        if (SubscribeResponse.CONTENT_TYPE_JSON.equals(response.getContentType())) {
            Map payload = JsonSerializer.fromJson(response.getPayload(),
                    new TypeToken<Map<String, String>>(){}.getType());
            if (EventType.Order.getCode() == response.getEventType() || EventType.Position.getCode() == response.getEventType()) {
                logger.info("{}", payload);
            }
        }
    }
}
```

## Response Example

Transaction event scene type examples:

### FILLED (Partially filled)

```json
{
  "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",
  "request_id": "036LVUOVRA8BV0KHKN60000000",
  "order_id": "036LVUOVRA8BV0KHKN60000000",
  "client_order_id": "6adeba36fc174acd92538e990c06274e",
  "instrument_id": "913256135",
  "order_status": "PARTIAL_FILLED",
  "symbol": "AAPL",
  "short_name": "Apple Inc",
  "qty": "3.0000000000",
  "filled_price": "10.0",
  "filled_qty": "1.0",
  "filled_time": "2025-11-26T11:40:35.524+0000",
  "side": "BUY",
  "scene_type": "FILLED",
  "category": "US_STOCK",
  "order_type": "LIMIT",
  "actual_commission": "0.01",
  "receivable_commission": "0.01",
  "fees": [
    {
      "type": "FINRA_CAT_REGULATORY_FEE",
      "actual_value": "0.01",
      "receivable_value": "0.01"
    }
  ]
}
```

### FINAL_FILLED (All filled)

```json
{
  "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",
  "request_id": "036LVUAB7C8BV0KHKN60000000",
  "order_id": "036LVUAB7C8BV0KHKN60000000",
  "client_order_id": "9b0440781feb4c0cb8523224ce0926ac",
  "instrument_id": "913256135",
  "order_status": "FILLED",
  "symbol": "AAPL",
  "short_name": "Apple Inc",
  "qty": "2.0000000000",
  "filled_price": "277.98",
  "filled_qty": "2.0",
  "filled_time": "2025-11-26T11:35:38.513+0000",
  "side": "BUY",
  "scene_type": "FINAL_FILLED",
  "category": "US_STOCK",
  "order_type": "MARKET",
  "actual_commission": "0.01",
  "receivable_commission": "0.01",
  "fees": [
    {
      "type": "FINRA_CAT_REGULATORY_FEE",
      "actual_value": "0.01",
      "receivable_value": "0.01"
    }
  ]
}
```

### PLACE_FAILED (Order failed)

```json
{
  "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",
  "request_id": "036LVV3TME8BV0KHKN60000000",
  "order_id": "036LVV3TME8BV0KHKN60000000",
  "client_order_id": "794cabc6783640d7869a37f966ae4819",
  "instrument_id": "913256135",
  "order_status": "FAILED",
  "symbol": "AAPL",
  "short_name": "Apple Inc",
  "qty": "92.0000000000",
  "filled_price": "0E-10",
  "filled_qty": "0E-10",
  "side": "BUY",
  "scene_type": "PLACE_FAILED",
  "category": "US_STOCK",
  "order_type": "LIMIT"
}
```

### MODIFY_SUCCESS (Change order successfully)

```json
{
  "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",
  "request_id": "036LVV5P4I8BV0KHKN60000000",
  "order_id": "036LVV5P4I8BV0KHKN60000000",
  "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",
  "instrument_id": "913256135",
  "order_status": "WORKING",
  "symbol": "AAPL",
  "short_name": "Apple Inc",
  "qty": "4.0000000000",
  "filled_price": "0E-10",
  "filled_qty": "0E-10",
  "side": "BUY",
  "scene_type": "MODIFY_SUCCESS",
  "category": "US_STOCK",
  "order_type": "LIMIT",
  "actual_commission": "0.01",
  "receivable_commission": "0.01",
  "fees": [
    {
      "type": "FINRA_CAT_REGULATORY_FEE",
      "actual_value": "0.01",
      "receivable_value": "0.01"
    }
  ]
}
```

### CANCEL_SUCCESS (Cancellation succeeded)

```json
{
  "account_id": "PHIUK08VAKH7EOVG85ULCAG3JB",
  "request_id": "036LVV5P4I8BV0KHKN60000000",
  "order_id": "036LVV5P4I8BV0KHKN60000000",
  "client_order_id": "04cda8db7ed940f6afeb26be6201ee53",
  "instrument_id": "913256135",
  "order_status": "CANCELLED",
  "symbol": "AAPL",
  "short_name": "Apple Inc",
  "qty": "4.0000000000",
  "filled_price": "0E-10",
  "filled_qty": "0E-10",
  "side": "BUY",
  "scene_type": "CANCEL_SUCCESS",
  "category": "US_STOCK",
  "order_type": "LIMIT",
  "actual_commission": "0.01",
  "receivable_commission": "0.01",
  "fees": [
    {
      "type": "FINRA_CAT_REGULATORY_FEE",
      "actual_value": "0.01",
      "receivable_value": "0.01"
    }
  ]
}
```

## Response Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| account_id | string | Account identifier | PHIUK08VAKH7EOVG85ULCAG3JB |
| request_id | string | Request identifier | 036LVUOVRA8BV0KHKN60000000 |
| order_id | string | System-generated order identifier | 036LVUOVRA8BV0KHKN60000000 |
| client_order_id | string | Client-defined order identifier | 6adeba36fc174acd92538e990c06274e |
| instrument_id | string | Instrument identifier | 913256135 |
| order_status | string | Order status (PARTIAL_FILLED, FILLED, FAILED, WORKING, CANCELLED) | PARTIAL_FILLED |
| symbol | string | Trading symbol | AAPL |
| short_name | string | Instrument short name | Apple Inc |
| qty | string | Order quantity | 3.0000000000 |
| filled_price | string | Filled price | 10.0 |
| filled_qty | string | Filled quantity | 1.0 |
| filled_time | string | Fill timestamp (ISO8601) | 2025-11-26T11:40:35.524+0000 |
| side | string | Order side (BUY, SELL, SHORT) | BUY |
| scene_type | string | Event scene type | FILLED |
| category | string | Market category (US_STOCK, etc.) | US_STOCK |
| order_type | string | Order type (LIMIT, MARKET, etc.) | LIMIT |
| actual_commission | string | Actual commission | 0.01 |
| receivable_commission | string | Receivable commission | 0.01 |
| fees | array | Fee breakdown array | (see below) |

### fees items

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| type | string | Fee type | FINRA_CAT_REGULATORY_FEE |
| actual_value | string | Actual fee value | 0.01 |
| receivable_value | string | Receivable fee value | 0.01 |

## Environment Endpoints

| Environment | Host |
|-------------|------|
| Production | events-api.webull.hk |
| Sandbox/Test | events-api.sandbox.webull.hk |
