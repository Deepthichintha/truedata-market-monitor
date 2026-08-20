# TrueData Market Monitor

TrueData Market Monitor is a real-time market-monitoring proof of concept that receives live NSE and BSE equity data from TrueData, normalizes and stores the data in PostgreSQL, exposes REST APIs through FastAPI, and displays the live market through a React/Vite dashboard.

The current implementation has been validated end-to-end with **50 NSE symbols + 10 BSE symbols = 60 active symbols**.

> **Current status:** Functional local POC. Automatic WebSocket reconnect/recovery is intentionally deferred to the next production-hardening phase.

---

## 1. Current Scope

| Capability | Status |
|---|---|
| TrueData WebSocket | ✅ Validated |
| NSE live ingestion | ✅ 50 symbols |
| NSE Bid/Ask | ✅ Validated |
| BSE live ingestion | ✅ 10 symbols |
| BSE Bid/Ask L2 | ✅ Validated |
| PostgreSQL persistence | ✅ Validated |
| FastAPI live APIs | ✅ Validated |
| IST market session | ✅ Validated |
| 08:45 pre-market handling | ✅ Validated |
| React/Vite dashboard | ✅ Validated |
| ALL/NSE/BSE filters | ✅ Validated |
| Automatic reconnect | ⏸️ Deferred |
| Production deployment | ⏸️ Not yet implemented |

---

## 2. System Architecture

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
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Trade / Quote Parser |
                         | BidAsk / BidAskL2    |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      PostgreSQL      |
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
```

Mermaid sources:

- `docs/ARCHITECTURE_DIAGRAM.mmd`
- `docs/DATA_FLOW_DIAGRAM.mmd`

Detailed architecture: `docs/ARCHITECTURE.md`

---

## 3. Data Flow

```text
TrueData WebSocket
        |
        | trade / bidask / bidaskL2 / heartbeat
        v
TrueData Collector
        |
        +----> Trade Parser
        +----> Quote Processing
        |
        v
PostgreSQL live_ticks
        |
        v
FastAPI
        |
        +----> /api/market/live
        +----> /api/market/status
        +----> /api/market/{symbol}
        +----> /api/market/{symbol}/history
        |
        v
React/Vite Dashboard
        |
        +----> ALL / NSE / BSE
        +----> Search
        +----> Live table
```

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Frontend Build | Vite |
| Backend | Python |
| API | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Market Data | TrueData |
| Market Protocol | WebSocket |
| Configuration | Pydantic Settings + `.env` |
| API Documentation | OpenAPI / Swagger |
| Package Management | pip / npm |

---

## 5. Repository Structure

```text
truedata-market-monitor/
|
+-- app/
|   +-- api/
|   |   +-- market.py
|   +-- config/
|   |   +-- settings.py
|   |   +-- symbols.py
|   |   +-- bse_symbols.py
|   +-- database/
|   |   +-- connection.py
|   |   +-- init_db.py
|   |   +-- models.py
|   |   +-- seed.py
|   +-- services/
|       +-- smarttheta.py
|       +-- truedata_collector.py
|       +-- truedata_parser.py
|   +-- main.py
|
+-- frontend/
|   +-- src/
|       +-- App.jsx
|       +-- App.css
|
+-- docs/
|   +-- API.md
|   +-- ARCHITECTURE.md
|   +-- ARCHITECTURE_DIAGRAM.mmd
|   +-- DATA_FLOW_DIAGRAM.mmd
|   +-- DATA_MODEL.md
|   +-- DOCUMENTATION_INDEX.md
|   +-- OPERATIONS.md
|   +-- PRODUCTION_READINESS.md
|   +-- SECURITY.md
|   +-- TESTING.md
|   +-- STOCK_MARKET_TERMINOLOGY.md
|
+-- .env.example
+-- .gitignore
+-- requirements.txt
+-- README.md
```

---

## 6. Exchange Support

### NSE

Configured in:

```text
app/config/symbols.py
```

Current validated set:

```text
50 symbols
```

### BSE

Configured in:

```text
app/config/bse_symbols.py
```

Current validated set:

```text
10 symbols
```

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

The BSE symbols were selected from the current SmartTheta application and validated through TrueData subscription.

---

## 7. TrueData Integration

WebSocket endpoint:

```text
wss://push.truedata.in:8086
```

Collector responsibilities:

- Load credentials
- Load active NSE/BSE symbols
- Connect and authenticate
- Subscribe symbols
- Handle heartbeat messages
- Handle subscription confirmations
- Process trade messages
- Process regular Bid/Ask messages
- Process BSE `bidaskL2` messages
- Persist live data
- Handle processing/database errors
- Close cleanly on shutdown

Start the collector:

```bash
python -u -m app.services.truedata_collector
```

The collector is a long-running process and should remain running while live data is required.

---

## 8. Bid/Ask Handling

Trade messages create the base `live_ticks` record.

Regular Bid/Ask messages update the latest tick for the corresponding TrueData symbol.

BSE `bidaskL2` messages are processed to extract the best bid/ask price and quantity and update the latest tick.

If a quote arrives before the first trade, the collector logs that no base `LiveTick` exists yet and continues. Once the first trade arrives, subsequent quote updates can be persisted.

---

## 9. Market Session

The application explicitly uses:

```text
Asia/Kolkata
```

Session schedule:

```text
08:45 - PRE_MARKET
09:15 - OPEN
15:30 - CLOSED
```

During `OPEN`, feed status is:

```text
LIVE  -> latest tick is <= 60 seconds old
STALE -> latest tick is > 60 seconds old
```

The explicit timezone prevents incorrect market status when the host server uses UTC or another timezone.

---

## 10. Database

Primary tables:

```text
symbols
live_ticks
historical_bars
```

`symbols` contains the exchange mapping:

```text
exchange = NSE
exchange = BSE
```

`live_ticks` stores:

```text
LTP
LTQ
ATP
Volume
OHLC
Previous Close
OI
Turnover
Bid
Bid Quantity
Ask
Ask Quantity
```

See `docs/DATA_MODEL.md` for details.

---

## 11. FastAPI

Application entry point:

```text
app/main.py
```

Market API:

```text
app/api/market.py
```

Start:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health |
| GET | `/api/symbols` | Active symbols |
| GET | `/api/market/status` | Session/feed status |
| GET | `/api/market/live` | Latest NSE/BSE data |
| GET | `/api/market/{symbol}` | One-symbol live data |
| GET | `/api/market/{symbol}/history` | Historical EOD data |

Swagger:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

---

## 12. Frontend

Main application:

```text
frontend/src/App.jsx
```

The dashboard provides:

- Live market table
- NSE/BSE exchange labels
- ALL / NSE / BSE filtering
- Symbol search
- LTP / ATP
- Volume
- OHLC
- Previous close
- Bid / Ask
- Market status
- Historical data selection
- Automatic five-second refresh

Frontend setup:

```bash
cd frontend
npm install
npm run dev
```

The local frontend normally runs on:

```text
http://127.0.0.1:5173
```

Expected exchange filters:

```text
ALL (60)
NSE (50)
BSE (10)
```

---

## 13. Environment Configuration

Create `.env` from `.env.example`.

Required values include:

```text
TRUEDATA_USERNAME=<your_username>
TRUEDATA_PASSWORD=<your_password>
DATABASE_URL=<your_postgresql_url>
```

Never commit real credentials.

---

## 14. Database Initialization

Initialize tables:

```bash
python -m app.database.init_db
```

Seed symbols:

```bash
python -m app.database.seed
```

Expected current active-symbol count:

```text
60
```

---

## 15. Recommended Startup Order

```text
1. PostgreSQL
2. Initialize database
3. Seed symbols
4. Start TrueData collector
5. Start FastAPI
6. Start React frontend
```

---

## 16. Quick Validation

Health:

```bash
curl http://127.0.0.1:8000/health
```

Status:

```bash
curl -s http://127.0.0.1:8000/api/market/status
```

Live data:

```bash
curl -s http://127.0.0.1:8000/api/market/live
```

BSE count:

```bash
curl -s http://127.0.0.1:8000/api/market/live | python -c "import sys,json; d=json.load(sys.stdin); print('BSE records:',sum(1 for x in d['data'] if x['exchange']=='BSE'))"
```

Expected:

```text
BSE records: 10
```

---

## 17. Validation Summary

The following end-to-end behavior has been validated:

```text
50 NSE symbols
        |
        v
TrueData subscription
        |
        v
Live trades + Bid/Ask
        |
        v
PostgreSQL
        |
        v
FastAPI
        |
        v
React dashboard
```

and:

```text
10 BSE symbols
        |
        v
TrueData BSE subscription
        |
        v
Live trades + bidaskL2
        |
        v
PostgreSQL
        |
        v
FastAPI
        |
        v
React dashboard
```

Final validated dashboard scope:

```text
60 active symbols
50 NSE
10 BSE
```

---

## 18. Current Limitations

The current POC intentionally does not yet provide:

- Automatic WebSocket reconnect
- Exponential backoff
- Subscription recovery
- Production process supervision
- Production authentication/authorization
- Production-grade monitoring/alerting
- Production database backup/retention policy
- BSE historical EOD ingestion validation

These items are documented in `docs/PRODUCTION_READINESS.md`.

---

## 19. Documentation

Start with:

```text
docs/DOCUMENTATION_INDEX.md
```

Then review:

```text
docs/ARCHITECTURE.md
docs/API.md
docs/DATA_MODEL.md
docs/OPERATIONS.md
docs/TESTING.md
docs/SECURITY.md
docs/PRODUCTION_READINESS.md
```

---

## 20. Security

Never commit:

```text
TRUEDATA_USERNAME
TRUEDATA_PASSWORD
DATABASE_URL credentials
API tokens
Authorization headers
```

Use `.env` locally and `.env.example` as the safe template.

See `docs/SECURITY.md`.
