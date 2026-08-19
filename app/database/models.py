from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    truedata_symbol_id: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
    )

    exchange: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NSE",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class LiveTick(Base):
    __tablename__ = "live_ticks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    symbol_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    ltp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    ltq: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    atp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    total_volume: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    open: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    high: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    low: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    prev_close: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    oi: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    prev_oi: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    turnover: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    bid: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    bid_qty: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    ask: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    ask_qty: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )


class HistoricalBar(Base):
    __tablename__ = "historical_bars"

    __table_args__ = (
        UniqueConstraint(
            "symbol_id",
            "timestamp",
            "timeframe",
            name="uq_historical_symbol_timestamp_timeframe",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    symbol_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    timeframe: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1D",
        index=True,
    )

    open: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    high: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    low: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    close: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    volume: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    oi: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
