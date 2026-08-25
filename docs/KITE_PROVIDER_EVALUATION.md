# Kite Provider Evaluation

## Purpose

This is an isolated Kite Connect evaluation added to the `truedata-market-monitor` repository.

**TrueData is not being replaced, refactored, or modified by this evaluation.** The existing TrueData collector and `/api/market/*` API remain the reference implementation.

Kite has its own:

- OAuth login and access-token flow
- instrument download and NSE/BSE mapping
- WebSocket collector
- `kite_test_symbols` and `kite_test_ticks` tables
- `/api/kite-test/*` API
- frontend test page

The two providers do not exchange live data.

## Provider navigation

Open the frontend root:

```text
http://127.0.0.1:5173/
```

Select:

```text
TrueData -> /?provider=truedata
Kite     -> /?provider=kite
```

The TrueData button opens the existing application. The Kite button opens the new independent evaluation page.

## Kite authentication

Set these local environment variables:

```text
KITE_API_KEY=...
KITE_API_SECRET=...
KITE_REDIRECT_URL=http://127.0.0.1:8000/api/kite-test/callback
KITE_FRONTEND_URL=http://127.0.0.1:5173/?provider=kite&auth=success
```

Do not commit the API secret or access token.

The Kite login flow is:

```text
Kite Test Page
      |
      v
GET /api/kite-test/login
      |
      v
Kite login page
      |
      v
registered callback + request_token
      |
      v
POST/session exchange on backend
      |
      v
server-side access token
      |
      v
Kite Test Page
```

Kite access tokens are session/day credentials. A fresh manual login should be performed as required by Kite's authentication rules rather than attempting to automate the login itself.

## Instrument mapping

The test universe is deliberately the same 10 symbols used for the provider comparison:

```text
AARTIIND
ADANIPORTS
AETHER
APOLLOHOSP
ASHIANA
ATUL
AUBANK
BAJAJ-AUTO
CARERATING
CCL
```

Both exchanges are mapped independently:

```text
NSE:<symbol> -> Kite instrument_token
BSE:<symbol> -> Kite instrument_token
```

The Kite instrument dump is downloaded to `data/kite_instruments.csv` and is not read from the TrueData mapping.

## Start the test

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173/
```

Choose **Kite**.

Then:

1. Click **Login with Kite**.
2. Complete the manual Kite login.
3. Return to the Kite test page.
4. Click **Refresh Kite Mapping**.
5. Confirm `20/20` instruments are mapped.
6. Click **Start Kite Collector**.
7. Wait for live NSE and BSE ticks during market hours.
8. Verify the table and database records.

## Backend endpoints

```text
GET  /api/kite-test/login
GET  /api/kite-test/callback?request_token=...
GET  /api/kite-test/auth/status
POST /api/kite-test/mapping
GET  /api/kite-test/status
POST /api/kite-test/start
POST /api/kite-test/stop
GET  /api/kite-test/live
```

## Storage isolation

Kite uses:

```text
kite_test_symbols
kite_test_ticks
```

TrueData continues using its existing:

```text
symbols
live_ticks
historical_bars
```

The Kite collector does not import `truedata_collector`, does not use TrueData IDs, and does not write to `live_ticks`.

## WebSocket mode

The Kite collector uses `FULL` mode so the evaluation includes:

- LTP
- last traded quantity
- average traded price
- volume
- OHLC
- open interest
- best bid/ask
- bid/ask quantities
- market depth supplied by Kite
- last-trade timestamp
- exchange timestamp
- local receive timestamp

Kite documents a maximum of 3,000 instruments per WebSocket connection. Our initial test deliberately uses only 20 instruments so that the provider comparison remains controlled.

## Comparison rule

Do not decide the winner based only on how many WebSocket messages arrive.

For each provider, compare the same security and exchange using:

- LTP
- last-traded timestamp
- exchange timestamp
- bid/ask
- bid/ask quantity
- volume
- market depth
- missing/stale instruments
- receive latency
- reconnect behavior

An independent reference should be used when the two providers disagree on a value. A difference in message count does not automatically mean a difference in accuracy.

## Acceptance criteria for this phase

- [ ] TrueData collector behavior unchanged.
- [ ] Kite login redirects correctly.
- [ ] Kite request token is exchanged server-side.
- [ ] 10 NSE + 10 BSE instruments map correctly.
- [ ] Kite collector connects independently.
- [ ] One Kite WebSocket receives both NSE and BSE data.
- [ ] Kite records are written only to Kite test tables.
- [ ] Kite frontend shows the same core market fields used for TrueData comparison.
- [ ] Raw test data is preserved before selecting a provider.

## Official references

- Kite WebSocket streaming: https://kite.trade/docs/connect/v3/websocket/
- Kite market data and instruments: https://kite.trade/docs/connect/v3/market-data-and-instruments/
- Kite Python client: https://kite.trade/docs/pykiteconnect/v4/
