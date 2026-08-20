# TrueData Market Monitor - Operations Runbook

## 1. Scope

This runbook covers local operation and validation of the TrueData Market Monitor with:

```text
50 NSE symbols
10 BSE symbols
60 active symbols total
```

Automatic WebSocket reconnect is intentionally not enabled yet and remains a production-hardening item.

## 2. Prerequisites

- Python 3.11+ recommended
- PostgreSQL
- Node.js and npm
- Valid TrueData credentials
- Network access to `wss://push.truedata.in:8086`

## 3. Backend Setup

Create a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 4. Environment

Create `.env` from `.env.example` and configure:

```text
TRUEDATA_USERNAME=
TRUEDATA_PASSWORD=
DATABASE_URL=
```

Never commit the real `.env` file.

## 5. Database Initialization

Initialize tables:

```bash
python -m app.database.init_db
```

Seed both exchange configurations:

```bash
python -m app.database.seed
```

Expected current result:

```text
NSE symbols added: 0 or the number of newly added NSE records
BSE symbols added: 0 or the number of newly added BSE records
Total active symbols: 60
```

Verify BSE mappings:

```bash
python -c "from app.database.connection import SessionLocal; from app.database.models import Symbol; db=SessionLocal(); rows=db.query(Symbol).filter(Symbol.exchange=='BSE').order_by(Symbol.id).all(); print([(x.symbol,x.truedata_symbol_id,x.exchange) for x in rows]); db.close()"
```

## 6. Start Collector

```bash
python -u -m app.services.truedata_collector
```

Expected sequence:

```text
Load configuration
     |
     v
Load active symbols
     |
     v
Connect to TrueData
     |
     v
Subscribe symbols
     |
     v
Receive heartbeat / trade / quote messages
     |
     v
Parse and normalize data
     |
     v
Persist live ticks
```

The collector is a continuous process during a live-data session. Keep the terminal/process running while live data is required.

## 7. Validate NSE

The collector should report:

```text
Mode: NSE NORMAL
Symbols loaded: 50
Subscription confirmed
Symbols added: 50
```

Validate the API:

```bash
curl -s http://127.0.0.1:8000/api/market/live
```

## 8. Validate BSE

The validated BSE set contains 10 symbols:

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

The collector should report:

```text
Mode: BSE TEST
Symbols loaded: 10
Subscription confirmed
Symbols added: 10
Total subscribed: 10
```

The BSE feed was validated with live trade data and Bid/Ask L2 data.

Validate BSE records:

```bash
curl -s http://127.0.0.1:8000/api/market/live | python -c "import sys,json; d=json.load(sys.stdin); rows=[x for x in d['data'] if x['exchange']=='BSE']; print('BSE records:',len(rows)); [print(f\"{x['symbol']:<20} LTP={x['ltp']:<10} BID={x['bid']:<10} ASK={x['ask']:<10}\") for x in rows]"
```

Expected validated result:

```text
BSE records: 10
```

## 9. Start API

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Validate:

```bash
curl http://127.0.0.1:8000/health
```

## 10. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The local dashboard normally runs on:

```text
http://127.0.0.1:5173
```

The dashboard refreshes live data every five seconds.

## 11. Frontend Exchange Validation

The dashboard should show:

```text
ALL (60)
NSE (50)
BSE (10)
```

Expected behavior:

```text
ALL -> 60 records
NSE -> 50 records
BSE -> 10 records
```

The BSE table should display LTP, ATP, volume, OHLC, Bid, Ask, quantities, and timestamp when those values are available.

## 12. Market Status

```bash
curl -s http://127.0.0.1:8000/api/market/status
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

During `OPEN`, a feed is:

```text
LIVE  -> latest tick <= 60 seconds old
STALE -> latest tick > 60 seconds old
```

## 13. Troubleshooting

### Backend does not start

Check Python dependencies, `.env`, PostgreSQL, and `DATABASE_URL`.

### TrueData authentication failure

Verify `TRUEDATA_USERNAME` and `TRUEDATA_PASSWORD` without exposing their values.

### No live market data

Check, in order:

1. PostgreSQL is running.
2. Collector is running.
3. TrueData connection succeeds.
4. Symbols are subscribed.
5. TrueData mappings are present.
6. `live_ticks` contains recent rows.
7. `/api/market/live` returns records.

### BSE symbol shows no data

Check:

1. The BSE symbol exists in `symbols`.
2. `exchange` is `BSE`.
3. The TrueData ID matches `app/config/bse_symbols.py`.
4. The collector subscribed successfully.
5. A trade tick has arrived.
6. `/api/market/live` contains the symbol.

A Bid/Ask update can arrive before the first trade. In that case the collector may log `No LiveTick found` until the first trade creates the base record.

### Market status is STALE

Check the collector, WebSocket connection, latest `live_ticks` timestamp, and system time/timezone.

```sql
SELECT * FROM live_ticks ORDER BY timestamp DESC LIMIT 10;
```

### Frontend reports backend unavailable

Run:

```bash
curl http://127.0.0.1:8000/health
```

Then inspect browser network errors and the frontend API configuration.

## 14. Production Operations

Before production, add:

- Process supervision
- Automatic WebSocket reconnect/backoff
- Subscription recovery
- Structured logging
- Centralized logs
- Metrics and alerts
- Database backups
- Storage monitoring
- Tick ingestion monitoring
- Stale-feed alerts
- Deployment health checks
