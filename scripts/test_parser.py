from app.services.truedata_parser import parse_trade


message = {
    "trade": [
        "100000011",
        "2026-08-19T14:34:24",
        "527.5",
        "34",
        "525.73",
        "1215204",
        "532.7",
        "535.35",
        "520.25",
        "530.1",
        "0",
        "0",
        "638869198.92",
        "",
        "2116",
        "527.5",
        "6972",
        "527.75",
        "70",
    ]
}


result = parse_trade(message)

print("Symbol ID:", result["symbol_id"])
print("Timestamp:", result["timestamp"])
print("Number of raw fields:", len(result["raw_values"]))
print("Raw values:", result["raw_values"])
