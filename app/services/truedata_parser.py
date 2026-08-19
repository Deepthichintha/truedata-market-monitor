from datetime import datetime
from typing import Any


def _to_float(value: Any) -> float | None:
    """Convert a value to float, returning None for empty values."""
    if value in (None, ""):
        return None

    return float(value)


def _to_int(value: Any) -> int | None:
    """Convert a value to int, returning None for empty values."""
    if value in (None, ""):
        return None

    return int(float(value))


def parse_trade(data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse a TrueData trade message.

    TrueData trade format:

    0  - Symbol ID
    1  - Timestamp
    2  - LTP
    3  - LTQ
    4  - ATP
    5  - Total Volume
    6  - Open
    7  - High
    8  - Low
    9  - Previous Close
    10 - OI
    11 - Previous OI
    12 - Turnover
    13 - Reserved / empty
    14 - Bid
    15 - Bid Quantity
    16 - Ask
    17 - Ask Quantity
    18 - Additional field

    The complete raw values are also preserved.
    """

    values = data.get("trade")

    if not isinstance(values, list):
        raise ValueError("Invalid TrueData trade message: 'trade' field missing")

    if len(values) != 19:
        raise ValueError(
            f"Unexpected TrueData trade length: {len(values)}; expected 19"
        )

    try:
        return {
            "symbol_id": str(values[0]),
            "timestamp": datetime.fromisoformat(str(values[1])),

            "ltp": _to_float(values[2]),
            "ltq": _to_int(values[3]),
            "atp": _to_float(values[4]),
            "total_volume": _to_int(values[5]),

            "open": _to_float(values[6]),
            "high": _to_float(values[7]),
            "low": _to_float(values[8]),
            "prev_close": _to_float(values[9]),

            "oi": _to_int(values[10]),
            "prev_oi": _to_int(values[11]),
            "turnover": _to_float(values[12]),

            "bid": _to_float(values[14]),
            "bid_qty": _to_int(values[15]),
            "ask": _to_float(values[16]),
            "ask_qty": _to_int(values[17]),

            # Preserve the complete original TrueData message.
            "raw_values": values,
        }

    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Failed to parse TrueData trade values: {values}"
        ) from exc
