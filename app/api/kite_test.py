"""HTTP API for the isolated Kite provider evaluation."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import desc

from app.database.connection import Base, SessionLocal, engine
from app.kite.auth import auth_status, exchange_request_token, login_url
from app.kite.collector import collector
from app.kite.config import KITE_ACCESS_TOKEN, KITE_FRONTEND_URL
from app.kite.historical import SUPPORTED_INTERVALS, fetch_historical
from app.kite.historical_models import KiteTestHistoricalBar
from app.kite.instruments import download_instruments, map_test_universe, validate_test_universe
from app.kite.models import KiteTestSymbol, KiteTestTick

router = APIRouter(prefix="/api/kite-test", tags=["Kite Provider Evaluation"])


# Keep Kite evaluation storage isolated from the existing TrueData tables.
# We create only the tables owned by the Kite evaluation models and never run
# Base.metadata.create_all() for the whole application schema here.
def ensure_kite_tables() -> None:
    Base.metadata.create_all(
        bind=engine,
        tables=[
            KiteTestSymbol.__table__,
            KiteTestTick.__table__,
            KiteTestHistoricalBar.__table__,
        ],
    )


@router.get("/login")
def kite_login():
    try:
        return RedirectResponse(login_url())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/callback")
def kite_callback(
    request_token: str | None = Query(None),
    status: str | None = Query(None),
    action: str | None = Query(None),
    type: str | None = Query(None),
):
    """Handle Kite's registered redirect callback.

    Kite appends ``status=success``, ``action=login`` and the short-lived
    ``request_token`` to the registered redirect URL.  The request token is
    exchanged server-side and is never returned to the browser.
    """
    if status and status != "success":
        raise HTTPException(status_code=401, detail=f"Kite login failed: {status}")
    if not request_token:
        raise HTTPException(status_code=400, detail="Kite request_token is missing")

    try:
        exchange_request_token(request_token)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Kite authentication failed: {exc}")

    return RedirectResponse(KITE_FRONTEND_URL)


# Compatibility callback for Kite apps that still have the legacy
# /api/kite/callback path registered. It uses the exact same server-side
# token exchange and does not touch the existing TrueData routes.
legacy_router = APIRouter(prefix="/api/kite", tags=["Kite Provider Evaluation"])


@legacy_router.get("/callback")
def kite_legacy_callback(
    request_token: str | None = Query(None),
    status: str | None = Query(None),
    action: str | None = Query(None),
    type: str | None = Query(None),
):
    return kite_callback(
        request_token=request_token,
        status=status,
        action=action,
        type=type,
    )


@router.get("/auth/status")
def kite_auth_status():
    status = auth_status()
    if KITE_ACCESS_TOKEN and not status["authenticated"]:
        status["authenticated"] = True
        status["source"] = "KITE_ACCESS_TOKEN"
    return status


@router.post("/mapping")
def kite_mapping():
    try:
        ensure_kite_tables()
        path = download_instruments()
        rows = map_test_universe(path)
        validation = validate_test_universe(rows)
        return {"file": str(path), "validation": validation, "instruments": rows}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Kite instrument mapping failed: {exc}")


@router.get("/status")
def kite_status():
    return {"auth": kite_auth_status(), "collector": collector.status()}


@router.post("/start")
def kite_start():
    try:
        ensure_kite_tables()
        return {"status": "started", "collector": collector.start()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/stop")
def kite_stop():
    collector.stop()
    return {"status": "stopped", "collector": collector.status()}


@router.get("/live")
def kite_live():
    ensure_kite_tables()
    db = SessionLocal()
    try:
        rows = db.query(KiteTestTick).order_by(desc(KiteTestTick.timestamp), desc(KiteTestTick.id)).all()
        latest: dict[tuple[str, str], KiteTestTick] = {}
        for row in rows:
            latest.setdefault((row.exchange, row.symbol), row)
        data = [
            {
                "provider": "kite", "symbol": row.symbol, "exchange": row.exchange,
                "instrument_token": row.instrument_token, "timestamp": row.timestamp,
                "received_at": row.received_at, "ltp": row.ltp, "ltq": row.ltq,
                "atp": row.atp, "total_volume": row.total_volume, "open": row.open,
                "high": row.high, "low": row.low, "prev_close": row.prev_close,
                "oi": row.oi, "bid": row.bid, "bid_qty": row.bid_qty,
                "ask": row.ask, "ask_qty": row.ask_qty,
                "last_trade_time": row.last_trade_time,
                "exchange_timestamp": row.exchange_timestamp,
            }
            for row in sorted(latest.values(), key=lambda x: (x.exchange, x.symbol))
        ]
        return {"count": len(data), "data": data}
    finally:
        db.close()


@router.post("/historical")
def kite_historical(
    from_date: date = Query(..., description="Start date, YYYY-MM-DD"),
    to_date: date = Query(..., description="End date, YYYY-MM-DD"),
    interval: str = Query("day", description="Kite candle interval"),
    include_oi: bool = Query(True),
):
    if interval not in SUPPORTED_INTERVALS:
        raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")
    try:
        return fetch_historical(from_date, to_date, interval=interval, include_oi=include_oi)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Kite historical request failed: {exc}")


@router.get("/historical")
def kite_historical_read(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    interval: str | None = Query(None),
    exchange: str | None = Query(None),
    symbol: str | None = Query(None),
):
    ensure_kite_tables()
    db = SessionLocal()
    try:
        query = db.query(KiteTestHistoricalBar)
        if from_date:
            query = query.filter(KiteTestHistoricalBar.candle_timestamp >= from_date)
        if to_date:
            query = query.filter(KiteTestHistoricalBar.candle_timestamp < to_date.fromordinal(to_date.toordinal() + 1))
        if interval:
            query = query.filter(KiteTestHistoricalBar.interval == interval)
        if exchange:
            query = query.filter(KiteTestHistoricalBar.exchange == exchange.upper())
        if symbol:
            query = query.filter(KiteTestHistoricalBar.symbol == symbol.upper())

        rows = query.order_by(KiteTestHistoricalBar.candle_timestamp, KiteTestHistoricalBar.exchange, KiteTestHistoricalBar.symbol).all()
        return {
            "count": len(rows),
            "data": [
                {
                    "provider": "kite", "symbol": row.symbol, "exchange": row.exchange,
                    "instrument_token": row.instrument_token,
                    "timestamp": row.candle_timestamp, "interval": row.interval,
                    "open": row.open, "high": row.high, "low": row.low,
                    "close": row.close, "volume": row.volume, "oi": row.oi,
                }
                for row in rows
            ],
        }
    finally:
        db.close()
