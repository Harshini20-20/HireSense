from backend.app.database.base import Base
from backend.app.database.connection import engine
from backend.app import models


def initialize_database():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
    print("HireSense database initialized successfully!")