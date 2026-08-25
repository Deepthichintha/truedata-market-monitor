from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.api.market import router as market_router
from app.api.kite_test import router as kite_test_router, legacy_router as kite_legacy_router


app = FastAPI(
    title=settings.app_name,
    description="Real-time stock monitoring POC with isolated TrueData and Kite provider evaluation",
    version="0.1.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


# ---------------------------------------------------------
# Symbols
# ---------------------------------------------------------

@app.get("/api/symbols")
async def get_symbols():
    from app.config.symbols import SYMBOLS

    return {
        "count": len(SYMBOLS),
        "symbols": SYMBOLS,
    }


# ---------------------------------------------------------
# Market API
# ---------------------------------------------------------

app.include_router(market_router)


# ---------------------------------------------------------
# Kite provider evaluation API
# ---------------------------------------------------------

# This router is intentionally separate from /api/market. Existing TrueData
# routes and collector are not modified by the Kite evaluation path.
app.include_router(kite_test_router)

# Compatibility callback for the Kite app's currently registered production
# /api/kite/callback URL. This only handles the Kite request_token exchange and
# does not proxy market data or alter the existing TrueData implementation.
app.include_router(kite_legacy_router)
