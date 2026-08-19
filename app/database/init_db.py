from app.database.connection import Base, engine
from app.database.models import Symbol


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")
