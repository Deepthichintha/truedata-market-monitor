"""Independent Kite WebSocket collector for provider comparison.

This module does not import or read the TrueData collector, TrueData IDs, or
TrueData live-tick tables. It uses Kite instrument tokens and writes only to
kite_test_* tables.
"""

from datetime import datetime, timezone
import threading

from kiteconnect import KiteTicker
from sqlalchemy import delete

from app.database.connection import Base, SessionLocal, engine
from app.kite.auth import get_access_token
from app.kite.config import KITE_API_KEY, KITE_ACCESS_TOKEN
from app.kite.instruments import download_instruments, map_test_universe, validate_test_universe
from app.kite.models import KiteTestSymbol, KiteTestTick


class KiteCollector:
    def __init__(self) -> None:
        self._ticker = None
        self._thread: threading.Thread | None = None
        self._stop_requested = False
        self._mapping: dict[int, dict] = {}
        self._last_error: str | None = None
        self._connected = False
        self._ticks_received = 0

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def status(self) -> dict:
        return {
            "running": self.running,
            "connected": self._connected,
            "ticks_received": self._ticks_received,
            "subscribed_instruments": len(self._mapping),
            "last_error": self._last_error,
        }

    def prepare_mapping(self) -> dict:
        path = download_instruments()
        rows = map_test_universe(path)
        validation = validate_test_universe(rows)
        if not validation["complete"]:
            raise RuntimeError(
                "Kite test universe is incomplete: " + ", ".join(validation["missing"])
            )

        Base.metadata.create_all(bind=engine, tables=[KiteTestSymbol.__table__, KiteTestTick.__table__])
        db = SessionLocal()
        try:
            db.execute(delete(KiteTestSymbol))
            for row in rows:
                db.add(KiteTestSymbol(**row))
            db.commit()
        finally:
            db.close()

        self._mapping = {row["instrument_token"]: row for row in rows}
        return {
            "file": str(path),
            "validation": validation,
            "instruments": rows,
        }

    def start(self) -> dict:
        if self.running:
            return self.status()

        if not KITE_API_KEY:
            raise RuntimeError("KITE_API_KEY is not configured")

        access_token = get_access_token() or KITE_ACCESS_TOKEN
        if not access_token:
            raise RuntimeError("Kite is not authenticated. Complete /api/kite-test/login first.")

        if not self._mapping:
            self.prepare_mapping()

        self._stop_requested = False
        self._last_error = None
        self._ticks_received = 0

        self._ticker = KiteTicker(KITE_API_KEY, access_token)
        self._ticker.on_connect = self._on_connect
        self._ticker.on_ticks = self._on_ticks
        self._ticker.on_close = self._on_close
        self._ticker.on_error = self._on_error
        self._ticker.on_reconnect = self._on_reconnect
        self._ticker.on_noreconnect = self._on_noreconnect

        self._thread = threading.Thread(
            target=self._ticker.connect,
            kwargs={"threaded": False},
            daemon=True,
            name="kite-test-collector",
        )
        self._thread.start()
        return self.status()

    def stop(self) -> None:
        self._stop_requested = True
        if self._ticker is not None:
            try:
                self._ticker.close()
            except Exception:
                pass
        self._connected = False

    def _on_connect(self, ws, response):
        tokens = list(self._mapping)
        ws.subscribe(tokens)
        ws.set_mode(ws.MODE_FULL, tokens)
        self._connected = True
        print(f"Kite connected — subscribed to {len(tokens)} NSE+BSE instruments")

    def _on_ticks(self, ws, ticks):
        db = SessionLocal()
        try:
            for tick in ticks:
                row = self._mapping.get(tick.get("instrument_token"))
                if not row:
                    continue

                depth = tick.get("depth") or {}
                buy = depth.get("buy") or []
                sell = depth.get("sell") or []
                best_bid = buy[0] if buy else {}
                best_ask = sell[0] if sell else {}

                timestamp = tick.get("exchange_timestamp") or tick.get("last_trade_time")
                last_trade_time = tick.get("last_trade_time")
                exchange_timestamp = tick.get("exchange_timestamp")

                db.add(
                    KiteTestTick(
                        symbol=row["symbol"],
                        exchange=row["exchange"],
                        instrument_token=row["instrument_token"],
                        timestamp=timestamp,
                        received_at=datetime.now(timezone.utc).replace(tzinfo=None),
                        ltp=tick.get("last_price"),
                        ltq=tick.get("last_traded_quantity"),
                        atp=tick.get("average_traded_price"),
                        total_volume=tick.get("volume_traded"),
                        open=(tick.get("ohlc") or {}).get("open"),
                        high=(tick.get("ohlc") or {}).get("high"),
                        low=(tick.get("ohlc") or {}).get("low"),
                        prev_close=(tick.get("ohlc") or {}).get("close"),
                        oi=tick.get("oi"),
                        bid=best_bid.get("price"),
                        bid_qty=best_bid.get("quantity"),
                        ask=best_ask.get("price"),
                        ask_qty=best_ask.get("quantity"),
                        last_trade_time=last_trade_time,
                        exchange_timestamp=exchange_timestamp,
                    )
                )
                self._ticks_received += 1

            db.commit()
        except Exception as exc:
            db.rollback()
            self._last_error = str(exc)
            print(f"Kite tick persistence error: {exc}")
        finally:
            db.close()

    def _on_close(self, ws, code, reason):
        self._connected = False
        print(f"Kite WebSocket closed: {code} {reason}")

    def _on_error(self, ws, code, reason):
        self._last_error = f"{code}: {reason}"
        print(f"Kite WebSocket error: {code} {reason}")

    def _on_reconnect(self, ws, attempts_count):
        print(f"Kite reconnect attempt: {attempts_count}")

    def _on_noreconnect(self, ws, attempts_count):
        self._connected = False
        print(f"Kite reconnect exhausted after {attempts_count} attempts")


collector = KiteCollector()
