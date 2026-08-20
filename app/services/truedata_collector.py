import json
import os

import websocket
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import LiveTick, Symbol
from app.services.truedata_parser import parse_trade

load_dotenv()

TRUEDATA_WS_URL = "wss://push.truedata.in:8086"


def get_active_symbols(db: Session) -> list[str]:
    """
    Load active NSE symbols from PostgreSQL.

    TrueData subscription uses the human-readable
    exchange symbols, not the internal TrueData numeric IDs.
    """
    rows = (
        db.query(Symbol)
        .filter(
            Symbol.is_active.is_(True),
            Symbol.truedata_symbol_id.isnot(None),
        )
        .order_by(Symbol.id)
        .all()
    )
    return [row.symbol for row in rows]


def save_tick(db: Session, trade_data: dict) -> None:
    """Save a parsed TrueData trade into PostgreSQL."""
    tick = LiveTick(
        symbol_id=trade_data["symbol_id"],
        timestamp=trade_data["timestamp"],
        ltp=trade_data["ltp"],
        ltq=trade_data["ltq"],
        atp=trade_data["atp"],
        total_volume=trade_data["total_volume"],
        open=trade_data["open"],
        high=trade_data["high"],
        low=trade_data["low"],
        prev_close=trade_data["prev_close"],
        oi=trade_data["oi"],
        prev_oi=trade_data["prev_oi"],
        turnover=trade_data["turnover"],
        bid=None,
        bid_qty=None,
        ask=None,
        ask_qty=None,
    )
    db.add(tick)
    db.commit()


def update_bidask(db: Session, bidask: list) -> None:
    """
    Persist a TrueData bid/ask update onto the latest LiveTick for the symbol.

    TrueData bidask format observed from the live feed:
        [truedata_symbol_id, timestamp, bid, bid_qty, ask, ask_qty]
    """
    if len(bidask) < 6:
        print(f"Ignoring malformed Bid/Ask update: {bidask}")
        return

    truedata_symbol_id = str(bidask[0])
    timestamp = bidask[1]

    try:
        bid = float(bidask[2])
        bid_qty = int(float(bidask[3]))
        ask = float(bidask[4])
        ask_qty = int(float(bidask[5]))
    except (TypeError, ValueError) as exc:
        print(f"Ignoring invalid Bid/Ask update {bidask}: {exc}")
        return

    symbol = (
        db.query(Symbol)
        .filter(Symbol.truedata_symbol_id == truedata_symbol_id)
        .first()
    )

    if symbol is None:
        print(f"Bid/Ask symbol not found: {truedata_symbol_id}")
        return

    latest_tick = (
        db.query(LiveTick)
        .filter(LiveTick.symbol_id == symbol.id)
        .order_by(LiveTick.timestamp.desc(), LiveTick.id.desc())
        .first()
    )

    if latest_tick is None:
        print(f"No LiveTick found for Bid/Ask symbol: {truedata_symbol_id}")
        return

    latest_tick.bid = bid
    latest_tick.bid_qty = bid_qty
    latest_tick.ask = ask
    latest_tick.ask_qty = ask_qty
    db.commit()

    print(
        "Saved Bid/Ask | "
        f"Symbol: {symbol.symbol} | "
        f"Timestamp: {timestamp} | "
        f"Bid: {bid} ({bid_qty}) | "
        f"Ask: {ask} ({ask_qty})"
    )


def run_collector() -> None:
    username = os.getenv("TRUEDATA_USERNAME")
    password = os.getenv("TRUEDATA_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "TRUEDATA_USERNAME and TRUEDATA_PASSWORD "
            "must be configured in .env"
        )

    db = SessionLocal()
    ws = None

    try:
        symbols = get_active_symbols(db)

        if not symbols:
            raise RuntimeError(
                "No active TrueData symbols found in database."
            )

        print("=" * 70)
        print("TrueData Market Data Collector")
        print("=" * 70)
        print(f"WebSocket: {TRUEDATA_WS_URL}")
        print(f"Symbols loaded from database: {len(symbols)}")
        print("=" * 70)

        print("Symbols:")
        print(", ".join(symbols))
        print()

        url = (
            f"{TRUEDATA_WS_URL}"
            f"?user={username}&password={password}"
        )

        print("Connecting to TrueData...")

        ws = websocket.create_connection(
            url,
            timeout=30,
        )

        print("Connected to TrueData.")
        print()

        subscription = {
            "method": "addsymbol",
            "symbols": symbols,
        }

        print(f"Subscribing to {len(symbols)} symbols...")
        ws.send(json.dumps(subscription))
        print("Subscription request sent.")
        print()

        while True:
            message = ws.recv()

            if not message:
                continue

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print("Received non-JSON message:", message)
                continue

            if data.get("message") == "HeartBeat":
                print(f"Heartbeat: {data.get('timestamp')}")
                continue

            if data.get("message") == "symbols added":
                print("Subscription confirmed.")
                print(f"Symbols added: {data.get('symbolsadded')}")
                print(f"Total subscribed: {data.get('totalsymbolsubscribed')}")
                continue

            if "trade" in data:
                try:
                    trade_data = parse_trade(data)
                    save_tick(db, trade_data)

                    print(
                        "Saved tick | "
                        f"TrueData ID: {trade_data['symbol_id']} | "
                        f"Timestamp: {trade_data['timestamp']} | "
                        f"LTP: {trade_data['ltp']} | "
                        f"LTQ: {trade_data['ltq']} | "
                        f"Volume: {trade_data['total_volume']}"
                    )
                except Exception as exc:
                    db.rollback()
                    print("Failed to process trade:", exc)
                continue

            if "bidask" in data:
                try:
                    update_bidask(db, data["bidask"])
                except Exception as exc:
                    db.rollback()
                    print("Failed to process Bid/Ask update:", exc)
                continue

            print("TrueData message:")
            try:
                print(json.dumps(data, indent=2))
            except Exception:
                print(data)

    except KeyboardInterrupt:
        print("\nStopping collector...")

    except Exception as exc:
        print(f"\nCollector error: {exc}")

    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        db.close()
        print("Collector stopped.")
