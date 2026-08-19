from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.api.market import router as market_router


app = FastAPI(
    title=settings.app_name,
    description="Real-time stock monitoring POC using TrueData APIs",
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
