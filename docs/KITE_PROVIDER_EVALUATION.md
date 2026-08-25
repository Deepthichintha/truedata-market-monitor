# Kite Provider Evaluation

## Purpose

This is an isolated Kite Connect evaluation added to the `truedata-market-monitor` repository.

**TrueData is not being replaced, refactored, or modified by this evaluation.** The existing TrueData collector and `/api/market/*` API remain the reference implementation.

Kite has its own:

- OAuth login and access-token flow
- instrument download and NSE/BSE mapping
- WebSocket collector
- `kite_test_symbols` and `kite_test_ticks` tables
- `kite_test_historical_bars` table
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

The TrueData button opens the existing application. The Kite button opens the independent evaluation page.

## Kite authentication — important

Set these local environment variables in the **backend** `.env`:

```text
KITE_API_KEY=...
KITE_API_SECRET=...
KITE_ACCESS_TOKEN=<optional_existing_access_token>
KITE_REDIRECT_URL=http://127.0.0.1:8000/api/kite-test/callback
KITE_FRONTEND_URL=http://127.0.0.1:5173/?provider=kite&auth=success
```

Do not commit the API secret or access token.

### The redirect URL has two required locations

The value in `.env` is only the URL this application expects. It **does not override Kite's developer-console configuration**.

For the local test, the Kite API application used by the lead must have this exact Redirect URL registered in the Kite developer console:

```text
http://127.0.0.1:8000/api/kite-test/callback
```

These must match exactly:

```text
Kite developer console Redirect URL
            =
KITE_REDIRECT_URL in backend .env
            =
http://127.0.0.1:8000/api/kite-test/callback
```

If the Kite application is still registered with:

```text
https://tier1app2026-production.up.railway.app/api/kite/callback
```

Kite will continue redirecting there after login, regardless of the local `.env` value. The local FastAPI application cannot override a redirect URL registered against the Kite API key.

For a deployed test, the registered URL must instead be the deployed backend callback URL, and the backend deployment must contain the `/api/kite-test/callback` route.

### Official login flow

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
Kite developer-console registered Redirect URL
      |
      v
request_token
      |
      v
server-side request-token exchange
      |
      v
access_token
      |
      v
Kite Test Page
```

Kite also supports an optional `redirect_params` value on its login URL. This repository uses `provider=kite` only as informational context; it does not change the developer-console registered Redirect URL.

Kite access tokens are session/day credentials. A fresh manual login should be performed as required by Kite's authentication rules rather than attempting to automate the login itself.

## Authentication diagnostics

After restarting FastAPI, check:

```bash
curl http://127.0.0.1:8000/api/kite-test/auth/status
curl http://127.0.0.1:8000/api/kite-test/auth/config
```

`/auth/config` returns only non-secret setup diagnostics, including the callback URL the running backend expects. It never returns the API secret or access token.

A direct callback test without a token should return HTTP 400 with a clear message. That is expected:

```bash
curl -i http://127.0.0.1:8000/api/kite-test/callback
```

Do not manually call the callback during a real login. Kite must supply the one-time `request_token`.

## Instrument mapping

The provider comparison uses the existing evaluation universe:

```text
50 NSE symbols
10 BSE symbols
60 instruments total
```

Both exchanges are mapped independently:

```text
NSE:<symbol> -> Kite instrument_token
BSE:<symbol> -> Kite instrument_token
```

The Kite instrument dump is downloaded to `data/kite_instruments.csv` and is not read from the TrueData live feed.

The mapping endpoint creates only the Kite evaluation tables, validates the complete universe, and persists the mapped rows to `kite_test_symbols`.

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

1. Confirm the Kite developer-console Redirect URL matches the backend `.env`.
2. Click **Login with Kite**.
3. Complete the manual Kite login.
4. Confirm `/api/kite-test/auth/status` reports `authenticated: true`.
5. Click **Refresh Kite Mapping**.
6. Confirm `60/60` instruments are mapped: `50 NSE + 10 BSE`.
7. Click **Start Kite Collector**.
8. Wait for live NSE and BSE ticks during market hours.
9. Verify the table and database records.

## Backend endpoints

```text
GET  /api/kite-test/login
GET  /api/kite-test/callback?request_token=...
GET  /api/kite-test/auth/status
GET  /api/kite-test/auth/config
POST /api/kite-test/mapping
GET  /api/kite-test/status
POST /api/kite-test/start
POST /api/kite-test/stop
GET  /api/kite-test/live
POST /api/kite-test/historical
GET  /api/kite-test/historical
```

A compatibility callback also exists for older Kite application registrations:

```text
GET /api/kite/callback?request_token=...
```

It performs the same server-side token exchange but should not be used as the primary local evaluation callback.

## Manual backend validation

Health:

```bash
curl http://127.0.0.1:8000/health
```

Kite authentication status:

```bash
curl http://127.0.0.1:8000/api/kite-test/auth/status
```

Expected before login:

```json
{"configured":true,"authenticated":false,"user_id":null}
```

Kite mapping:

```bash
curl -X POST http://127.0.0.1:8000/api/kite-test/mapping
```

Expected validation:

```text
expected: 60
found: 60
NSE: 50
BSE: 10
complete: true
```

Kite collector status:

```bash
curl http://127.0.0.1:8000/api/kite-test/status
```

Start collection only after authentication succeeds:

```bash
curl -X POST http://127.0.0.1:8000/api/kite-test/start
```

Live data:

```bash
curl http://127.0.0.1:8000/api/kite-test/live
```

An empty result before the first live tick is valid:

```json
{"count":0,"data":[]}
```

Once the feed is live, verify both exchanges and that `ticks_received` is increasing.

Stop collection:

```bash
curl -X POST http://127.0.0.1:8000/api/kite-test/stop
```

## Storage isolation

Kite uses:

```text
kite_test_symbols
kite_test_ticks
kite_test_historical_bars
```

TrueData continues using its existing:

```text
symbols
live_ticks
historical_bars
```

The Kite collector does not import `truedata_collector`, does not use TrueData IDs, and does not write to `live_ticks`.

The API initializes only the three Kite-owned SQLAlchemy tables. It does not call `Base.metadata.create_all()` for the entire application schema.

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
- last-trade timestamp
- exchange timestamp
- local receive timestamp

The initial evaluation universe is only 60 instruments, so it remains comfortably within the Kite WebSocket connection limit.

## Historical data

Historical evaluation uses only Kite instrument tokens and Kite's historical API. Example:

```bash
curl -X POST "http://127.0.0.1:8000/api/kite-test/historical?from_date=2026-08-24&to_date=2026-08-24&interval=day&include_oi=true"
```

Read stored candles:

```bash
curl "http://127.0.0.1:8000/api/kite-test/historical?exchange=NSE&symbol=RELIANCE&interval=day"
```

## Comparison rule

Do not decide the winner based only on how many WebSocket messages arrive.

For each provider, compare the same security and exchange using:

- LTP
- last-traded timestamp
- exchange timestamp
- bid/ask
- bid/ask quantity
- volume
- market depth where available
- missing/stale instruments
- receive latency
- reconnect behavior
- historical candle availability and consistency

An independent reference should be used when the two providers disagree on a value. A difference in message count does not automatically mean a difference in accuracy.

## Acceptance criteria

- [ ] TrueData collector behavior unchanged.
- [ ] Kite developer-console Redirect URL matches the running backend callback.
- [ ] Kite login redirects correctly.
- [ ] Kite request token is exchanged server-side.
- [ ] Mapping reports 60/60 instruments.
- [ ] Mapping reports 50 NSE + 10 BSE.
- [ ] `kite_test_symbols` contains the mapped universe.
- [ ] Kite collector connects independently.
- [ ] Collector reports 60 subscribed instruments.
- [ ] One Kite WebSocket receives both NSE and BSE data.
- [ ] Kite records are written only to Kite test tables.
- [ ] `kite_test_ticks` receives live records during market hours.
- [ ] Provider timestamps are preserved separately from local receive time.
- [ ] Historical candles can be fetched and read back.
- [ ] Kite frontend shows the same core market fields used for TrueData comparison.
- [ ] Raw test data is preserved before selecting a provider.
- [ ] Existing TrueData APIs continue to work unchanged.

## Troubleshooting

### Browser redirects to the old Railway `Not Found` page

This means the Kite API application's registered Redirect URL still points to the old Railway URL. Changing `KITE_REDIRECT_URL` in the local `.env` cannot override the developer-console setting.

For local testing, change the Kite application Redirect URL to:

```text
http://127.0.0.1:8000/api/kite-test/callback
```

Restart FastAPI and start a fresh login flow. The one-time `request_token` should then arrive at the local callback.

### `/api/kite-test/callback` returns 400

The callback requires Kite's `request_token`. Do not call the callback URL manually without the token. Start authentication from `/api/kite-test/login`.

### Authentication says `configured=false`

Check `KITE_API_KEY` and `KITE_API_SECRET` in `.env`, then restart FastAPI.

### Authentication says `configured=true` but `authenticated=false`

The API key/secret are present, but there is no current access token. Complete the browser login. If the browser redirects to another host, fix the Kite developer-console Redirect URL first.

### Collector says `Kite is not authenticated`

Complete the browser login and verify `/api/kite-test/auth/status` reports `authenticated: true` before starting the collector.

### Mapping is incomplete

Run the mapping endpoint again and inspect the returned `missing` list. The evaluation is considered valid only when all 60 instruments are present.

## Official references

- Kite Connect v3 user/login flow: https://kite.trade/docs/connect/v3/user/
- Kite WebSocket streaming: https://kite.trade/docs/connect/v3/websocket/
- Kite market data and instruments: https://kite.trade/docs/connect/v3/market-data-and-instruments/
- Kite historical candle data: https://kite.trade/docs/connect/v3/historical/
- Kite Python client: https://kite.trade/docs/pykiteconnect/v4/
