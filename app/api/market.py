from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc

from app.database.connection import SessionLocal
from app.database.models import LiveTick, Symbol

router = APIRouter(
    prefix="/api/market",
    tags=["Market"],
)


def tick_to_dict(tick: LiveTick, symbol: Symbol | None = None) -> dict:
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
                .order_by(desc(LiveTick.timestamp), desc(LiveTick.id))
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
                LiveTick.symbol_id
                == db_symbol.truedata_symbol_id
            )
            .order_by(desc(LiveTick.timestamp), desc(LiveTick.id))
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
        default=20,
        ge=1,
        le=500,
    ),
):
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

        ticks = (
            db.query(LiveTick)
            .filter(
                LiveTick.symbol_id
                == db_symbol.truedata_symbol_id
            )
            .order_by(
                desc(LiveTick.timestamp),
                desc(LiveTick.id),
            )
            .limit(limit)
            .all()
        )

        return {
            "symbol": db_symbol.symbol,
            "exchange": db_symbol.exchange,
            "truedata_symbol_id": db_symbol.truedata_symbol_id,
            "count": len(ticks),
            "data": [
                tick_to_dict(
                    tick,
                    db_symbol,
                )
                for tick in ticks
            ],
        }

    finally:
        db.close()
