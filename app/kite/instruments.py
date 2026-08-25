"""Kite instrument dump download and exact NSE/BSE test-universe mapping."""

import csv
import gzip
import io
from pathlib import Path

import requests

from app.kite.config import (
    KITE_API_KEY,
    KITE_ACCESS_TOKEN,
    KITE_INSTRUMENTS_FILE,
    KITE_TEST_EXCHANGES,
    KITE_TEST_SYMBOLS,
)

INSTRUMENTS_URL = "https://api.kite.trade/instruments"


def download_instruments(path: Path = KITE_INSTRUMENTS_FILE) -> Path:
    """Download Kite's daily instrument dump without touching TrueData data."""
    path.parent.mkdir(parents=True, exist_ok=True)

    headers = {"X-Kite-Version": "3"}
    if KITE_API_KEY and KITE_ACCESS_TOKEN:
        headers["Authorization"] = f"token {KITE_API_KEY}:{KITE_ACCESS_TOKEN}"

    response = requests.get(INSTRUMENTS_URL, headers=headers, timeout=60)
    response.raise_for_status()

    payload = response.content
    try:
        payload = gzip.decompress(payload)
    except OSError:
        pass

    path.write_bytes(payload)
    return path


def _read_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def map_test_universe(path: Path = KITE_INSTRUMENTS_FILE) -> list[dict]:
    """Map the exact evaluation symbols independently to Kite tokens.

    Only NSE/BSE equity instruments are considered. The key is exchange plus
    tradingsymbol, so NSE and BSE are intentionally kept as separate records.
    """
    wanted = set(KITE_TEST_SYMBOLS)
    results: list[dict] = []

    for row in _read_rows(path):
        exchange = (row.get("exchange") or "").upper()
        symbol = (row.get("tradingsymbol") or "").upper()
        instrument_type = (row.get("instrument_type") or "").upper()
        segment = (row.get("segment") or "").upper()

        if exchange not in KITE_TEST_EXCHANGES:
            continue
        if symbol not in wanted:
            continue
        if instrument_type != "EQ" or segment not in {"NSE", "BSE"}:
            continue

        results.append(
            {
                "exchange": exchange,
                "symbol": symbol,
                "instrument_token": int(row["instrument_token"]),
                "exchange_token": row.get("exchange_token"),
                "name": row.get("name") or "",
                "tick_size": row.get("tick_size"),
            }
        )

    # Keep one deterministic row per exchange:symbol.
    unique = {(r["exchange"], r["symbol"]): r for r in results}
    return [
        unique[key]
        for key in sorted(unique, key=lambda x: (x[0], x[1]))
    ]


def validate_test_universe(rows: list[dict]) -> dict:
    found = {(r["exchange"], r["symbol"]) for r in rows}
    missing = [
        f"{exchange}:{symbol}"
        for exchange in KITE_TEST_EXCHANGES
        for symbol in KITE_TEST_SYMBOLS
        if (exchange, symbol) not in found
    ]
    return {
        "expected": len(KITE_TEST_SYMBOLS) * len(KITE_TEST_EXCHANGES),
        "found": len(rows),
        "missing": missing,
        "complete": not missing,
    }
