"""Database tables used only by the independent Kite provider evaluation."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class KiteTestSymbol(Base):
    __tablename__ = "kite_test_symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    instrument_token: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    exchange_token: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    tick_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class KiteTestTick(Base):
    __tablename__ = "kite_test_ticks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    instrument_token: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    ltp: Mapped[float | None] = mapped_column(Float, nullable=True)
    ltq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    atp: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open: Mapped[float | None] = mapped_column(Float, nullable=True)
    high: Mapped[float | None] = mapped_column(Float, nullable=True)
    low: Mapped[float | None] = mapped_column(Float, nullable=True)
    prev_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    oi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    bid_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Preserve provider-specific timestamps separately for an honest latency comparison.
    last_trade_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exchange_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
