
from sqlalchemy import text

from backend.app.database.connection import engine, SessionLocal


def test_database_connection():
    assert engine.dialect.name == "sqlite"

    with SessionLocal() as db:
        result = db.execute(text("SELECT 1"))

        assert result.scalar() == 1
