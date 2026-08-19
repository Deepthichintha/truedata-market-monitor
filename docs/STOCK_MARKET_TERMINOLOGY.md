# TrueData Market Monitor - Stock Market Terminology Guide

This document is a beginner-friendly guide to the market terminology used by TrueData Market Monitor. It explains the database columns, how stock-market prices are formed, and the concepts a developer should understand before extending the application.

> This is an educational and software-architecture guide, not investment advice.

---

## 1. How a Stock Market Works

A stock exchange is a marketplace where buyers and sellers submit orders. When compatible buy and sell orders are matched, a trade is executed.

```text
Buyer places order
        |
        v
     Order Book
        ^
        |
Seller places order
        |
        v
Orders are matched
        |
        v
     TRADE
        |
        +----> Last Traded Price (LTP)
        +----> Last Traded Quantity (LTQ)
        +----> Volume
        +----> Turnover
```

The important distinction is:

- **Order** = an instruction to buy or sell.
- **Trade** = an order match that actually executes.
- **Tick** = a market-data event/update received by the application.

---

# 2. The Three Most Important Terms

## Bid

**Bid** is the best/highest price currently offered by a buyer.

Example:

```text
BUY SIDE

Quantity    Price
500         ₹999.90   <- Best Bid
800         ₹999.80
1200        ₹999.70
```

Remember:

> Bid = what a buyer is willing to pay.

## Ask

**Ask** is the best/lowest price currently offered by a seller.

```text
SELL SIDE

Price       Quantity
₹1000.10    400       <- Best Ask
₹1000.20    600
₹1000.30    900
```

Remember:

> Ask = what a seller is willing to accept.

## LTP

**LTP = Last Traded Price.**

It is the price at which the most recent trade was executed.

For example:

```text
Bid = ₹999.90
Ask = ₹1000.10

A trade executes at ₹1000.00

LTP = ₹1000.00
```

Therefore:

```text
Bid = buyer's best price
Ask = seller's best price
LTP = most recent executed trade price
```

---

# 3. Bid-Ask Spread

The spread is the difference between the best ask and best bid.

```text
Spread = Ask - Bid
```

Example:

```text
Ask = ₹1000.10
Bid = ₹999.90

Spread = ₹0.20
```

A smaller spread generally indicates better displayed liquidity, while a wider spread can indicate lower liquidity or greater uncertainty. Spread should be interpreted together with depth and trading activity.

---

# 4. Bid Quantity and Ask Quantity

If:

```text
bid = ₹999.90
bid_qty = 500
```

there are 500 units represented at the best bid price in the supplied market-data snapshot.

If:

```text
ask = ₹1000.10
ask_qty = 400
```

there are 400 units represented at the best ask price in that snapshot.

Our current application stores the best bid and ask information. It does **not** by itself represent a complete multi-level order book.

---

# 5. Order Book and Market Depth

An order book contains pending buy and sell orders.

Example:

```text
LEVEL     BID       BID QTY       ASK       ASK QTY
1         999.90       500       1000.10      400
2         999.80       800       1000.20      600
3         999.70      1200       1000.30      900
4         999.60      1500       1000.40     1100
5         999.50      1800       1000.50     1400
```

This is commonly called **market depth** or Level 2-style information, depending on the data product.

A future version of this application can add multiple bid/ask levels if the TrueData subscription and feed provide them.

---

# 6. `symbols` Table

The `symbols` table is the application's instrument master/mapping table.

| Column | Meaning |
|---|---|
| `id` | Internal database identifier for the symbol record |
| `symbol` | Human-readable trading symbol such as `RELIANCE` |
| `truedata_symbol_id` | TrueData instrument identifier used to map incoming feed data |
| `exchange` | Exchange associated with the instrument, currently NSE in the documented setup |
| `is_active` | Controls whether the symbol is active for collection/use |
| `created_at` | Timestamp when the symbol record was created |

### `id`

Internal primary-key value. It identifies the database record, not the stock in the external market.

### `symbol`

The familiar market symbol, for example:

```text
RELIANCE
TCS
INFY
HDFCBANK
```

### `truedata_symbol_id`

TrueData's identifier for the instrument. The application uses this mapping to associate an incoming TrueData identifier with the application's symbol.

### `exchange`

Identifies the exchange/instrument venue. The current documented setup uses NSE.

### `is_active`

A boolean control used to determine whether the symbol should be active in the application's collection/processing flow.

### `created_at`

Creation timestamp for the symbol record.

---

# 7. `live_ticks` Table

`live_ticks` is the core real-time market-data table.

It stores normalized market information received from the TrueData feed.

```text
TrueData WebSocket
        |
        v
Collector
        |
        v
Parser
        |
        v
live_ticks
```

The documented fields are:

| Column | Meaning |
|---|---|
| `id` | Unique database identifier for the tick record |
| `symbol_id` | Links the tick to a record in `symbols` |
| `timestamp` | Time associated with the market event/tick |
| `ltp` | Last Traded Price |
| `ltq` | Last Traded Quantity |
| `atp` | Average Traded Price |
| `total_volume` | Total traded quantity represented by the feed/session context |
| `open` | Opening price for the relevant session/data context |
| `high` | Highest price for the relevant session/data context |
| `low` | Lowest price for the relevant session/data context |
| `prev_close` | Previous trading-session close/reference price |
| `oi` | Open Interest, mainly relevant to derivatives |
| `prev_oi` | Previous Open Interest |
| `turnover` | Monetary value of traded activity as supplied by the feed |
| `bid` | Best bid price |
| `bid_qty` | Quantity represented at the best bid |
| `ask` | Best ask price |
| `ask_qty` | Quantity represented at the best ask |

---

## 8. `live_ticks.id`

A unique identifier for the database tick row.

It identifies the stored record, not the external market instrument.

---

## 9. `live_ticks.symbol_id`

Links the tick to the `symbols` table.

Example:

```text
symbols

id   symbol
1    RELIANCE
2    TCS
3    INFY
```

A live tick with:

```text
symbol_id = 1
```

belongs to RELIANCE.

Conceptually:

```text
symbols.id
     |
     +----> live_ticks.symbol_id
```

---

## 10. `live_ticks.timestamp`

The timestamp associated with the market event/tick.

This is important for:

- Ordering market events
- Detecting stale data
- Historical analysis
- Debugging feed interruptions
- Measuring ingestion latency

Example:

```text
Latest tick: 10:31:15
Current time: 10:31:20
Age: 5 seconds
```

The application can use the age of the latest data as part of feed-status detection.

---

## 11. `live_ticks.ltp`

Last Traded Price.

It answers:

> At what price did the latest trade execute?

Example:

```text
ltp = ₹1000
```

---

## 12. `live_ticks.ltq`

Last Traded Quantity.

It answers:

> How many units were involved in the latest trade?

Example:

```text
ltp = ₹1000
ltq = 200
```

means the latest trade was represented as 200 units at ₹1000.

---

## 13. `live_ticks.atp`

Average Traded Price.

ATP provides an average price measure for traded activity over the relevant feed/session context. It is useful for understanding where the market has traded on average.

---

## 14. `live_ticks.total_volume`

Total traded quantity represented by the feed/session context.

Do not confuse it with LTQ:

```text
LTQ          = quantity in the latest trade
Total Volume = accumulated traded quantity
```

Example:

```text
Latest trade quantity = 200
Session volume        = 500,000
```

---

## 15. `live_ticks.open`

The opening price for the relevant trading session/data context.

Example:

```text
Open = ₹995
```

---

## 16. `live_ticks.high`

Highest price reached during the relevant session/data context.

Example:

```text
High = ₹1020
```

---

## 17. `live_ticks.low`

Lowest price reached during the relevant session/data context.

Example:

```text
Low = ₹980
```

---

## 18. `live_ticks.prev_close`

Previous trading-session closing/reference price.

It is used to calculate common price-change displays.

```text
Change = LTP - Previous Close

Percentage Change =
(LTP - Previous Close) / Previous Close * 100
```

Example:

```text
Previous Close = ₹990
LTP            = ₹1010

Change         = +₹20
Percentage     ≈ +2.02%
```

---

# 19. Open Interest (`oi`)

Open Interest is mainly a derivatives concept.

It represents outstanding open derivative contracts, subject to the definition and feed conventions of the data provider.

Do not confuse:

```text
Volume = contracts traded during a period
OI     = contracts remaining open
```

For cash equities, OI is not normally the primary market-data field. It becomes much more important when the application expands into futures and options.

---

# 20. Previous Open Interest (`prev_oi`)

Previous Open Interest provides a reference point for comparing current OI with the previous value.

Example:

```text
Previous OI = 1,000,000
Current OI  = 1,200,000

Change in OI = +200,000
```

Combining price movement and OI is commonly used in derivatives analytics, but interpretations such as long buildup or short buildup should be treated as analytical heuristics rather than guaranteed conclusions.

---

# 21. Turnover

Turnover represents the monetary value of traded activity according to the feed's calculation/convention.

A simplified intuition is:

```text
Turnover ≈ traded price × traded quantity
```

Example:

```text
₹1000 × 100,000 shares
= ₹100,000,000
= ₹10 crore
```

Exact exchange/feed calculations can differ, so the provider's field definition should be treated as authoritative.

---

# 22. Bid (`bid`)

Best bid price.

Example:

```text
Bid = ₹999.90
```

This means the highest displayed buy price in the supplied quote snapshot is ₹999.90.

---

# 23. Bid Quantity (`bid_qty`)

Quantity associated with the best bid in the supplied market-data snapshot.

Example:

```text
Bid     = ₹999.90
Bid Qty = 500
```

---

# 24. Ask (`ask`)

Best ask price.

Example:

```text
Ask = ₹1000.10
```

This means the lowest displayed sell price in the supplied quote snapshot is ₹1000.10.

---

# 25. Ask Quantity (`ask_qty`)

Quantity associated with the best ask in the supplied market-data snapshot.

Example:

```text
Ask     = ₹1000.10
Ask Qty = 400
```

---

# 26. `historical_bars` Table

The `historical_bars` table represents aggregated historical market data rather than individual real-time ticks.

Typical documented fields include:

| Column | Meaning |
|---|---|
| `id` | Unique database identifier |
| `symbol_id` | Related instrument in `symbols` |
| `timestamp` | Period/date represented by the bar |
| `timeframe` | Bar timeframe, currently documented as `1D` |
| `open` | Opening price of the bar |
| `high` | Highest price of the bar |
| `low` | Lowest price of the bar |
| `close` | Closing price of the bar |
| `volume` | Volume represented by the bar |
| `oi` | Open interest where applicable/supplied |
| `created_at` | When the historical record was stored |

A daily bar can be represented as:

```text
Date       Open   High   Low   Close   Volume
Aug 18     990    1010   985   1005    2.4M
Aug 19    1005    1030   995   1025    3.1M
```

Historical bars are the foundation for candlestick charts and many technical calculations.

---

# 27. OHLC

OHLC means:

```text
O = Open
H = High
L = Low
C = Close
```

For a daily bar:

```text
Open  = ₹990
High  = ₹1020
Low   = ₹980
Close = ₹1010
```

A candlestick visualizes these four values.

---

# 28. Volume vs Turnover

These are related but different.

```text
Volume   -> how many units were traded
Turnover -> monetary value of trading activity
```

Example:

```text
Price  = ₹1000
Volume = 100,000

Approximate value = ₹10 crore
```

---

# 29. Tick

A tick is an individual market-data update/event received by the application.

For example:

```text
10:00:01 -> ₹1000.00
10:00:02 -> ₹1000.20
10:00:03 -> ₹1000.10
```

Depending on the feed, not every tick necessarily represents a brand-new executed trade; it is important to use the provider's feed semantics when interpreting individual messages.

---

# 30. Liquidity

Liquidity describes how easily a security can be bought or sold without causing significant price impact.

Common indicators include:

- Trading volume
- Turnover
- Bid-ask spread
- Order-book depth
- Trading frequency

A narrow spread and deep displayed book often indicate stronger displayed liquidity, but liquidity should be evaluated using multiple measures.

---

# 31. Slippage

Slippage is the difference between an expected execution price and the actual execution price.

It can become significant when:

- Order size is large
- Liquidity is low
- Market volatility is high
- The spread is wide
- Price moves rapidly

---

# 32. Market Order vs Limit Order

### Market Order

An instruction to execute immediately at available market prices.

### Limit Order

An instruction to execute only at the specified price or better.

Example:

```text
BUY 100 RELIANCE LIMIT ₹1000
```

means the buyer does not want to pay more than ₹1000, subject to exchange/order rules.

---

# 33. Price Change

A common dashboard calculation is:

```text
Absolute Change = LTP - Previous Close

Percentage Change =
(LTP - Previous Close) / Previous Close × 100
```

Example:

```text
Previous Close = ₹990
LTP            = ₹1010

Change = +₹20
Change % ≈ +2.02%
```

---

# 34. Circuit Limits / Price Bands

Exchanges can apply price bands or market-wide circuit mechanisms to control extreme price movement under defined rules.

A monitoring application should obtain the applicable security/market limits from an authoritative source rather than hard-coding a universal percentage.

The dashboard can eventually display:

```text
Previous Close  ₹1000
Upper Band      ₹1100
Lower Band      ₹900
Current Price   ₹1080
```

and alert when the price approaches a configured limit.

---

# 35. 52-Week High and Low

The 52-week high is the highest relevant price over the preceding 52 weeks, while the 52-week low is the lowest.

Example:

```text
52W High = ₹1250
52W Low  = ₹780
```

A market monitor can use these values for breakout/record-high alerts.

Corporate-action adjustments and provider definitions must be respected when calculating or displaying these values.

---

# 36. Market Breadth

Market breadth compares the number of advancing and declining securities.

Example:

```text
Advances  = 1400
Declines  = 900
Unchanged = 100
```

A simple advance/decline ratio is:

```text
Advances / Declines
```

Breadth provides market-wide context beyond an individual stock.

---

# 37. Market Index

An index represents a selected basket of securities using an index methodology.

Examples include broad-market and sector indices.

A future dashboard can monitor:

```text
NIFTY 50
BANK NIFTY
NIFTY IT
NIFTY AUTO
NIFTY PHARMA
```

The exact index calculation methodology should come from the index provider/exchange.

---

# 38. Sectors

Stocks can be grouped by industry/sector.

Example:

```text
IT
BANKING
AUTO
PHARMA
ENERGY
FMCG
```

Sector-level performance helps answer:

> Is a price move specific to one company, or is the whole sector moving?

---

# 39. Derivatives Terms

When the application expands to futures and options, these terms become important.

### Futures

A standardized derivative contract whose value is linked to an underlying instrument/index.

### Options

Contracts giving the holder rights defined by the contract, subject to the option type and exchange rules.

### Strike Price

The price specified in an option contract.

### Expiry

The contract's expiration date.

### Open Interest

Outstanding open derivative contracts.

### Change in OI

Difference between current and reference OI.

### Implied Volatility (IV)

A market-derived measure related to expected volatility embedded in option prices.

### Put-Call Ratio (PCR)

A ratio that can be calculated using selected put and call quantities, commonly OI or volume depending on the methodology.

### Max Pain

A derived option-market metric based on option open interest and strike prices. It is an analytical concept, not a guaranteed price forecast.

---

# 40. Technical Analysis Terms

These are calculated from historical price/volume data rather than directly being basic exchange quote fields.

### SMA

Simple Moving Average.

Example:

```text
20-day SMA = average of the last 20 selected closing prices
```

### EMA

Exponential Moving Average. Recent observations receive greater weight than older observations.

### RSI

Relative Strength Index. A momentum indicator commonly displayed on a 0-100 scale.

Common reference zones are 70 and 30, but they should not be treated as automatic buy/sell rules.

### MACD

Moving Average Convergence Divergence. A trend/momentum indicator derived from moving averages.

### Bollinger Bands

A volatility visualization consisting of a middle moving average and upper/lower bands derived using a volatility measure.

---

# 41. How These Concepts Fit Our Application

```text
                         TRUE DATA
                            |
                            v
                    WebSocket Messages
                            |
                            v
                   TrueData Collector
                            |
                            v
                     Trade Parser
                            |
                            v
                       live_ticks
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
        LTP              Bid/Ask          Volume
          |                 |                 |
          |                 v                 |
          |             Spread               |
          |                 |                 |
          +-----------------+-----------------+
                            |
                            v
                       FastAPI API
                            |
                            v
                    React Dashboard
```

Historical data follows a different path:

```text
Historical Data
      |
      v
historical_bars
      |
      v
Candlestick / Charts
      |
      v
Indicators
      |
      +---- SMA
      +---- EMA
      +---- RSI
      +---- MACD
      +---- Bollinger Bands
```

---

# 42. What a Developer Should Understand First

## Level 1 - Essential

Learn these first:

```text
Stock
Exchange
Order
Trade
Tick
LTP
Bid
Ask
Bid Quantity
Ask Quantity
Spread
Volume
Turnover
Open
High
Low
Close
Previous Close
```

## Level 2 - Application-specific

```text
WebSocket
TrueData Symbol ID
symbols table
live_ticks table
historical_bars table
Market Status
Stale Feed
```

## Level 3 - Market Analytics

```text
Market Depth
Liquidity
Slippage
52-week High/Low
Price Bands
Market Breadth
Indices
Sectors
Gainers / Losers
```

## Level 4 - Advanced

```text
Futures
Options
OI
Change in OI
IV
PCR
Max Pain
SMA
EMA
RSI
MACD
Bollinger Bands
```

---

# 43. Practical Example: One RELIANCE Snapshot

Imagine the application receives:

```text
Symbol        = RELIANCE
LTP           = ₹1000
LTQ           = 200
ATP           = ₹995
Volume        = 500,000
Open          = ₹990
High          = ₹1010
Low           = ₹985
Previous Close= ₹992
Bid           = ₹999.90
Bid Qty       = 500
Ask           = ₹1000.10
Ask Qty       = 400
```

A human interpretation is:

> RELIANCE's latest traded price is ₹1000. The most recent trade involved 200 units. The stock has traded 500,000 units in the relevant session context. It opened at ₹990, reached ₹1010, and has traded as low as ₹985. The previous close was ₹992. The best displayed bid is ₹999.90 for 500 units and the best displayed ask is ₹1000.10 for 400 units. The displayed bid-ask spread is ₹0.20.

That one record is the core information our current live dashboard is consuming.

---

# 44. Important Development Rules

When extending this application:

1. Do not assume every field is a trade execution field.
2. Treat the TrueData feed specification as authoritative for message semantics.
3. Do not calculate exchange-defined values using assumptions when an authoritative feed field exists.
4. Keep raw/provider identifiers mapped correctly to internal symbols.
5. Store timestamps consistently and document timezone assumptions.
6. Do not expose provider credentials in frontend code or logs.
7. Distinguish live ticks from aggregated historical bars.
8. Do not treat technical indicators as guaranteed trading signals.
9. Do not hard-code exchange rules that can change; make market calendars and applicable limits data-driven.
10. For production, monitor feed freshness, reconnects, ingestion rate, database health, and API latency.

---

# 45. Quick Reference

```text
LTP          = Last traded price
LTQ          = Quantity in last trade
Bid          = Best displayed buyer price
Bid Qty      = Quantity at best bid
Ask          = Best displayed seller price
Ask Qty      = Quantity at best ask
Spread       = Ask - Bid
ATP          = Average traded price
Volume       = Traded quantity
Turnover     = Monetary value of trading activity
Open         = Session opening price
High         = Session high
Low          = Session low
Close        = Session closing price
Prev Close   = Previous session close/reference price
OI           = Open interest, mainly derivatives
Prev OI      = Previous open interest
Tick         = Market-data event/update
Order        = Instruction to buy/sell
Trade        = Matched executed transaction
Depth        = Multiple order-book levels
Liquidity    = Ease of trading with limited price impact
Slippage     = Difference between expected and actual execution price
```

---

# 46. Relationship to the Project Documentation

Related documents:

- `README.md` - project overview and setup
- `docs/ARCHITECTURE.md` - system architecture
- `docs/API.md` - API reference
- `docs/DATA_MODEL.md` - database model
- `docs/OPERATIONS.md` - operational runbook
- `docs/SECURITY.md` - security guidance
- `docs/TESTING.md` - testing strategy
- `docs/PRODUCTION_READINESS.md` - production checklist

This terminology guide should be used as the beginner reference before working on market-data features such as market depth, alerts, charts, derivatives, or analytics.
