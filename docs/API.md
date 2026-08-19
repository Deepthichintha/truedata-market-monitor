# TrueData Market Monitor - API Reference

## Base URLs

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

## 1. GET /health

Checks application health.

```bash
curl http://127.0.0.1:8000/health
```

Typical response:

```json
{
  "status": "healthy",
  "service": "TrueData Market Monitor",
  "environment": "development"
}
```

## 2. GET /api/symbols

Returns configured market symbols.

```bash
curl http://127.0.0.1:8000/api/symbols
```

The configured project uses the validated NSE symbol set.

## 3. GET /api/market/status

Returns market/feed state.

```bash
curl http://127.0.0.1:8000/api/market/status
```

Possible statuses:

- `LIVE`
- `STALE`
- `CLOSED`

Configured NSE market window:

```text
09:15 - 15:30
```

Configured stale threshold:

```text
60 seconds
```

## 4. GET /api/market/live

Returns the latest stored tick for active mapped symbols.

```bash
curl http://127.0.0.1:8000/api/market/live
```

Typical market fields include:

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

## 5. GET /api/market/{symbol}

Returns the latest tick for one symbol.

Example:

```bash
curl http://127.0.0.1:8000/api/market/RELIANCE
```

Possible `404` conditions include unknown symbols, missing TrueData mappings, or absence of stored market data.

## 6. GET /api/market/{symbol}/history

Returns historical EOD bars.

Example:

```bash
curl "http://127.0.0.1:8000/api/market/RELIANCE/history?limit=200"
```

Parameter:

| Parameter | Range | Purpose |
|---|---:|---|
| `limit` | 1-500 | Maximum number of historical rows |

Current timeframe is `1D`.

## Error Handling

Common responses:

| Code | Meaning |
|---:|---|
| 200 | Successful request |
| 404 | Symbol, mapping, or data not found |
| 500 | Internal application/database error |

The authoritative API contract is always the generated FastAPI OpenAPI specification available at `/docs` and `/openapi.json`.
