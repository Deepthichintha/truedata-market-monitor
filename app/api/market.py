from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc

from app.database.connection import SessionLocal
from app.database.models import HistoricalBar, LiveTick, Symbol


router = APIRouter(
    prefix="/api/market",
    tags=["Market"],
)


# NSE equity market session:
# 08:45-09:15 -> PRE_MARKET
# 09:15-15:30 -> OPEN
# Outside     -> CLOSED
IST = ZoneInfo("Asia/Kolkata")
PRE_MARKET_START = time(8, 45)
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

# A feed is considered stale if no new tick arrives within this period.
STALE_THRESHOLD_SECONDS = 60


def get_india_time() -> datetime:
    """Return the current time in Asia/Kolkata."""
    return datetime.now(IST)


def get_market_session() -> str:
    """
    Return the current NSE market session.

    PRE_MARKET: 08:45-09:15
    OPEN:       09:15-15:30
    CLOSED:     Outside those hours or weekends
    """
    now = get_india_time()

    if now.weekday() >= 5:
        return "CLOSED"

    current_time = now.time()

    if PRE_MARKET_START <= current_time < MARKET_OPEN:
        return "PRE_MARKET"

    if MARKET_OPEN <= current_time <= MARKET_CLOSE:
        return "OPEN"

    return "CLOSED"


def is_market_open() -> bool:
    """Return True only during regular NSE market hours."""
    return get_market_session() == "OPEN"


def tick_to_dict(
    tick: LiveTick,
    symbol: Symbol | None = None,
) -> dict:
    return {
        "symbol": symbol.symbol if symbol else None,
        "exchange": symbol.exchange if symbol else None,
        "truedata_symbol_id": tick.symbol_id,
        "timestamp": tick.timestamp,
        "ltp": tick.ltp,
        "ltq": tick.ltq,
        "atp": tick.atp,
        "total_volume": tick.total_volume,
        "open": tick.open,
        "high": tick.high,
        "low": tick.low,
        "prev_close": tick.prev_close,
        "oi": tick.oi,
        "prev_oi": tick.prev_oi,
        "turnover": tick.turnover,
        "bid": tick.bid,
        "bid_qty": tick.bid_qty,
        "ask": tick.ask,
        "ask_qty": tick.ask_qty,
    }


@router.get("/status")
def get_market_status():
    """
    Return the current NSE market/feed status.

    PRE_MARKET -> pre-market session
    OPEN + recent tick -> LIVE
    OPEN + old tick -> STALE
    CLOSED -> market closed
    """
    db = SessionLocal()

    try:
        latest_tick = (
            db.query(LiveTick)
            .order_by(
                desc(LiveTick.timestamp),
                desc(LiveTick.id),
            )
            .first()
        )

        now = get_india_time()

        latest_timestamp = None
        age_seconds = None

        if latest_tick:
            latest_timestamp = latest_tick.timestamp
            now_naive = now.replace(tzinfo=None)
            age_seconds = max(
                0,
                (now_naive - latest_tick.timestamp).total_seconds(),
            )

        market_session = get_market_session()

        if market_session == "PRE_MARKET":
            status = "PRE_MARKET"
        elif market_session == "CLOSED":
            status = "CLOSED"
        elif not latest_tick:
            status = "STALE"
        elif age_seconds <= STALE_THRESHOLD_SECONDS:
            status = "LIVE"
        else:
            status = "STALE"

        symbol_count = (
            db.query(Symbol)
            .filter(
                Symbol.is_active.is_(True),
                Symbol.truedata_symbol_id.isnot(None),
            )
            .count()
        )

        return {
            "status": status,
            "market_open": market_session == "OPEN",
            "market_session": market_session,
            "market": "NSE",
            "pre_market_start_time": "08:45",
            "market_open_time": "09:15",
            "market_close_time": "15:30",
            "latest_tick": latest_timestamp,
            "age_seconds": age_seconds,
            "stale_threshold_seconds": STALE_THRESHOLD_SECONDS,
            "active_symbols": symbol_count,
            "server_time": now,
            "timezone": "Asia/Kolkata",
        }

    finally:
        db.close()


@router.get("/live")
def get_live_market_data():
    db = SessionLocal()

    try:
        symbols = (
            db.query(Symbol)
            .filter(
                Symbol.is_active.is_(True),
                Symbol.truedata_symbol_id.isnot(None),
            )
            .order_by(Symbol.id)
            .all()
        )

        data = []

        for symbol in symbols:
            tick = (
                db.query(LiveTick)
                .filter(
                    LiveTick.symbol_id == symbol.truedata_symbol_id
                )
                .order_by(
                    desc(LiveTick.timestamp),
                    desc(LiveTick.id),
                )
                .first()
            )

            if tick:
                data.append(
                    tick_to_dict(
                        tick,
                        symbol,
                    )
                )

        return {
            "count": len(data),
            "data": data,
        }

    finally:
        db.close()


@router.get("/{symbol}")
def get_market_data(symbol: str):
    db = SessionLocal()

    try:
        db_symbol = (
            db.query(Symbol)
            .filter(
                Symbol.symbol == symbol.upper(),
                Symbol.is_active.is_(True),
            )
            .first()
        )

        if not db_symbol:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol '{symbol.upper()}' not found",
            )

        if not db_symbol.truedata_symbol_id:
            raise HTTPException(
                status_code=404,
                detail=f"No TrueData mapping found for '{symbol.upper()}'",
            )

        tick = (
            db.query(LiveTick)
            .filter(
                LiveTick.symbol_id == db_symbol.truedata_symbol_id
            )
            .order_by(
                desc(LiveTick.timestamp),
                desc(LiveTick.id),
            )
            .first()
        )

        if not tick:
            raise HTTPException(
                status_code=404,
                detail=f"No market data available for '{symbol.upper()}'",
            )

        return tick_to_dict(
            tick,
            db_symbol,
        )

    finally:
        db.close()


@router.get("/{symbol}/history")
def get_market_history(
    symbol: str,
    limit: int = Query(
        default=200,
        ge=1,
        le=500,
    ),
):
    """
    Return completed EOD historical market data.

    Data source:
        historical_bars PostgreSQL table

    Timeframe:
        1D / EOD

    The newest completed trading day is returned first.
    """
    db = SessionLocal()

    try:
        db_symbol = (
            db.query(Symbol)
            .filter(
                Symbol.symbol == symbol.upper(),
                Symbol.is_active.is_(True),
            )
            .first()
        )

        if not db_symbol:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol '{symbol.upper()}' not found",
            )

        if not db_symbol.truedata_symbol_id:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No TrueData mapping found for "
                    f"'{symbol.upper()}'"
                ),
            )

        bars = (
            db.query(HistoricalBar)
            .filter(
                HistoricalBar.symbol_id == db_symbol.truedata_symbol_id,
                HistoricalBar.timeframe == "1D",
            )
            .order_by(
                desc(HistoricalBar.timestamp),
                desc(HistoricalBar.id),
            )
            .limit(limit)
            .all()
        )

        return {
            "symbol": db_symbol.symbol,
            "exchange": db_symbol.exchange,
            "truedata_symbol_id": db_symbol.truedata_symbol_id,
            "timeframe": "1D",
            "count": len(bars),
            "data": [
                {
                    "timestamp": bar.timestamp,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "oi": bar.oi,
                }
                for bar in bars
            ],
        }

    finally:
        db.close()
