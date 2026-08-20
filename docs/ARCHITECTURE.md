# TrueData Market Monitor - System Architecture

## 1. Purpose

This document describes the current local proof-of-concept architecture for TrueData Market Monitor, including NSE and BSE live-market ingestion, PostgreSQL persistence, FastAPI APIs, and the React/Vite dashboard.

The current implementation has been validated end-to-end with **50 NSE symbols + 10 BSE symbols = 60 active symbols**.

Automatic WebSocket reconnect/recovery is intentionally deferred and is tracked as future production hardening.

## 2. Current Architecture

```text
                         +----------------------+
                         |       TrueData       |
                         |   WebSocket Feed     |
                         |  NSE + BSE Equity    |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |  TrueData Collector  |
                         |       Python         |
                         |                      |
                         | - Load active symbols|
                         | - Connect/auth       |
                         | - Subscribe          |
                         | - Receive ticks      |
                         | - Receive Bid/Ask    |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Trade / Feed Parser  |
                         |                      |
                         | Normalize and validate|
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      PostgreSQL      |
                         |                      |
                         | symbols              |
                         | live_ticks           |
                         | historical_bars      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |       FastAPI        |
                         |     REST Backend     |
                         |       :8000          |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |    React + Vite      |
                         |      Dashboard       |
                         |       :5173          |
                         +----------------------+
                                    |
                                    v
                               Web Browser
```

## 3. Component Responsibilities

### TrueData

External real-time market-data provider.

WebSocket endpoint:

```text
wss://push.truedata.in:8086
```

Validated equity segments include both NSE and BSE feeds.

### TrueData Collector

File:

```text
app/services/truedata_collector.py
```

Responsibilities:

- Read TrueData credentials from environment configuration
- Load active NSE/BSE symbols from PostgreSQL
- Establish the WebSocket connection
- Subscribe to configured symbols
- Handle heartbeat messages
- Handle subscription confirmations
- Process trade messages
- Process regular Bid/Ask messages
- Process BSE `bidaskL2` messages
- Persist normalized live data
- Handle parsing/database errors
- Close the connection cleanly on shutdown

The collector is a long-running process.

### TrueData Parser

File:

```text
app/services/truedata_parser.py
```

Responsibilities:

- Validate trade payload structure
- Parse timestamps
- Convert numeric values
- Normalize trade fields for database persistence

### Database Layer

Files under:

```text
app/database/
```

Primary tables:

- `symbols`
- `live_ticks`
- `historical_bars`

The `symbols.exchange` field identifies `NSE` or `BSE`.

### FastAPI

Files:

```text
app/main.py
app/api/market.py
```

Responsibilities:

- Health checks
- Symbol access
- Live market data
- Individual symbol data
- Historical EOD data
- Market-session status
- Stale-feed detection

### React/Vite Frontend

Primary application:

```text
frontend/src/App.jsx
```

The dashboard consumes the FastAPI APIs and supports:

- NSE and BSE live data
- ALL / NSE / BSE exchange filtering
- Symbol search
- LTP, ATP, OHLC, volume
- Bid/Ask
- Market status
- Historical data selection
- Automatic five-second refresh

## 4. Exchange Configuration

### NSE

Current validated set:

```text
50 symbols
```

Configured in:

```text
app/config/symbols.py
```

TrueData subscription uses the human-readable NSE exchange symbols.

### BSE

Current validated set:

```text
10 symbols
```

Configured in:

```text
app/config/bse_symbols.py
```

The validated BSE symbols use the TrueData `_BSE` naming convention and their mapped TrueData IDs.

Current BSE test set:

| Symbol | TrueData ID |
|---|---:|
| AARTIIND_BSE | 410001512 |
| ADANIPORTS_BSE | 410002671 |
| AETHER_BSE | 410004487 |
| APOLLOHOSP_BSE | 410000697 |
| ASHIANA_BSE | 410001474 |
| ATUL_BSE | 410000078 |
| AUBANK_BSE | 410003594 |
| BAJAJ-AUTO_BSE | 410002707 |
| CARERATING_BSE | 410002923 |
| CCL_BSE | 410001265 |

## 5. Live Data Handling

The collector receives multiple TrueData message types.

### Trade

Trade messages are parsed and stored as `live_ticks` records.

### Bid/Ask

Regular Bid/Ask messages update the latest stored tick for the corresponding TrueData symbol ID.

### BSE Bid/Ask L2

BSE validation demonstrated TrueData `bidaskL2` messages. The collector extracts the best bid/bid quantity and best ask/ask quantity and carries them onto the latest live tick.

If a quote arrives before a trade has been persisted for a symbol, the collector logs that no live tick exists yet and waits for the next applicable update. This was observed for ATUL_BSE during initial testing and later resolved once its trade tick arrived.

## 6. Market Session Logic

Market-session calculations use explicit India Standard Time:

```text
Timezone: Asia/Kolkata
```

Configured NSE equity session:

```text
08:45 - Pre-market
09:15 - Regular market open
15:30 - Regular market close
```

The API distinguishes:

```text
PRE_MARKET
OPEN
CLOSED
```

During regular `OPEN`, feed status is additionally classified as:

```text
LIVE
STALE
```

The stale threshold is:

```text
60 seconds
```

This prevents the server's local timezone from incorrectly determining Indian market hours when deployed on a UTC or other-timezone host.

## 7. Runtime Data Flow

```text
TrueData WebSocket
       |
       | trade / bidask / bidaskL2 / heartbeat
       v
TrueData Collector
       |
       +----> Trade Parser
       |
       +----> Quote processing
       |
       v
PostgreSQL live_ticks
       |
       v
FastAPI REST API
       |
       +----> /api/market/live
       +----> /api/market/status
       +----> /api/market/{symbol}
       +----> /api/market/{symbol}/history
       |
       v
React/Vite Dashboard
       |
       +----> ALL / NSE / BSE filter
       +----> Symbol search
       +----> Live table
```

## 8. Target Production Architecture

The following is a recommended future architecture, not a claim that all components are currently deployed.

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

## 9. Reliability Recommendations

The current collector intentionally does not include automatic reconnect yet.

Production hardening should add:

- Automatic WebSocket reconnect
- Exponential backoff
- Subscription recovery
- Collector health monitoring
- Process supervision
- Structured logging
- Centralized logs
- Metrics and alerting
- Database retry handling
- Backup and restore procedures

## 10. Scalability Considerations

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
