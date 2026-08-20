# TrueData Market Monitor - API Reference

## 1. Base URLs

Local backend:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

## 2. Endpoint Summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Application health |
| GET | `/api/symbols` | Configured active symbols |
| GET | `/api/market/status` | Market session and feed status |
| GET | `/api/market/live` | Latest live data for active symbols |
| GET | `/api/market/{symbol}` | Latest data for one symbol |
| GET | `/api/market/{symbol}/history` | Historical EOD data |

The API currently supports both `NSE` and `BSE` symbols through the common market-data endpoints.

## 3. GET /health

Checks application health.

```bash
curl http://127.0.0.1:8000/health
```

## 4. GET /api/symbols

Returns configured active symbols.

```bash
curl http://127.0.0.1:8000/api/symbols
```

The current validated configuration contains:

```text
NSE: 50 symbols
BSE: 10 symbols
Total: 60 active symbols
```

## 5. GET /api/market/status

Returns the current Indian-market session and live-feed state.

```bash
curl http://127.0.0.1:8000/api/market/status
```

Timezone:

```text
Asia/Kolkata
```

Session schedule:

```text
08:45 - PRE_MARKET
09:15 - OPEN
15:30 - CLOSED
```

During the regular `OPEN` session, feed status is classified as:

- `LIVE` - recent tick received within the stale threshold
- `STALE` - latest tick is older than the stale threshold

Outside regular hours the session is reported separately as `PRE_MARKET` or `CLOSED`.

Current stale threshold:

```text
60 seconds
```

Typical fields include:

```text
status
market_open
market_session
market
pre_market_start_time
market_open_time
market_close_time
latest_tick
age_seconds
stale_threshold_seconds
active_symbols
server_time
timezone
```

## 6. GET /api/market/live

Returns the latest stored tick for each active symbol with a valid TrueData mapping.

```bash
curl http://127.0.0.1:8000/api/market/live
```

The response contains both NSE and BSE records when their latest live data is available.

Typical fields:

```text
symbol
exchange
truedata_symbol_id
timestamp
ltp
ltq
atp
total_volume
open
high
low
prev_close
oi
prev_oi
turnover
bid
bid_qty
ask
ask_qty
```

Example BSE response fragment:

```json
{
  "symbol": "AETHER_BSE",
  "exchange": "BSE",
  "truedata_symbol_id": "410004487",
  "ltp": 1623.35,
  "bid": 1623.85,
  "bid_qty": 16,
  "ask": 1626.6,
  "ask_qty": 7
}
```

## 7. GET /api/market/{symbol}

Returns the latest stored market tick for one active symbol.

Examples:

```bash
curl http://127.0.0.1:8000/api/market/AARTIIND
```

BSE:

```bash
curl http://127.0.0.1:8000/api/market/AETHER_BSE
```

Possible `404` conditions include:

- Symbol not found
- TrueData mapping missing
- No market data has been stored yet

## 8. GET /api/market/{symbol}/history

Returns historical EOD bars for the requested symbol.

```bash
curl "http://127.0.0.1:8000/api/market/AARTIIND/history?limit=200"
```

Parameter:

| Parameter | Range | Purpose |
|---|---:|---|
| `limit` | 1-500 | Maximum number of historical rows |

Current timeframe:

```text
1D
```

Historical BSE availability depends on whether BSE historical bars have been loaded into `historical_bars`; successful live BSE ingestion does not by itself create historical EOD records.

## 9. Response and Error Handling

| Code | Meaning |
|---:|---|
| 200 | Successful request |
| 404 | Symbol, mapping, or data not found |
| 500 | Internal application/database error |

The generated FastAPI OpenAPI specification is the authoritative API contract.
