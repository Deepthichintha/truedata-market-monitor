# TrueData Market Monitor - Testing Strategy

## 1. Testing Objectives

Testing should verify application startup, database connectivity, API behavior, TrueData parsing, collector behavior, persistence, market status, frontend behavior, error handling, and performance.

## 2. Unit Testing

Recommended unit coverage:

- TrueData parser
- Numeric conversion
- Timestamp parsing
- Market-hours logic
- Stale-feed logic
- Symbol processing

## 3. API Testing

Validate:

```text
GET /health
GET /api/symbols
GET /api/market/status
GET /api/market/live
GET /api/market/{symbol}
GET /api/market/{symbol}/history
```

## 4. Integration Testing

Validate:

```text
Application -> PostgreSQL
```

and:

```text
TrueData -> Collector -> Parser -> PostgreSQL
```

## 5. End-to-End Testing

The complete acceptance flow is:

```text
TrueData
   |
   v
Collector
   |
   v
Parser
   |
   v
PostgreSQL
   |
   v
FastAPI
   |
   v
React Dashboard
```

A successful end-to-end test should show a recently received tick through `/api/market/live` and in the dashboard.

## 6. Negative Testing

Test the following scenarios:

- Invalid symbol
- Missing symbol mapping
- No live data
- Invalid TrueData payload
- Malformed JSON
- WebSocket disconnect
- Database unavailable
- Backend unavailable
- Frontend timeout

## 7. Performance Testing

Measure:

- API response time
- Database query latency
- Collector ingestion rate
- PostgreSQL write throughput
- WebSocket stability
- Frontend refresh load

Performance tests should use realistic symbol counts and sustained market-data volumes.

## 8. Security Testing

Validate:

- No secrets in repository
- No credentials in frontend
- CORS restrictions
- Authentication and authorization when enabled
- TLS in production
- Database access controls
