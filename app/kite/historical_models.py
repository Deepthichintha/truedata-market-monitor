"""Independent Kite historical-candle storage model."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class KiteTestHistoricalBar(Base):
    __tablename__ = "kite_test_historical_bars"
    __table_args__ = (
        UniqueConstraint(
            "instrument_token",
            "candle_timestamp",
            "interval",
            name="uq_kite_hist_token_timestamp_interval",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    instrument_token: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    candle_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    interval: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)
    oi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
