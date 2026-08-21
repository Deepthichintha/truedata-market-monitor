import json
import os

import websocket
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.config.bse_symbols import BSE_SYMBOLS
from app.database.connection import SessionLocal
from app.database.models import LiveTick, Symbol
from app.services.truedata_parser import parse_trade

load_dotenv()

TRUEDATA_WS_URL = "wss://push.truedata.in:8086"

MAX_NSE_SYMBOLS = 50
MAX_BSE_SYMBOLS = 10


def get_active_symbols(db: Session) -> list[str]:
    """
    Load NSE and BSE symbols for one TrueData subscription.

    NSE:
        Up to 50 active symbols.

    BSE:
        Configured BSE symbols, up to 10.

    Both exchanges are returned together so the collector
    uses one WebSocket connection for NSE + BSE.
    """

    nse_rows = (
        db.query(Symbol)
        .filter(
            Symbol.is_active.is_(True),
            Symbol.exchange == "NSE",
            Symbol.truedata_symbol_id.isnot(None),
        )
        .order_by(Symbol.id)
        .all()
    )

    nse_symbols = [
        row.symbol
        for row in nse_rows
    ][:MAX_NSE_SYMBOLS]

    bse_rows = (
        db.query(Symbol)
        .filter(
            Symbol.is_active.is_(True),
            Symbol.exchange == "BSE",
            Symbol.truedata_symbol_id.isnot(None),
        )
        .order_by(Symbol.id)
        .all()
    )

    bse_symbols = [
        row.symbol
        for row in bse_rows
        if row.symbol in BSE_SYMBOLS
    ][:MAX_BSE_SYMBOLS]

    return nse_symbols + bse_symbols


def save_tick(
    db: Session,
    trade_data: dict,
) -> None:
    """
    Save a parsed TrueData trade into PostgreSQL.

    Existing Bid/Ask values are carried forward from
    the previous tick for the same TrueData symbol.
    """

    symbol_id = str(
        trade_data["symbol_id"]
    )

    previous_tick = (
        db.query(LiveTick)
        .filter(
            LiveTick.symbol_id == symbol_id
        )
        .order_by(
            LiveTick.timestamp.desc(),
            LiveTick.id.desc(),
        )
        .first()
    )

    tick = LiveTick(
        symbol_id=symbol_id,
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
        bid=(
            previous_tick.bid
            if previous_tick
            else None
        ),
        bid_qty=(
            previous_tick.bid_qty
            if previous_tick
            else None
        ),
        ask=(
            previous_tick.ask
            if previous_tick
            else None
        ),
        ask_qty=(
            previous_tick.ask_qty
            if previous_tick
            else None
        ),
    )

    db.add(tick)
    db.commit()


def update_bidask(
    db: Session,
    bidask: list,
) -> None:
    """
    Process the normal TrueData Bid/Ask message.

    Format:

        [
            symbol_id,
            timestamp,
            bid,
            bid_qty,
            ask,
            ask_qty
        ]
    """

    if (
        not isinstance(bidask, list)
        or len(bidask) < 6
    ):
        print(
            "Ignoring malformed Bid/Ask update: "
            f"{bidask}"
        )
        return

    symbol_id = str(
        bidask[0]
    )

    timestamp = bidask[1]

    try:
        bid = float(bidask[2])
        bid_qty = int(
            float(bidask[3])
        )
        ask = float(bidask[4])
        ask_qty = int(
            float(bidask[5])
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        print(
            "Ignoring invalid Bid/Ask update "
            f"{bidask}: {exc}"
        )
        return

    latest_tick = (
        db.query(LiveTick)
        .filter(
            LiveTick.symbol_id == symbol_id
        )
        .order_by(
            LiveTick.timestamp.desc(),
            LiveTick.id.desc(),
        )
        .first()
    )

    if latest_tick is None:
        print(
            "No LiveTick found for TrueData "
            f"symbol: {symbol_id}"
        )
        return

    latest_tick.bid = bid
    latest_tick.bid_qty = bid_qty
    latest_tick.ask = ask
    latest_tick.ask_qty = ask_qty

    db.commit()

    print(
        "Saved Bid/Ask | "
        f"TrueData ID: {symbol_id} | "
        f"Timestamp: {timestamp} | "
        f"Bid: {bid} ({bid_qty}) | "
        f"Ask: {ask} ({ask_qty})"
    )


def parse_bidask_l2(
    bidask_l2: list,
) -> tuple[float, int, float, int] | None:
    """
    Parse a TrueData bidaskL2 message.

    Observed structure:

        [
            symbol_id,
            timestamp,
            level,
            bid_price,
            bid_qty,
            level,
            ask_price,
            ask_qty,
            ...
        ]

    The first level contains the best available
    bid and ask values in the observed payload.

    Returns:

        bid,
        bid_qty,
        ask,
        ask_qty
    """

    if (
        not isinstance(bidask_l2, list)
        or len(bidask_l2) < 8
    ):
        return None

    try:
        bid = float(
            bidask_l2[3]
        )

        bid_qty = int(
            float(bidask_l2[4])
        )

        ask = float(
            bidask_l2[6]
        )

        ask_qty = int(
            float(bidask_l2[7])
        )

    except (
        TypeError,
        ValueError,
        IndexError,
    ):
        return None

    if bid <= 0 or ask <= 0:
        return None

    if bid_qty < 0 or ask_qty < 0:
        return None

    return (
        bid,
        bid_qty,
        ask,
        ask_qty,
    )


def update_bidask_l2(
    db: Session,
    bidask_l2: list,
) -> None:
    """
    Process a TrueData Level-2 Bid/Ask message.

    The best bid and best ask from the observed
    TrueData L2 payload are persisted onto the
    latest LiveTick.
    """

    if (
        not isinstance(bidask_l2, list)
        or len(bidask_l2) < 8
    ):
        print(
            "Ignoring malformed Bid/Ask L2 update: "
            f"{bidask_l2}"
        )
        return

    symbol_id = str(
        bidask_l2[0]
    )

    timestamp = bidask_l2[1]

    parsed = parse_bidask_l2(
        bidask_l2
    )

    if parsed is None:
        print(
            "Could not parse Bid/Ask L2 "
            f"for TrueData ID: {symbol_id}"
        )
        return

    bid, bid_qty, ask, ask_qty = parsed

    latest_tick = (
        db.query(LiveTick)
        .filter(
            LiveTick.symbol_id == symbol_id
        )
        .order_by(
            LiveTick.timestamp.desc(),
            LiveTick.id.desc(),
        )
        .first()
    )

    if latest_tick is None:
        print(
            "No LiveTick found for TrueData "
            f"symbol: {symbol_id}"
        )
        return

    latest_tick.bid = bid
    latest_tick.bid_qty = bid_qty
    latest_tick.ask = ask
    latest_tick.ask_qty = ask_qty

    db.commit()

    print(
        "Saved Bid/Ask L2 | "
        f"TrueData ID: {symbol_id} | "
        f"Timestamp: {timestamp} | "
        f"Bid: {bid} ({bid_qty}) | "
        f"Ask: {ask} ({ask_qty})"
    )


def run_collector() -> None:
    """
    Start the TrueData WebSocket collector.

    One collector subscribes to both exchanges:

        50 NSE symbols
        10 BSE symbols

    Total target subscription:

        60 symbols
    """

    username = os.getenv(
        "TRUEDATA_USERNAME"
    )

    password = os.getenv(
        "TRUEDATA_PASSWORD"
    )

    if not username or not password:
        raise RuntimeError(
            "TRUEDATA_USERNAME and "
            "TRUEDATA_PASSWORD must be "
            "configured in .env"
        )

    db = SessionLocal()
    ws = None

    try:
        symbols = get_active_symbols(db)

        if not symbols:
            raise RuntimeError(
                "No active NSE or BSE symbols found "
                "in database."
            )

        nse_count = len(
            [
                symbol
                for symbol in symbols
                if symbol not in BSE_SYMBOLS
            ]
        )

        bse_count = len(
            [
                symbol
                for symbol in symbols
                if symbol in BSE_SYMBOLS
            ]
        )

        print("=" * 70)
        print(
            "TrueData Market Data Collector"
        )
        print("=" * 70)
        print(
            f"WebSocket: {TRUEDATA_WS_URL}"
        )
        print(
            "Mode: NSE + BSE"
        )
        print(
            f"NSE symbols: {nse_count}"
        )
        print(
            f"BSE symbols: {bse_count}"
        )
        print(
            f"Total symbols: {len(symbols)}"
        )
        print("=" * 70)

        print("Symbols:")
        print(
            ", ".join(symbols)
        )

        print()

        url = (
            f"{TRUEDATA_WS_URL}"
            f"?user={username}"
            f"&password={password}"
        )

        print(
            "Connecting to TrueData..."
        )

        ws = websocket.create_connection(
            url,
            timeout=30,
        )

        print(
            "Connected to TrueData."
        )

        print()

        subscription = {
            "method": "addsymbol",
            "symbols": symbols,
        }

        print(
            f"Subscribing to "
            f"{len(symbols)} symbols..."
        )

        ws.send(
            json.dumps(
                subscription
            )
        )

        print(
            "Subscription request sent."
        )

        print()

        while True:
            message = ws.recv()

            if not message:
                continue

            try:
                data = json.loads(
                    message
                )

            except json.JSONDecodeError:
                print(
                    "Received non-JSON "
                    "message:",
                    message,
                )
                continue

            # -------------------------------------------------
            # Heartbeat
            # -------------------------------------------------

            if (
                data.get("message")
                == "HeartBeat"
            ):
                print(
                    "Heartbeat: "
                    f"{data.get('timestamp')}"
                )
                continue

            # -------------------------------------------------
            # Subscription confirmation
            # -------------------------------------------------

            if (
                data.get("message")
                == "symbols added"
            ):
                print(
                    "Subscription confirmed."
                )

                print(
                    "Symbols added: "
                    f"{data.get('symbolsadded')}"
                )

                print(
                    "Total subscribed: "
                    f"{data.get('totalsymbolsubscribed')}"
                )

                continue

            # -------------------------------------------------
            # Trade message
            # -------------------------------------------------

            if "trade" in data:
                try:
                    trade_data = parse_trade(
                        data
                    )

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
            # Normal Bid/Ask message
            # -------------------------------------------------

            if "bidask" in data:
                try:
                    update_bidask(
                        db,
                        data["bidask"],
                    )

                except Exception as exc:
                    db.rollback()

                    print(
                        "Failed to process "
                        "Bid/Ask update:",
                        exc,
                    )

                continue

            # -------------------------------------------------
            # Level-2 Bid/Ask message
            # -------------------------------------------------

            if "bidaskL2" in data:
                try:
                    update_bidask_l2(
                        db,
                        data["bidaskL2"],
                    )

                except Exception as exc:
                    db.rollback()

                    print(
                        "Failed to process "
                        "Bid/Ask L2 update:",
                        exc,
                    )

                continue

            # -------------------------------------------------
            # Other TrueData messages
            # -------------------------------------------------

            print(
                "TrueData message:"
            )

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
                ws.close()
            except Exception:
                pass

        db.close()

        print(
            "Collector stopped."
        )


if __name__ == "__main__":
    run_collector()
