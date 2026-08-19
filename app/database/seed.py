from app.config.symbols import SYMBOLS
from app.database.connection import SessionLocal
from app.database.models import Symbol


def seed_symbols():
    db = SessionLocal()

    try:
        existing_symbols = {
            row.symbol
            for row in db.query(Symbol).all()
        }

        added = 0

        for symbol in SYMBOLS:
            if symbol not in existing_symbols:
                db.add(
                    Symbol(
                        symbol=symbol,
                        exchange="NSE",
                        is_active=True,
                    )
                )
                added += 1

        db.commit()

        print(f"Symbols added: {added}")
        print(f"Total configured symbols: {len(SYMBOLS)}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_symbols()
