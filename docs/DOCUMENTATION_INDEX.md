# TrueData Market Monitor - Documentation Index

## Documentation Set

| Document | Purpose |
|---|---|
| `README.md` | Project overview, setup, architecture, APIs, operations, and production direction |
| `docs/ARCHITECTURE.md` | System architecture, components, runtime flow, and production target |
| `docs/API.md` | REST API reference and examples |
| `docs/DATA_MODEL.md` | PostgreSQL tables and data flow |
| `docs/OPERATIONS.md` | Setup, startup, validation, and troubleshooting |
| `docs/SECURITY.md` | Secrets, database, API, frontend, and logging security |
| `docs/TESTING.md` | Unit, API, integration, end-to-end, performance, and security testing |
| `docs/PRODUCTION_READINESS.md` | Production hardening checklist |
| `docs/ARCHITECTURE_DIAGRAM.mmd` | Standalone Mermaid architecture diagram source |
| `docs/DATA_FLOW_DIAGRAM.mmd` | Standalone Mermaid runtime data-flow diagram source |

## Current Logical Flow

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

## Local Services

Backend:

```text
http://127.0.0.1:8000
```

Frontend:

```text
http://127.0.0.1:5173
```

TrueData WebSocket:

```text
wss://push.truedata.in:8086
```

## Primary Database Tables

```text
symbols
live_ticks
historical_bars
```
