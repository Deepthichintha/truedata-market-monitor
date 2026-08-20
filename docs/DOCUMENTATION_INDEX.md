# TrueData Market Monitor - Documentation Index

## Documentation Set

| Document | Purpose |
|---|---|
| `README.md` | Project overview, setup, architecture, APIs, exchange support, and validation |
| `docs/ARCHITECTURE.md` | Current architecture, component responsibilities, exchange flows, and production target |
| `docs/API.md` | REST API reference and examples |
| `docs/DATA_MODEL.md` | PostgreSQL tables, exchange mapping, and live quote persistence |
| `docs/OPERATIONS.md` | Setup, startup, validation, troubleshooting, and daily operation |
| `docs/SECURITY.md` | Secrets, database, API, frontend, and logging security |
| `docs/TESTING.md` | NSE/BSE validation, API, integration, frontend, negative, and production testing |
| `docs/PRODUCTION_READINESS.md` | Production hardening checklist and deferred work |
| `docs/ARCHITECTURE_DIAGRAM.mmd` | Standalone Mermaid architecture diagram source |
| `docs/DATA_FLOW_DIAGRAM.mmd` | Standalone Mermaid runtime data-flow diagram source |
| `docs/STOCK_MARKET_TERMINOLOGY.md` | Market-data terminology reference |

## Current Validated Scope

```text
NSE: 50 symbols
BSE: 10 symbols
Total: 60 active symbols
```

## Current Logical Flow

```text
TrueData WebSocket
        |
        v
Python Collector
        |
        +---- Trade Parser
        |
        +---- Bid/Ask / BidAskL2 Processing
        |
        v
PostgreSQL
        |
        v
FastAPI
        |
        v
React/Vite Dashboard
```

## Market Session

```text
Timezone: Asia/Kolkata
08:45 -> PRE_MARKET
09:15 -> OPEN
15:30 -> CLOSED
```

During `OPEN`:

```text
LIVE  -> recent tick available
STALE -> no recent tick within 60 seconds
```

## Local Services

Backend:

```text
http://127.0.0.1:8000
```

Frontend:

```text
http://127.0.0.1:5173
```

TrueData WebSocket:

```text
wss://push.truedata.in:8086
```

## Primary Database Tables

```text
symbols
live_ticks
historical_bars
```

## Exchange Configuration

NSE:

```text
app/config/symbols.py
```

BSE:

```text
app/config/bse_symbols.py
```

## Important Current Limitation

Automatic WebSocket reconnect, exponential backoff, and subscription recovery are intentionally deferred to the next production-hardening phase.
