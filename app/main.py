from fastapi import FastAPI

from app.config.settings import settings
from app.api.market import router as market_router


app = FastAPI(
    title=settings.app_name,
    description="Real-time stock monitoring POC using TrueData APIs",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/api/symbols")
async def get_symbols():
    from app.config.symbols import SYMBOLS

    return {
        "count": len(SYMBOLS),
        "symbols": SYMBOLS,
    }


app.include_router(market_router)
