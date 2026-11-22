
from pathlib import Path
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

# Store the database inside the backend directory
BASE_DIR = Path(__file__).resolve().parents[2]

configured_database_url = os.getenv("DATABASE_URL", "").strip()
if configured_database_url:
    DATABASE_URL = make_url(configured_database_url)
    if DATABASE_URL.drivername in {
        "postgres",
        "postgresql",
        "postgresql+psycopg",
        "postgresql+psycopg2",
    }:
        DATABASE_URL = DATABASE_URL.set(drivername="postgresql+psycopg")
        if "sslmode" not in DATABASE_URL.query:
            DATABASE_URL = DATABASE_URL.update_query_dict({"sslmode": "require"})
else:
    DATABASE_URL = make_url(
        f"sqlite:///{(BASE_DIR / 'hiresense.db').as_posix()}"
    )

# SQLite needs a thread-specific connection argument; psycopg does not.
engine_options = {}
if DATABASE_URL.get_backend_name() == "sqlite":
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)

# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Dependency for database sessions
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
