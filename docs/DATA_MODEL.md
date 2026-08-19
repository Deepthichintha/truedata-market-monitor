# TrueData Market Monitor - Data Model

## 1. Overview

PostgreSQL stores the application's configured symbols, real-time ticks, and historical EOD bars.

Primary tables:

```text
symbols
live_ticks
historical_bars
```

## 2. Relationship

```text
symbols
   |
   +----> live_ticks
   |
   +----> historical_bars
```

The TrueData symbol identifier is used to connect incoming market data to the configured symbol records.

## 3. symbols

Purpose: stores configured market symbols.

Important fields:

| Field | Purpose |
|---|---|
| `id` | Internal primary key |
| `symbol` | Human-readable market symbol |
| `truedata_symbol_id` | TrueData identifier |
| `exchange` | Exchange, currently NSE |
| `is_active` | Whether symbol is active |
| `created_at` | Creation timestamp |

## 4. live_ticks

Purpose: stores normalized real-time trade information.

Important fields:

```text
id
symbol_id
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

A new parsed trade can result in a new `live_ticks` record.

## 5. historical_bars

Purpose: stores historical end-of-day market bars.

Important fields:

```text
id
symbol_id
timestamp
timeframe
open
high
low
close
volume
oi
created_at
```

The current API uses the `1D` timeframe.

## 6. Indexing

The database model includes indexes/constraints around symbol identifiers and timestamps to support common market queries.

Production performance should be verified using actual query plans and workload data.

## 7. Data Retention

`live_ticks` can grow rapidly during market hours. Production should define:

- Tick retention period
- Archive strategy
- Time-based partitioning if required
- Backup policy
- Storage monitoring

## 8. Data Flow

```text
TrueData trade
      |
      v
Parser
      |
      v
live_ticks
      |
      v
FastAPI live endpoint
      |
      v
Dashboard
```
