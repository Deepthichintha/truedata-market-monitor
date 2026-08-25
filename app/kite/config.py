"""Kite Connect configuration for the isolated provider evaluation."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

KITE_API_KEY = os.getenv("KITE_API_KEY", "")
KITE_API_SECRET = os.getenv("KITE_API_SECRET", "")
KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN", "")
KITE_REDIRECT_URL = os.getenv(
    "KITE_REDIRECT_URL",
    "http://127.0.0.1:8000/api/kite-test/callback",
)
KITE_LOGIN_URL = "https://kite.zerodha.com/connect/login?v=3"
KITE_WS_URL = "wss://ws.kite.trade"

KITE_INSTRUMENTS_FILE = Path(
    os.getenv("KITE_INSTRUMENTS_FILE", "data/kite_instruments.csv")
)
KITE_TEST_RUNS_FILE = Path(
    os.getenv("KITE_TEST_RUNS_FILE", "data/kite_test_ticks.jsonl")
)

# Keep the first evaluation small and identical to the existing TrueData test
# universe. The collector can be expanded after the provider comparison is
# validated.
KITE_TEST_SYMBOLS = [
    "AARTIIND",
    "ADANIPORTS",
    "AETHER",
    "APOLLOHOSP",
    "ASHIANA",
    "ATUL",
    "AUBANK",
    "BAJAJ-AUTO",
    "CARERATING",
    "CCL",
]

KITE_TEST_EXCHANGES = ("NSE", "BSE")
KITE_MAX_INSTRUMENTS_PER_CONNECTION = 3000
