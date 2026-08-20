# TrueData Market Monitor - Testing and Validation

## 1. Testing Objectives

Testing verifies the complete market-data path:

```text
TrueData -> Collector -> Parser -> PostgreSQL -> FastAPI -> React Dashboard
```

The current validation covers both exchanges:

```text
NSE: 50 symbols
BSE: 10 symbols
Total: 60 active symbols
```

## 2. Validation Matrix

| Area | Scope | Result |
|---|---|---|
| TrueData WebSocket | Connection/authentication | PASS |
| NSE subscription | 50 symbols | PASS |
| NSE trade ingestion | Live ticks | PASS |
| NSE Bid/Ask | Live quote updates | PASS |
| BSE subscription | 10 symbols | PASS |
| BSE trade ingestion | Live ticks | PASS |
| BSE Bid/Ask L2 | Best bid/ask persistence | PASS |
| PostgreSQL persistence | Live tick records | PASS |
| `/api/market/live` | NSE + BSE output | PASS |
| `/api/market/status` | IST/session/stale logic | PASS |
| React dashboard | NSE + BSE display | PASS |
| Exchange filter | ALL/NSE/BSE | PASS |
| Symbol search | Existing dashboard behavior | PASS |
| Historical API | Existing 1D flow | Supported |
| Automatic reconnect | Production hardening | DEFERRED |

## 3. NSE Validation

The collector was validated with the configured 50 NSE symbols.

Expected subscription confirmation:

```text
Symbols added: 50
Total subscribed: 50
```

Live trade and Bid/Ask messages were observed and persisted.

## 4. BSE Validation

The BSE test set contains 10 matched symbols from the current SmartTheta application.

```text
AARTIIND_BSE
ADANIPORTS_BSE
AETHER_BSE
APOLLOHOSP_BSE
ASHIANA_BSE
ATUL_BSE
AUBANK_BSE
BAJAJ-AUTO_BSE
CARERATING_BSE
CCL_BSE
```

TrueData accepted all 10 subscriptions:

```text
Requested : 10
Subscribed: 10
Total subscribed: 10
```

Live BSE records were subsequently visible through `/api/market/live`.

Final validation result:

```text
BSE records: 10
```

## 5. BSE Quote Validation

TrueData BSE `bidaskL2` messages were observed for the subscribed symbols.

The collector extracts the best bid and ask values and persists them on the latest live tick.

The dashboard was verified to display BSE:

```text
LTP
ATP
Volume
Open
High
Low
Previous Close
Bid
Ask
Updated timestamp
```

## 6. Market Session Validation

The API uses:

```text
Timezone: Asia/Kolkata
Pre-market: 08:45
Regular open: 09:15
Regular close: 15:30
Stale threshold: 60 seconds
```

The status endpoint was validated in the regular session with both `LIVE` and `STALE` states depending on collector activity.

Example live state:

```json
{
  "status": "LIVE",
  "market_open": true,
  "market_session": "OPEN",
  "timezone": "Asia/Kolkata"
}
```

When the collector was stopped and the latest tick exceeded the threshold, the API correctly reported `STALE` while the market session remained `OPEN`.

## 7. Frontend Validation

The dashboard was verified with the combined exchange dataset.

Expected filters:

```text
ALL (60)
NSE (50)
BSE (10)
```

Expected results:

```text
ALL -> 60
NSE -> 50
BSE -> 10
```

BSE rows were confirmed visible with live values and exchange labels.

## 8. API Testing

Validate:

```text
GET /health
GET /api/symbols
GET /api/market/status
GET /api/market/live
GET /api/market/{symbol}
GET /api/market/{symbol}/history
```

Example BSE checks:

```bash
curl -s http://127.0.0.1:8000/api/market/AETHER_BSE | python -m json.tool
```

```bash
curl -s http://127.0.0.1:8000/api/market/live | python -c "import sys,json; d=json.load(sys.stdin); rows=[x for x in d['data'] if x['exchange']=='BSE']; print('BSE records:',len(rows)); [print(x['symbol'],x['ltp'],x['bid'],x['ask']) for x in rows]"
```

## 9. Integration Testing

Validate:

```text
TrueData
   |
   v
Collector
   |
   v
Parser / Quote Processing
   |
   v
PostgreSQL
```

and:

```text
PostgreSQL
   |
   v
FastAPI
   |
   v
React Dashboard
```

## 10. Negative Testing

Important negative scenarios:

- Invalid symbol
- Missing symbol mapping
- No live data yet
- Invalid TrueData payload
- Malformed JSON
- WebSocket disconnect
- Database unavailable
- Backend unavailable
- Frontend timeout
- Quote received before first trade

The quote-before-trade condition was observed for BSE symbols during validation and is handled without terminating the collector.

## 11. Performance Testing

The current work is functional/live-feed validation rather than a production capacity benchmark.

Future performance testing should measure:

- API response time
- Database query latency
- Collector ingestion rate
- PostgreSQL write throughput
- WebSocket stability
- Frontend refresh load
- Tick retention/storage growth

## 12. Security Testing

Validate before production:

- No secrets in repository
- No credentials in frontend code
- CORS restrictions
- API authentication/authorization
- TLS in production
- Database access controls
- Secret rotation
- No secrets in logs

## 13. Deferred Reliability Testing

Automatic WebSocket reconnect and subscription recovery are intentionally deferred.

Once implemented, test:

```text
Connection loss
     |
     v
Reconnect/backoff
     |
     v
Re-authenticate
     |
     v
Re-subscribe
     |
     v
Resume tick ingestion
```
