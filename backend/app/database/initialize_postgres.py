"""Create missing HireSense tables in an explicitly configured PostgreSQL database.

Run from the project root after configuring DATABASE_URL:
    docker compose run --rm backend python -m backend.app.database.initialize_postgres

This command is never run by FastAPI startup. SQLAlchemy create_all only creates
missing tables; it does not drop or truncate existing tables or records.
"""
import os
import sys

from sqlalchemy.engine import make_url


SUPPORTED_POSTGRES_DRIVERS = {
    "postgres",
    "postgresql",
    "postgresql+psycopg",
    "postgresql+psycopg2",
}


def initialize_postgres_schema() -> int:
    raw_database_url = os.getenv("DATABASE_URL", "").strip()
    if not raw_database_url:
        print(
            "ERROR: DATABASE_URL is required. No database connection was attempted.",
            file=sys.stderr,
        )
        return 2

    try:
        configured_url = make_url(raw_database_url)
    except Exception as exc:
        print(
            f"ERROR: DATABASE_URL could not be parsed ({type(exc).__name__}).",
            file=sys.stderr,
        )
        return 2

    if configured_url.drivername not in SUPPORTED_POSTGRES_DRIVERS:
        print(
            "ERROR: PostgreSQL schema initialization only accepts a PostgreSQL "
            "DATABASE_URL. No database connection was attempted.",
            file=sys.stderr,
        )
        return 2

    engine = None
    try:
        from backend.app.database.connection import engine as configured_engine
        from backend.app.database.base import Base
        import backend.app.models  # noqa: F401 - register all model tables

        engine = configured_engine
        if engine.dialect.name != "postgresql":
            print(
                "ERROR: The configured SQLAlchemy engine is not PostgreSQL. "
                "No schema changes were made.",
                file=sys.stderr,
            )
            return 2

        Base.metadata.create_all(bind=engine, checkfirst=True)
        print(
            "HireSense PostgreSQL schema is ready. "
            f"Verified {len(Base.metadata.tables)} model tables."
        )
        return 0
    except Exception as exc:
        print(
            "ERROR: PostgreSQL schema initialization failed "
            f"({type(exc).__name__}). Check DATABASE_URL, network access, SSL, "
            "and schema privileges. Connection details were not printed.",
            file=sys.stderr,
        )
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(initialize_postgres_schema())
