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
    """
    Save a parsed TrueData trade into PostgreSQL.
    """

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
        bid=trade_data["bid"],
        bid_qty=trade_data["bid_qty"],
        ask=trade_data["ask"],
        ask_qty=trade_data["ask_qty"],
    )

    db.add(tick)
    db.commit()


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
        # -------------------------------------------------
        # Load symbols from PostgreSQL
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Connect to TrueData
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Subscribe
        # -------------------------------------------------

        subscription = {
            "method": "addsymbol",
            "symbols": symbols,
        }

        print(f"Subscribing to {len(symbols)} symbols...")

        ws.send(json.dumps(subscription))

        print("Subscription request sent.")
        print()

        # -------------------------------------------------
        # Receive data
        # -------------------------------------------------

        while True:
            message = ws.recv()

            if not message:
                continue

            try:
                data = json.loads(message)

            except json.JSONDecodeError:
                print(
                    "Received non-JSON message:",
                    message,
                )
                continue

            # -------------------------------------------------
            # Heartbeat
            # -------------------------------------------------

            if data.get("message") == "HeartBeat":
                print(
                    f"Heartbeat: {data.get('timestamp')}"
                )
                continue

            # -------------------------------------------------
            # Subscription confirmation
            # -------------------------------------------------

            if data.get("message") == "symbols added":

                print(
                    "Subscription confirmed."
                )

                print(
                    f"Symbols added: "
                    f"{data.get('symbolsadded')}"
                )

                print(
                    f"Total subscribed: "
                    f"{data.get('totalsymbolsubscribed')}"
                )

                continue

            # -------------------------------------------------
            # Trade message
            # -------------------------------------------------

            if "trade" in data:

                try:
                    trade_data = parse_trade(data)

                    save_tick(
                        db,
                        trade_data,
                    )

                    print(
                        "Saved tick | "
                        f"TrueData ID: "
                        f"{trade_data['symbol_id']} | "
                        f"Timestamp: "
                        f"{trade_data['timestamp']} | "
                        f"LTP: "
                        f"{trade_data['ltp']} | "
                        f"LTQ: "
                        f"{trade_data['ltq']} | "
                        f"Volume: "
                        f"{trade_data['total_volume']}"
                    )

                except Exception as exc:

                    db.rollback()

                    print(
                        "Failed to process trade:",
                        exc,
                    )

                continue

            # -------------------------------------------------
            # Bid/Ask message
            # -------------------------------------------------

            if "bidask" in data:

                print(
                    "Bid/Ask update:",
                    data["bidask"],
                )

                continue

            # -------------------------------------------------
            # Other TrueData messages
            # -------------------------------------------------

            print("TrueData message:")

            try:
                print(
                    json.dumps(
                        data,
                        indent=2,
                    )
                )

            except Exception:
                print(data)

    except KeyboardInterrupt:

        print(
            "\nStopping collector..."
        )

    except Exception as exc:

        print(
            f"\nCollector error: {exc}"
        )

    finally:

        if ws is not None:

            try:
                ws.send(
                    json.dumps(
                        {
                            "method": "logout",
                        }
                    )
                )

            except Exception:
                pass

            try:
                ws.close()

            except Exception:
                pass

        if db is not None:
            db.close()

        print(
            "Collector stopped."
        )


if __name__ == "__main__":
    run_collector()
