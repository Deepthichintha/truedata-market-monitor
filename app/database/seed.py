from app.config.bse_symbols import BSE_SYMBOLS
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

        added_nse = 0
        added_bse = 0

        # -------------------------------------------------
        # NSE symbols
        # -------------------------------------------------

        for symbol in SYMBOLS:
            if symbol not in existing_symbols:
                db.add(
                    Symbol(
                        symbol=symbol,
                        exchange="NSE",
                        is_active=True,
                    )
                )
                added_nse += 1

        # -------------------------------------------------
        # BSE symbols
        # -------------------------------------------------

        for symbol, truedata_symbol_id in BSE_SYMBOLS.items():
            if symbol not in existing_symbols:
                db.add(
                    Symbol(
                        symbol=symbol,
                        truedata_symbol_id=truedata_symbol_id,
                        exchange="BSE",
                        is_active=True,
                    )
                )
                added_bse += 1

        db.commit()

        total_symbols = (
            db.query(Symbol)
            .filter(Symbol.is_active.is_(True))
            .count()
        )

        print("=" * 60)
        print("Symbol Seeding Complete")
        print("=" * 60)
        print(f"NSE symbols added: {added_nse}")
        print(f"BSE symbols added: {added_bse}")
        print(f"Total active symbols: {total_symbols}")
        print("=" * 60)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_symbols()
