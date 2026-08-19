import argparse
import calendar
import csv
import io
import time
from datetime import date

import httpx
from sqlalchemy.dialects.postgresql import insert

from app.config.settings import settings
from app.database.connection import SessionLocal
from app.database.models import HistoricalBar, Symbol


HISTORY_URL = "https://history.truedata.in/getlastnbars"

# 200 trading bars is more than enough for six calendar months.
NBARS = 200

INTERVAL = "eod"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10


def get_access_token() -> str:
    """Generate a fresh TrueData bearer token."""

    response = httpx.post(
        "https://auth.truedata.in/token",
        data={
            "username": settings.truedata_username,
            "password": settings.truedata_password,
            "grant_type": "password",
        },
        timeout=30.0,
    )

    response.raise_for_status()

    data = response.json()

    token = data.get("access_token")

    if not token:
        raise RuntimeError(
            "TrueData authentication succeeded but no access_token "
            f"was returned: {data}"
        )

    return token


def get_date_range() -> tuple[date, date]:
    """
    Return the last six calendar months ending today.
    """

    end_date = date.today()

    month = end_date.month - 6
    year = end_date.year

    if month <= 0:
        month += 12
        year -= 1

    last_day = calendar.monthrange(year, month)[1]

    start_date = date(
        year,
        month,
        min(end_date.day, last_day),
    )

    return start_date, end_date


def fetch_symbol_history(
    client: httpx.Client,
    token: str,
    symbol: str,
) -> list[dict]:

    for attempt in range(1, MAX_RETRIES + 1):

        response = client.get(
            HISTORY_URL,
            params={
                "symbol": symbol,
                "response": "csv",
                "nbars": NBARS,
                "interval": INTERVAL,
                "bidask": 0,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
            timeout=30.0,
        )

        if response.status_code == 429:

            if attempt == MAX_RETRIES:
                response.raise_for_status()

            print(
                f"  HTTP 429 for {symbol}. "
                f"Retrying in {RETRY_DELAY_SECONDS}s "
                f"({attempt}/{MAX_RETRIES})..."
            )

            time.sleep(RETRY_DELAY_SECONDS)

            continue

        response.raise_for_status()

        text = response.text.strip()

        if not text:
            return []

        reader = csv.DictReader(
            io.StringIO(text)
        )

        rows = []

        for row in reader:

            timestamp = row.get("timestamp")

            if not timestamp:
                continue

            rows.append(
                {
                    "timestamp": timestamp,
                    "open": row.get("dopen"),
                    "high": row.get("dhigh"),
                    "low": row.get("dlow"),
                    "close": row.get("dclose"),
                    "volume": row.get("volume"),
                    "oi": row.get("oi"),
                }
            )

        return rows

    return []


def import_symbol(
    db,
    client: httpx.Client,
    token: str,
    symbol: Symbol,
    start_date: date,
    end_date: date,
) -> int:

    rows = fetch_symbol_history(
        client,
        token,
        symbol.symbol,
    )

    records = []

    for row in rows:

        row_date = date.fromisoformat(
            row["timestamp"][:10]
        )

        # Only store completed dates inside the requested period.
        if row_date < start_date:
            continue

        if row_date > end_date:
            continue

        records.append(
            {
                "symbol_id": symbol.truedata_symbol_id,
                "timestamp": row_date,
                "timeframe": "1D",
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(
                    float(row["volume"] or 0)
                ),
                "oi": int(
                    float(row["oi"] or 0)
                ),
            }
        )

    if not records:
        return 0

    statement = insert(
        HistoricalBar
    ).values(records)

    statement = statement.on_conflict_do_nothing(
        constraint="uq_historical_symbol_timestamp_timeframe"
    )

    result = db.execute(statement)

    db.commit()

    return result.rowcount or 0


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Import TrueData six-month EOD historical data."
    )

    parser.add_argument(
        "--symbols",
        nargs="+",
        help=(
            "Specific symbols to import. "
            "Example: --symbols KENNAMET KOVAI"
        ),
    )

    return parser.parse_args()


def main() -> None:

    args = parse_arguments()

    start_date, end_date = get_date_range()

    print("=" * 70)
    print("TrueData Historical Data Import")
    print("=" * 70)
    print(
        f"Period : {start_date} -> {end_date}"
    )
    print("Timeframe : 1D / EOD")
    print("=" * 70)

    print("\nGenerating TrueData access token...")

    token = get_access_token()

    print("Authentication successful.")

    db = SessionLocal()

    try:

        query = (
            db.query(Symbol)
            .filter(
                Symbol.is_active.is_(True),
                Symbol.truedata_symbol_id.isnot(None),
            )
        )

        if args.symbols:

            requested_symbols = [
                symbol.upper()
                for symbol in args.symbols
            ]

            query = query.filter(
                Symbol.symbol.in_(requested_symbols)
            )

        symbols = (
            query
            .order_by(Symbol.id)
            .all()
        )

        print(
            f"\nSymbols found: {len(symbols)}"
        )

        if args.symbols:
            print(
                "Requested symbols: "
                + ", ".join(
                    symbol.upper()
                    for symbol in args.symbols
                )
            )

        if not symbols:

            raise RuntimeError(
                "No matching active symbols with "
                "TrueData mappings found."
            )

        total_inserted = 0
        successful = 0
        failed = []

        with httpx.Client() as client:

            for index, symbol in enumerate(
                symbols,
                start=1,
            ):

                print(
                    f"\n[{index}/{len(symbols)}] "
                    f"Fetching {symbol.symbol}..."
                )

                try:

                    count = import_symbol(
                        db,
                        client,
                        token,
                        symbol,
                        start_date,
                        end_date,
                    )

                    total_inserted += count
                    successful += 1

                    print(
                        f"  {symbol.symbol}: "
                        f"{count} new EOD rows inserted"
                    )

                except httpx.HTTPStatusError as exc:

                    db.rollback()

                    failed.append(
                        symbol.symbol
                    )

                    print(
                        f"  ERROR {symbol.symbol}: "
                        f"HTTP "
                        f"{exc.response.status_code}"
                    )

                    print(
                        f"  Response: "
                        f"{exc.response.text[:300]}"
                    )

                except Exception as exc:

                    db.rollback()

                    failed.append(
                        symbol.symbol
                    )

                    print(
                        f"  ERROR {symbol.symbol}: "
                        f"{exc}"
                    )

    finally:

        db.close()

    print("\n" + "=" * 70)
    print("Historical import completed")
    print("=" * 70)

    print(
        f"Period          : "
        f"{start_date} -> {end_date}"
    )

    print(
        f"Symbols requested: "
        f"{len(symbols)}"
    )

    print(
        f"Successful       : "
        f"{successful}"
    )

    print(
        f"Failed           : "
        f"{len(failed)}"
    )

    print(
        f"New rows inserted: "
        f"{total_inserted}"
    )

    if failed:

        print(
            "Failed symbols   : "
            + ", ".join(failed)
        )

    print("=" * 70)


if __name__ == "__main__":
    main()
