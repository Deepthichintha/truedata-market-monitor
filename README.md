# TrueData Market Monitor

TrueData Market Monitor is a real-time NSE market monitoring application that receives live market data from TrueData, processes and stores the data in PostgreSQL, exposes REST APIs through FastAPI, and displays the market information through a React/Vite dashboard.

The current implementation is a local proof of concept designed to validate the complete market-data flow before production or cloud deployment.

---

## 1. Project Overview

The application provides:

- Real-time NSE market data ingestion
- TrueData WebSocket integration
- Subscription to configured market symbols
- Trade message parsing and validation
- PostgreSQL persistence
- Live market-data APIs
- Historical EOD market-data APIs
- Market/feed status detection
- React/Vite monitoring dashboard
- Automatic dashboard refresh
- Symbol search
- Historical data viewing
- Health monitoring

---

## 2. System Architecture

```text
                         +----------------------+
                         |       TrueData       |
                         |   WebSocket Feed     |
                         |    NSE Market Data   |
                         +----------+-----------+
                                    |
                                    |
                                    v
                         +----------------------+
                         |  TrueData Collector  |
                         |       Python         |
                         |                      |
                         | - Connect            |
                         | - Authenticate       |
                         | - Subscribe symbols  |
                         | - Receive ticks      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |    Trade Parser      |
                         |                      |
                         | Validate payload     |
                         | Normalize fields     |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      PostgreSQL      |
                         |                      |
                         |  symbols             |
                         |  live_ticks          |
                         |  historical_bars     |
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
                         +----------+-----------+
                                    |
                                    v
                              Web Browser
```

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Frontend Build Tool | Vite |
| Backend | Python |
| API Framework | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Market Data Provider | TrueData |
| Market Data Protocol | WebSocket |
| HTTP Client | HTTPX |
| Configuration | Pydantic Settings |
| Environment Configuration | `.env` |
| API Documentation | OpenAPI / Swagger |
| Package Management | pip / npm |

---

## 4. Repository Structure

```text
truedata-market-monitor/
|
+-- app/
|   |
|   +-- api/
|   |   +-- market.py
|   |
|   +-- config/
|   |   +-- settings.py
|   |   +-- symbols.py
|   |
|   +-- database/
|   |   +-- connection.py
|   |   +-- init_db.py
|   |   +-- models.py
|   |   +-- seed.py
|   |
|   +-- services/
|   |   +-- smarttheta.py
|   |   +-- truedata_collector.py
|   |   +-- truedata_parser.py
|   |
|   +-- main.py
|
+-- data/
|
+-- frontend/
|   +-- src/
|
+-- scripts/
|
+-- tests/
|
+-- docs/
|
+-- .env.example
+-- .gitignore
+-- requirements.txt
+-- README.md
```

---

## 5. TrueData Integration

The application receives real-time market data from the TrueData WebSocket service.

WebSocket endpoint:

```text
wss://push.truedata.in:8086
```

The collector performs the following operations:

```text
Read credentials
       |
       v
Load active symbols
       |
       v
Connect to TrueData
       |
       v
Authenticate
       |
       v
Subscribe to symbols
       |
       v
Receive market messages
       |
       v
Parse trade messages
       |
       v
Store data in PostgreSQL
```

The configured application has been validated with the required NSE symbol set.

---

## 6. TrueData Collector

File:

```text
app/services/truedata_collector.py
```

The collector is responsible for:

- Reading TrueData credentials
- Loading active symbols from PostgreSQL
- Establishing the WebSocket connection
- Subscribing to market symbols
- Receiving heartbeat messages
- Handling subscription confirmations
- Receiving trade messages
- Sending trade data to the parser
- Saving parsed ticks to PostgreSQL
- Handling errors
- Closing the WebSocket connection cleanly

The collector is designed as a separate long-running process.

Start it with:

```bash
python -m app.services.truedata_collector
```

---

## 7. TrueData Parser

File:

```text
app/services/truedata_parser.py
```

The parser converts the TrueData trade message into normalized application data.

The parser validates the expected trade message structure and converts fields such as:

```text
Symbol ID
Timestamp
LTP
LTQ
ATP
Total Volume
Open
High
Low
Previous Close
Open Interest
Previous Open Interest
Turnover
Bid
Bid Quantity
Ask
Ask Quantity
```

The parser also preserves the original values for traceability.

---

## 8. Database

The application uses PostgreSQL for persistence.

Primary tables:

```text
symbols
live_ticks
historical_bars
```

The database connection is configured through:

```text
DATABASE_URL
```

Example:

```text
postgresql://postgres:<password>@localhost:5432/truedata_market_monitor
```

---

## 9. Database Tables

### symbols

Stores configured market symbols.

Important fields:

```text
id
symbol
truedata_symbol_id
exchange
is_active
created_at
```

### live_ticks

Stores real-time market tick information.

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

### historical_bars

Stores historical EOD market data.

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

The current application uses:

```text
timeframe = 1D
```

---

## 10. FastAPI Backend

The FastAPI backend is the main REST API layer.

Application entry point:

```text
app/main.py
```

Market API:

```text
app/api/market.py
```

Local backend URL:

```text
http://127.0.0.1:8000
```

Start the backend:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 11. API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

---

## 12. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Application health |
| GET | `/api/symbols` | Return configured symbols |
| GET | `/api/market/status` | Market/feed status |
| GET | `/api/market/live` | Latest data for active symbols |
| GET | `/api/market/{symbol}` | Latest data for one symbol |
| GET | `/api/market/{symbol}/history` | Historical EOD data |

---

## 13. Health API

Endpoint:

```text
GET /health
```

Example:

```bash
curl http://127.0.0.1:8000/health
```

Example response:

```json
{
  "status": "healthy",
  "service": "TrueData Market Monitor",
  "environment": "development"
}
```

---

## 14. Symbols API

Endpoint:

```text
GET /api/symbols
```

Example:

```bash
curl http://127.0.0.1:8000/api/symbols
```

Example response:

```json
{
  "count": 50,
  "symbols": [
    "RELIANCE",
    "TCS"
  ]
}
```

The actual response contains the configured symbols.

---

## 15. Market Status API

Endpoint:

```text
GET /api/market/status
```

Example:

```bash
curl http://127.0.0.1:8000/api/market/status
```

The API determines whether the market/feed is:

```text
LIVE
STALE
CLOSED
```

Current configured NSE market window:

```text
Market Open  : 09:15
Market Close : 15:30
```

Stale-feed threshold:

```text
60 seconds
```

### LIVE

The NSE market is open and a recent tick has been received.

### STALE

The market is open, but no recent tick has been received within the configured stale threshold.

### CLOSED

The application is outside the configured NSE market hours.

---

## 16. Live Market API

Endpoint:

```text
GET /api/market/live
```

Example:

```bash
curl http://127.0.0.1:8000/api/market/live
```

The API returns the latest available tick for each active symbol.

Example:

```json
{
  "count": 1,
  "data": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "truedata_symbol_id": "123",
      "timestamp": "2026-08-19T10:30:00",
      "ltp": 1000.0,
      "ltq": 10,
      "atp": 995.0,
      "total_volume": 100000,
      "open": 990.0,
      "high": 1010.0,
      "low": 985.0,
      "prev_close": 992.0,
      "oi": 0,
      "prev_oi": 0,
      "turnover": 100000000,
      "bid": 999.5,
      "bid_qty": 100,
      "ask": 1000.5,
      "ask_qty": 120
    }
  ]
}
```

---

## 17. Symbol Market API

Endpoint:

```text
GET /api/market/{symbol}
```

Example:

```bash
curl http://127.0.0.1:8000/api/market/RELIANCE
```

The endpoint returns the most recent tick for the requested symbol.

Possible `404` conditions:

```text
Symbol not found
TrueData symbol mapping not found
No market data available
```

---

## 18. Historical Market API

Endpoint:

```text
GET /api/market/{symbol}/history
```

Example:

```bash
curl "http://127.0.0.1:8000/api/market/RELIANCE/history?limit=200"
```

Supported parameter:

```text
limit
```

Allowed range:

```text
1 - 500
```

Current timeframe:

```text
1D
```

The newest historical records are returned first.

---

## 19. React/Vite Frontend

The frontend provides the monitoring dashboard.

Main application:

```text
frontend/src/App.jsx
```

The dashboard provides:

- Live market table
- Symbol search
- LTP
- ATP
- Volume
- Open
- High
- Low
- Previous close
- Bid
- Ask
- Timestamp
- Market status
- Historical market data

---

## 20. Dashboard Refresh

The frontend automatically refreshes the market dashboard every:

```text
5 seconds
```

The frontend calls:

```text
/api/market/live
/api/market/status
```

during the refresh cycle.

Historical data is loaded when the user selects a symbol.

---

## 21. Frontend Setup

Go to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

The frontend normally runs on:

```text
http://127.0.0.1:5173
```

---

## 22. Environment Configuration

Create `.env` from `.env.example`.

Example:

```text
APP_NAME=TrueData Market Monitor
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000

TRUEDATA_USERNAME=<your_truedata_username>
TRUEDATA_PASSWORD=<your_truedata_password>

DATABASE_URL=postgresql://postgres:<password>@localhost:5432/truedata_market_monitor

SMARTTHETA_BASE_URL=http://127.0.0.1:8000
```

Never commit the real `.env` file.

---

## 23. Database Initialization

Initialize database tables:

```bash
python -m app.database.init_db
```

Seed configured symbols:

```bash
python -m app.database.seed
```

---

## 24. Recommended Startup Order

Start services in this order:

```text
1. PostgreSQL
       |
       v
2. Initialize database
       |
       v
3. Seed symbols
       |
       v
4. Start TrueData collector
       |
       v
5. Start FastAPI
       |
       v
6. Start React frontend
```

---

## 25. Validation Commands

### Backend health

```bash
curl http://127.0.0.1:8000/health
```

### Symbols

```bash
curl http://127.0.0.1:8000/api/symbols
```

### Market status

```bash
curl http://127.0.0.1:8000/api/market/status
```

### Live data

```bash
curl http://127.0.0.1:8000/api/market/live
```

### Individual symbol

```bash
curl http://127.0.0.1:8000/api/market/RELIANCE
```

### Historical data

```bash
curl "http://127.0.0.1:8000/api/market/RELIANCE/history?limit=200"
```

---

## 26. End-to-End Data Flow

```text
TrueData
   |
   | WebSocket
   v
TrueData Collector
   |
   | Raw trade message
   v
Trade Parser
   |
   | Normalized data
   v
PostgreSQL
   |
   | SQL queries
   v
FastAPI
   |
   | JSON
   v
React Dashboard
   |
   v
User
```

---

## 27. Error Handling

The application handles several failure conditions.

### TrueData

- Missing credentials
- WebSocket connection failure
- Invalid JSON
- Invalid trade payload
- Parsing failure

### Database

- Missing `DATABASE_URL`
- Database connection failure
- Database insert failure

### API

- Invalid symbol
- Missing symbol mapping
- Missing market data

### Frontend

- Backend unavailable
- Failed API request
- Empty market data
- Historical data unavailable

---

## 28. Security

Sensitive values include:

```text
TRUEDATA_USERNAME
TRUEDATA_PASSWORD
DATABASE_URL
```

These must never be committed to GitHub.

Use:

```text
.env
```

for local configuration and:

```text
.env.example
```

for documentation.

Production should use a proper secret-management system.

---

## 29. Production Target Architecture

The current application is primarily a local proof of concept.

A production deployment should separate the components:

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

---

## 30. Production Recommendations

Before production deployment, implement:

- WebSocket reconnect
- Exponential backoff
- Collector health monitoring
- Process supervision
- Structured logging
- Centralized logging
- API authentication
- API authorization
- HTTPS
- Restricted CORS
- Rate limiting
- Database migrations
- Database backups
- Tick retention
- Database partitioning evaluation
- Monitoring and alerting
- Secret management
- Automated CI/CD
- Automated tests

---

## 31. Scalability Considerations

The collector stores real-time ticks in PostgreSQL.

At higher market-data volumes, evaluate:

```text
Tick ingestion rate
Database write throughput
Storage growth
Index size
Query latency
Connection pool size
Retention requirements
```

Potential future architecture:

```text
TrueData
    |
    v
Collector
    |
    v
Message Queue / Stream
    |
    +----------------+
    |                |
    v                v
Real-time        PostgreSQL
Processing       / Historical
    |
    v
FastAPI
```

---

## 32. Monitoring Recommendations

Production monitoring should track:

```text
API availability
API response time
API error rate
WebSocket connection status
Collector process status
Tick ingestion rate
Database health
Database storage
Stale market feed
Application CPU
Application memory
```

---

## 33. Project Status

Current project flow:

```text
TrueData
    |
    v
WebSocket Collector
    |
    v
Trade Parser
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

The current implementation provides the core proof-of-concept market-data pipeline.

Production hardening should be completed before exposing the application publicly.

---

## 34. Documentation

Detailed documentation is available in:

```text
docs/
```

Recommended documents:

```text
docs/ARCHITECTURE.md
docs/API.md
docs/DATA_MODEL.md
docs/OPERATIONS.md
docs/SECURITY.md
docs/TESTING.md
docs/PRODUCTION_READINESS.md
docs/ARCHITECTURE_DIAGRAM.mmd
docs/DATA_FLOW_DIAGRAM.mmd
docs/DOCUMENTATION_INDEX.md
```

---

## License

Internal project / proof of concept.
