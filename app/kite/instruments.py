"""Kite instrument dump download and exact NSE/BSE test-universe mapping."""

import csv
import gzip
from pathlib import Path

import requests

from app.kite.config import (
    KITE_API_KEY,
    KITE_ACCESS_TOKEN,
    KITE_INSTRUMENTS_FILE,
    KITE_TEST_BSE_SYMBOLS,
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
    """Map the existing NSE/BSE evaluation universe independently to Kite tokens."""
    wanted_by_exchange = {
        "NSE": set(KITE_TEST_SYMBOLS),
        "BSE": set(KITE_TEST_BSE_SYMBOLS),
    }
    results: list[dict] = []

    for row in _read_rows(path):
        exchange = (row.get("exchange") or "").upper()
        symbol = (row.get("tradingsymbol") or "").upper()
        instrument_type = (row.get("instrument_type") or "").upper()
        segment = (row.get("segment") or "").upper()

        if exchange not in KITE_TEST_EXCHANGES:
            continue
        if symbol not in wanted_by_exchange[exchange]:
            continue
        if instrument_type != "EQ" or segment != exchange:
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

    unique = {(r["exchange"], r["symbol"]): r for r in results}
    return [unique[key] for key in sorted(unique, key=lambda x: (x[0], x[1]))]


def validate_test_universe(rows: list[dict]) -> dict:
    expected_by_exchange = {
        "NSE": len(KITE_TEST_SYMBOLS),
        "BSE": len(KITE_TEST_BSE_SYMBOLS),
    }
    found = {(r["exchange"], r["symbol"]) for r in rows}
    missing = []

    for exchange, symbols in (
        ("NSE", KITE_TEST_SYMBOLS),
        ("BSE", KITE_TEST_BSE_SYMBOLS),
    ):
        missing.extend(
            f"{exchange}:{symbol}"
            for symbol in symbols
            if (exchange, symbol) not in found
        )

    found_by_exchange = {
        exchange: sum(1 for row in rows if row["exchange"] == exchange)
        for exchange in KITE_TEST_EXCHANGES
    }
    expected = sum(expected_by_exchange.values())

    return {
        "expected": expected,
        "expected_by_exchange": expected_by_exchange,
        "found": len(rows),
        "found_by_exchange": found_by_exchange,
        "missing": missing,
        "complete": not missing and len(rows) == expected,
    }
