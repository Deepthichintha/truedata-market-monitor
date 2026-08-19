import json

from sqlalchemy import select

from app.database.connection import SessionLocal
from app.database.models import Symbol


MAPPING_FILE = "data/truedata_symbols.json"


def populate_mapping() -> None:
    with open(MAPPING_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    symbol_list = data.get("symbollist", [])

    if not symbol_list:
        raise RuntimeError("No symbol mapping found in TrueData response.")

    print(f"TrueData mappings found: {len(symbol_list)}")

    db = SessionLocal()

    try:
        updated = 0

        for item in symbol_list:
            if not isinstance(item, list) or len(item) < 2:
                print(f"Skipping invalid mapping: {item}")
                continue

            symbol_name = item[0]
            truedata_symbol_id = item[1]

            symbol = db.scalar(
                select(Symbol).where(
                    Symbol.symbol == symbol_name
                )
            )

            if symbol is None:
                print(
                    f"WARNING: {symbol_name} "
                    f"does not exist in symbols table"
                )
                continue

            symbol.truedata_symbol_id = str(
                truedata_symbol_id
            )

            updated += 1

        db.commit()

        print(f"Successfully updated: {updated} symbols")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    populate_mapping()

