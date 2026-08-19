# TrueData Market Monitor - System Architecture

## 1. Purpose

This document describes the current architecture, components, runtime data flow, database flow, and recommended production target architecture for TrueData Market Monitor.

## 2. Current Architecture

```text
TrueData WebSocket
       |
       v
Python TrueData Collector
       |
       v
TrueData Trade Parser
       |
       v
PostgreSQL
       |
       v
FastAPI REST API
       |
       v
React + Vite Dashboard
```

## 3. Component Responsibilities

### TrueData

External market-data provider. The collector connects to:

```text
wss://push.truedata.in:8086
```

### TrueData Collector

File: `app/services/truedata_collector.py`

Responsibilities:

- Read credentials from environment configuration
- Load active symbols
- Connect to TrueData WebSocket
- Subscribe to symbols
- Receive heartbeat and trade messages
- Pass trade messages to the parser
- Persist normalized ticks
- Handle connection errors and cleanup

### TrueData Parser

File: `app/services/truedata_parser.py`

Responsibilities:

- Validate trade payloads
- Validate expected field structure
- Parse timestamps
- Convert numeric values
- Normalize the market tick representation

### Database Layer

Files under `app/database/` manage SQLAlchemy connectivity, models, initialization, and symbol seeding.

Primary tables:

- `symbols`
- `live_ticks`
- `historical_bars`

### FastAPI

Files:

- `app/main.py`
- `app/api/market.py`

Responsibilities:

- Health endpoint
- Symbol endpoint
- Live market data
- Historical market data
- Market/feed status
- Stale-feed detection

### React/Vite Frontend

The dashboard consumes the FastAPI APIs, displays live market data and status, supports symbol search, and retrieves historical data.

## 4. Runtime Data Flow

```text
TrueData
   |
   | WebSocket trade message
   v
Collector
   |
   v
Parser
   |
   | normalized tick
   v
PostgreSQL live_ticks
   |
   v
FastAPI
   |
   | JSON
   v
React Dashboard
```

## 5. Market Status Logic

The application evaluates NSE market status using the configured trading window:

```text
Open: 09:15
Close: 15:30
Stale threshold: 60 seconds
```

The resulting status is:

- `LIVE` - market is open and recent ticks are available
- `STALE` - market is open but the latest tick exceeds the stale threshold
- `CLOSED` - outside the configured market window

## 6. Target Production Architecture

The following is a recommended target architecture, not a claim that all components are currently deployed.

```text
                         +----------------+
                         |     Users      |
                         +-------+--------+
                                 |
                                 v
                         +----------------+
                         | HTTPS / LB     |
                         +-------+--------+
                                 |
                  +--------------+--------------+
                  |                             |
                  v                             v
           +-------------+               +-------------+
           | React       |               | FastAPI     |
           | Frontend    |               | Backend     |
           +-------------+               +------+------+
                                                |
                                                v
                                         +-------------+
                                         | PostgreSQL  |
                                         +-------------+

        TrueData
            |
            v
     +-------------+
     | Collector   |
     | Worker      |
     +------+------+
            |
            v
       PostgreSQL
```

## 7. Reliability Recommendations

Production should add:

- WebSocket reconnect and exponential backoff
- Subscription recovery
- Collector health monitoring
- Process supervision
- Database retry handling
- Structured logging
- Centralized logs
- Metrics and alerting
- Database backup and restore procedures

## 8. Scalability Considerations

The collector writes real-time ticks to PostgreSQL. At higher volumes, review:

- Tick ingestion rate
- PostgreSQL write throughput
- Index size
- Storage growth
- Query latency
- Connection pool sizing
- Retention policy
- Time-based partitioning

A future stream-based architecture could introduce a message queue between the collector and downstream consumers.
