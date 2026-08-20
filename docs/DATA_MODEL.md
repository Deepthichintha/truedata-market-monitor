# TrueData Market Monitor - Data Model

## 1. Overview

PostgreSQL stores configured exchange symbols, real-time market ticks, and historical EOD bars.

Primary tables:

```text
symbols
live_ticks
historical_bars
```

The current validated configuration contains 50 NSE symbols and 10 BSE symbols.

## 2. Relationship

```text
symbols
   |
   +----> live_ticks
   |
   +----> historical_bars
```

Incoming TrueData records are associated with the configured `truedata_symbol_id`.

## 3. symbols

Purpose: stores configured market symbols and their exchange mapping.

Important fields:

| Field | Purpose |
|---|---|
| `id` | Internal primary key |
| `symbol` | Human-readable application symbol |
| `truedata_symbol_id` | TrueData identifier |
| `exchange` | `NSE` or `BSE` |
| `is_active` | Whether the symbol participates in ingestion/API output |
| `created_at` | Creation timestamp |

Current configuration:

```text
NSE: 50
BSE: 10
Active total: 60
```

## 4. NSE Symbol Configuration

NSE symbols are configured in:

```text
app/config/symbols.py
```

They are seeded with:

```text
exchange = NSE
```

## 5. BSE Symbol Configuration

The validated BSE test set is configured in:

```text
app/config/bse_symbols.py
```

The current BSE mapping is:

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

BSE records are seeded with:

```text
exchange = BSE
```

## 6. live_ticks

Purpose: stores normalized real-time market information.

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

`symbol_id` stores the TrueData symbol identifier used by the collector for incoming records.

A parsed trade creates a live tick. Subsequent Bid/Ask updates can update the latest live tick for that TrueData symbol.

## 7. Bid/Ask Data

The collector handles:

- TrueData regular `bidask` messages
- BSE `bidaskL2` messages

For BSE L2 data, the collector extracts the best available bid and ask levels and persists the corresponding price and quantity on the latest `live_ticks` record.

If a quote arrives before the first trade tick for a symbol, no live tick exists to update. The collector logs the condition and continues processing subsequent feed messages.

## 8. historical_bars

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

Current API timeframe:

```text
1D
```

## 9. Indexing and Constraints

The database model includes indexes/constraints around symbol identifiers and timestamps to support common latest-tick and historical queries.

Production performance should be verified using actual query plans and market-data workload.

## 10. Data Retention

`live_ticks` can grow rapidly during market hours. Production should define:

- Tick retention period
- Archive strategy
- Time-based partitioning if required
- Backup policy
- Storage monitoring

## 11. Data Flow

```text
TrueData trade / quote
        |
        v
Collector / Parser
        |
        v
live_ticks
        |
        v
FastAPI live endpoint
        |
        v
React dashboard
```
