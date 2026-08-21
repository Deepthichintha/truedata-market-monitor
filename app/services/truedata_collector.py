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

# TrueData applies the symbol limit to the whole WebSocket subscription,
# not separately to NSE and BSE. Keep this configurable so it can be raised
# when the TrueData account is upgraded (for example, to 60+ symbols).
TRUEDATA_SYMBOL_LIMIT = int(os.getenv("TRUEDATA_SYMBOL_LIMIT", "50"))
MAX_BSE_SYMBOLS = 10
MAX_NSE_SYMBOLS = 50


def get_active_symbols(db: Session) -> list[str]:
    """Return the configured NSE + BSE universe from the database."""
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
    nse_symbols = [row.symbol for row in nse_rows][:MAX_NSE_SYMBOLS]

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
        row.symbol for row in bse_rows if row.symbol in BSE_SYMBOLS
    ][:MAX_BSE_SYMBOLS]

    return nse_symbols + bse_symbols


def select_subscribed_symbols(symbols: list[str]) -> tuple[list[str], int, int]:
    """
    Select symbols that can actually be subscribed under the TrueData plan.

    BSE is deliberately selected first so a 50-symbol TrueData plan does not
    silently consume the entire allowance with NSE and leave BSE stale.

    With the current 50-symbol account and a 50 NSE + 10 BSE application
    universe this results in 40 NSE + 10 BSE live symbols. After increasing
    TRUEDATA_SYMBOL_LIMIT to 60 (and having the corresponding TrueData plan),
    all 50 NSE + 10 BSE symbols are subscribed automatically.
    """
    bse = [symbol for symbol in symbols if symbol in BSE_SYMBOLS]
    nse = [symbol for symbol in symbols if symbol not in BSE_SYMBOLS]

    bse = bse[:MAX_BSE_SYMBOLS]
    nse = nse[:MAX_NSE_SYMBOLS]

    limit = max(TRUEDATA_SYMBOL_LIMIT, 1)
    selected_bse = bse[:limit]
    remaining = max(limit - len(selected_bse), 0)
    selected_nse = nse[:remaining]

    selected = selected_bse + selected_nse
    return selected, len(selected_nse), len(selected_bse)


def save_tick(db: Session, trade_data: dict) -> None:
    """Save a parsed TrueData trade into PostgreSQL."""
    symbol_id = str(trade_data["symbol_id"])

    previous_tick = (
        db.query(LiveTick)
        .filter(LiveTick.symbol_id == symbol_id)
        .order_by(LiveTick.timestamp.desc(), LiveTick.id.desc())
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
        bid=previous_tick.bid if previous_tick else None,
        bid_qty=previous_tick.bid_qty if previous_tick else None,
        ask=previous_tick.ask if previous_tick else None,
        ask_qty=previous_tick.ask_qty if previous_tick else None,
    )

    db.add(tick)
    db.commit()


def update_bidask(db: Session, bidask: list) -> None:
    """Persist a normal TrueData best Bid/Ask update."""
    if not isinstance(bidask, list) or len(bidask) < 6:
        print(f"Ignoring malformed Bid/Ask update: {bidask}")
        return

    symbol_id = str(bidask[0])
    timestamp = bidask[1]

    try:
        bid = float(bidask[2])
        bid_qty = int(float(bidask[3]))
        ask = float(bidask[4])
        ask_qty = int(float(bidask[5]))
    except (TypeError, ValueError) as exc:
        print(f"Ignoring invalid Bid/Ask update {bidask}: {exc}")
        return

    latest_tick = (
        db.query(LiveTick)
        .filter(LiveTick.symbol_id == symbol_id)
        .order_by(LiveTick.timestamp.desc(), LiveTick.id.desc())
        .first()
    )

    if latest_tick is None:
        print(f"No LiveTick found for TrueData symbol: {symbol_id}")
        return

    latest_tick.bid = bid
    latest_tick.bid_qty = bid_qty
    latest_tick.ask = ask
    latest_tick.ask_qty = ask_qty
    db.commit()

    print(
        f"Saved Bid/Ask | TrueData ID: {symbol_id} | Timestamp: {timestamp} | "
        f"Bid: {bid} ({bid_qty}) | Ask: {ask} ({ask_qty})"
    )


def parse_bidask_l2(bidask_l2: list) -> tuple[float, int, float, int] | None:
    """Parse the first/best level from a TrueData Bid/Ask L2 payload."""
    if not isinstance(bidask_l2, list) or len(bidask_l2) < 8:
        return None

    try:
        bid = float(bidask_l2[3])
        bid_qty = int(float(bidask_l2[4]))
        ask = float(bidask_l2[6])
        ask_qty = int(float(bidask_l2[7]))
    except (TypeError, ValueError, IndexError):
        return None

    if bid <= 0 or ask <= 0 or bid_qty < 0 or ask_qty < 0:
        return None

    return bid, bid_qty, ask, ask_qty


def update_bidask_l2(db: Session, bidask_l2: list) -> None:
    """Persist the best bid/ask from a TrueData Level-2 message."""
    if not isinstance(bidask_l2, list) or len(bidask_l2) < 8:
        print(f"Ignoring malformed Bid/Ask L2 update: {bidask_l2}")
        return

    symbol_id = str(bidask_l2[0])
    timestamp = bidask_l2[1]
    parsed = parse_bidask_l2(bidask_l2)

    if parsed is None:
        print(f"Could not parse Bid/Ask L2 for TrueData ID: {symbol_id}")
        return

    bid, bid_qty, ask, ask_qty = parsed
    latest_tick = (
        db.query(LiveTick)
        .filter(LiveTick.symbol_id == symbol_id)
        .order_by(LiveTick.timestamp.desc(), LiveTick.id.desc())
        .first()
    )

    if latest_tick is None:
        print(f"No LiveTick found for TrueData symbol: {symbol_id}")
        return

    latest_tick.bid = bid
    latest_tick.bid_qty = bid_qty
    latest_tick.ask = ask
    latest_tick.ask_qty = ask_qty
    db.commit()

    print(
        f"Saved Bid/Ask L2 | TrueData ID: {symbol_id} | Timestamp: {timestamp} | "
        f"Bid: {bid} ({bid_qty}) | Ask: {ask} ({ask_qty})"
    )


def run_collector() -> None:
    """Start the TrueData WebSocket collector for the NSE+BSE universe."""
    username = os.getenv("TRUEDATA_USERNAME")
    password = os.getenv("TRUEDATA_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "TRUEDATA_USERNAME and TRUEDATA_PASSWORD must be configured in .env"
        )

    db = SessionLocal()
    ws = None

    try:
        all_symbols = get_active_symbols(db)
        if not all_symbols:
            raise RuntimeError("No active NSE or BSE symbols found in database.")

        subscribed_symbols, nse_count, bse_count = select_subscribed_symbols(all_symbols)
        total_available = len(all_symbols)

        available_nse = len([s for s in all_symbols if s not in BSE_SYMBOLS])
        available_bse = len([s for s in all_symbols if s in BSE_SYMBOLS])

        print("=" * 70)
        print("TrueData Market Data Collector")
        print("=" * 70)
        print(f"WebSocket: {TRUEDATA_WS_URL}")
        print("Mode: NSE + BSE")
        print(f"Application symbols: {total_available}")
        print(f"Available NSE: {available_nse}")
        print(f"Available BSE: {available_bse}")
        print(f"TrueData symbol limit: {TRUEDATA_SYMBOL_LIMIT}")
        print(f"Live NSE subscription: {nse_count}")
        print(f"Live BSE subscription: {bse_count}")
        print(f"Total live subscription: {len(subscribed_symbols)}")

        if total_available > TRUEDATA_SYMBOL_LIMIT:
            print(
                "WARNING: Application has more symbols than the current TrueData "
                "plan limit. BSE is prioritized so both NSE and BSE receive live data."
            )
            print(
                "To stream the complete universe, increase the TrueData symbol limit "
                "and set TRUEDATA_SYMBOL_LIMIT accordingly."
            )

        print("=" * 70)
        print("Subscribed symbols:")
        print(", ".join(subscribed_symbols))
        print()

        url = f"{TRUEDATA_WS_URL}?user={username}&password={password}"
        print("Connecting to TrueData...")
        ws = websocket.create_connection(url, timeout=30)
        print("Connected to TrueData.")
        print()

        subscription = {
            "method": "addsymbol",
            "symbols": subscribed_symbols,
        }

        print(f"Subscribing to {len(subscribed_symbols)} symbols...")
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
                added = data.get("symbolsadded")
                total = data.get("totalsymbolsubscribed")
                print("Subscription confirmed.")
                print(f"Symbols added: {added}")
                print(f"Total subscribed: {total}")

                expected = len(subscribed_symbols)
                if total != expected:
                    print(
                        f"WARNING: Expected {expected} subscribed symbols but "
                        f"TrueData reports {total}."
                    )
                continue

            if "trade" in data:
                try:
                    trade_data = parse_trade(data)
                    save_tick(db, trade_data)
                    print(
                        f"Saved tick | TrueData ID: {trade_data['symbol_id']} | "
                        f"Timestamp: {trade_data['timestamp']} | "
                        f"LTP: {trade_data['ltp']} | LTQ: {trade_data['ltq']} | "
                        f"Volume: {trade_data['total_volume']}"
                    )
                except Exception as exc:
                    db.rollback()
                    print(f"Failed to process trade: {exc}")
                continue

            if "bidask" in data:
                try:
                    update_bidask(db, data["bidask"])
                except Exception as exc:
                    db.rollback()
                    print(f"Failed to process Bid/Ask update: {exc}")
                continue

            if "bidaskL2" in data:
                try:
                    update_bidask_l2(db, data["bidaskL2"])
                except Exception as exc:
                    db.rollback()
                    print(f"Failed to process Bid/Ask L2 update: {exc}")
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


if __name__ == "__main__":
    run_collector()
