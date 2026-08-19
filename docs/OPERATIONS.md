# TrueData Market Monitor - Operations Runbook

## 1. Prerequisites

- Python 3.11+ recommended
- PostgreSQL
- Node.js and npm
- Valid TrueData credentials
- Network access to the TrueData WebSocket

## 2. Backend Setup

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

## 3. Environment

Create local configuration from the example:

```bash
cp .env.example .env
```

Configure at minimum:

```text
TRUEDATA_USERNAME=
TRUEDATA_PASSWORD=
DATABASE_URL=
```

Never commit the real `.env` file.

## 4. Database Initialization

Initialize tables:

```bash
python -m app.database.init_db
```

Seed symbols:

```bash
python -m app.database.seed
```

## 5. Start Collector

```bash
python -m app.services.truedata_collector
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
Receive heartbeat/trades
     |
     v
Parse trades
     |
     v
Insert live ticks
```

## 6. Start API

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Validate:

```bash
curl http://127.0.0.1:8000/health
```

## 7. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

## 8. Troubleshooting

### Backend does not start

Check Python dependencies, `.env`, PostgreSQL availability, and `DATABASE_URL`.

### TrueData authentication failure

Verify `TRUEDATA_USERNAME` and `TRUEDATA_PASSWORD` without exposing them in logs.

### No live market data

Check, in order:

1. PostgreSQL is running.
2. Collector is running.
3. TrueData connection succeeds.
4. Symbols are subscribed.
5. TrueData mappings are present.
6. `live_ticks` contains recent rows.
7. `/api/market/live` returns data.

### Market status is STALE

Check the collector, WebSocket connection, latest `live_ticks` timestamp, and system time.

Example:

```sql
SELECT * FROM live_ticks ORDER BY timestamp DESC LIMIT 10;
```

### Frontend reports backend unavailable

Run:

```bash
curl http://127.0.0.1:8000/health
```

Then inspect browser network errors and frontend API configuration.

## 9. Production Operations

Recommended production controls:

- Process supervision for collector
- Automatic restart
- WebSocket reconnect/backoff
- Structured logging
- Centralized logs
- Metrics and alerts
- Database backups
- Storage monitoring
- Tick ingestion monitoring
- Stale-feed alerts
