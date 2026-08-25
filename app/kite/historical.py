"""Kite Historical Candle API client for the independent provider evaluation.

This module uses only Kite Connect instrument tokens and the Kite Historical
API. It never reads TrueData identifiers or TrueData historical tables.
"""

from datetime import date, datetime, timedelta

from kiteconnect import KiteConnect
from sqlalchemy import delete

from app.database.connection import Base, SessionLocal, engine
from app.kite.auth import get_access_token
from app.kite.config import KITE_ACCESS_TOKEN, KITE_API_KEY
from app.kite.historical_models import KiteTestHistoricalBar
from app.kite.instruments import download_instruments, map_test_universe, validate_test_universe


SUPPORTED_INTERVALS = {
    "minute", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute", "day"
}


def _client() -> KiteConnect:
    token = get_access_token() or KITE_ACCESS_TOKEN
    if not KITE_API_KEY:
        raise RuntimeError("KITE_API_KEY is not configured")
    if not token:
        raise RuntimeError("Kite is not authenticated. Complete /api/kite-test/login first.")

    kite = KiteConnect(api_key=KITE_API_KEY)
    kite.set_access_token(token)
    return kite


def _validate_range(from_date: date, to_date: date) -> None:
    if from_date > to_date:
        raise ValueError("from_date must be on or before to_date")
    if (to_date - from_date).days > 365:
        raise ValueError("Historical evaluation range cannot exceed 365 days per request")


def fetch_historical(
    from_date: date,
    to_date: date,
    interval: str = "day",
    include_oi: bool = True,
    replace_range: bool = True,
) -> dict:
    """Fetch historical candles for the exact Kite test universe and persist them."""
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(f"Unsupported interval: {interval}")
    _validate_range(from_date, to_date)

    path = download_instruments()
    rows = map_test_universe(path)
    validation = validate_test_universe(rows)
    if not validation["complete"]:
        raise RuntimeError(
            "Kite test universe is incomplete: " + ", ".join(validation["missing"])
        )

    Base.metadata.create_all(bind=engine, tables=[KiteTestHistoricalBar.__table__])

    kite = _client()
    db = SessionLocal()
    saved = 0
    instruments = 0

    try:
        if replace_range:
            db.execute(
                delete(KiteTestHistoricalBar).where(
                    KiteTestHistoricalBar.interval == interval,
                    KiteTestHistoricalBar.candle_timestamp >= datetime.combine(from_date, datetime.min.time()),
                    KiteTestHistoricalBar.candle_timestamp < datetime.combine(to_date + timedelta(days=1), datetime.min.time()),
                )
            )

        for row in rows:
            candles = kite.historical_data(
                row["instrument_token"],
                from_date,
                to_date,
                interval,
                continuous=False,
                oi=include_oi,
            )
            instruments += 1

            for candle in candles:
                db.add(
                    KiteTestHistoricalBar(
                        symbol=row["symbol"],
                        exchange=row["exchange"],
                        instrument_token=row["instrument_token"],
                        candle_timestamp=candle["date"],
                        interval=interval,
                        open=candle.get("open"),
                        high=candle.get("high"),
                        low=candle.get("low"),
                        close=candle.get("close"),
                        volume=candle.get("volume"),
                        oi=candle.get("oi"),
                    )
                )
                saved += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {
        "provider": "kite",
        "interval": interval,
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "include_oi": include_oi,
        "instruments": instruments,
        "candles_saved": saved,
        "validation": validation,
    }
