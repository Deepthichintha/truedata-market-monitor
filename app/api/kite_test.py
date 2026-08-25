"""HTTP API for the isolated Kite provider evaluation.

These routes are deliberately separate from /api/market and do not alter the
existing TrueData endpoints.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import desc

from app.database.connection import SessionLocal
from app.kite.auth import auth_status, exchange_request_token, login_url
from app.kite.collector import collector
from app.kite.config import KITE_ACCESS_TOKEN, KITE_FRONTEND_URL
from app.kite.instruments import download_instruments, map_test_universe, validate_test_universe
from app.kite.models import KiteTestTick

router = APIRouter(prefix="/api/kite-test", tags=["Kite Provider Evaluation"])


@router.get("/login")
def kite_login():
    try:
        return RedirectResponse(login_url())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/callback")
def kite_callback(request_token: str):
    try:
        session = exchange_request_token(request_token)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Kite authentication failed: {exc}")

    # Keep the token server-side; never return it to the browser.
    return RedirectResponse(KITE_FRONTEND_URL)


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
        path = download_instruments()
        rows = map_test_universe(path)
        validation = validate_test_universe(rows)
        return {"file": str(path), "validation": validation, "instruments": rows}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Kite instrument mapping failed: {exc}")


@router.get("/status")
def kite_status():
    return {
        "auth": kite_auth_status(),
        "collector": collector.status(),
    }


@router.post("/start")
def kite_start():
    try:
        result = collector.start()
        return {"status": "started", "collector": result}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/stop")
def kite_stop():
    collector.stop()
    return {"status": "stopped", "collector": collector.status()}


@router.get("/live")
def kite_live():
    db = SessionLocal()
    try:
        rows = (
            db.query(KiteTestTick)
            .order_by(desc(KiteTestTick.timestamp), desc(KiteTestTick.id))
            .all()
        )
        latest: dict[tuple[str, str], KiteTestTick] = {}
        for row in rows:
            latest.setdefault((row.exchange, row.symbol), row)

        data = [
            {
                "provider": "kite",
                "symbol": row.symbol,
                "exchange": row.exchange,
                "instrument_token": row.instrument_token,
                "timestamp": row.timestamp,
                "received_at": row.received_at,
                "ltp": row.ltp,
                "ltq": row.ltq,
                "atp": row.atp,
                "total_volume": row.total_volume,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "prev_close": row.prev_close,
                "oi": row.oi,
                "bid": row.bid,
                "bid_qty": row.bid_qty,
                "ask": row.ask,
                "ask_qty": row.ask_qty,
                "last_trade_time": row.last_trade_time,
                "exchange_timestamp": row.exchange_timestamp,
            }
            for row in sorted(latest.values(), key=lambda x: (x.exchange, x.symbol))
        ]
        return {"count": len(data), "data": data}
    finally:
        db.close()
