from sqlalchemy import inspect

from backend.app.database.connection import engine
from backend.app.database.init_db import initialize_database


def test_all_tables_created():
    initialize_database()

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected_tables = {
        "jobs",
        "job_requirements",
        "candidates",
        "resumes",
        "analyses",
        "analysis_details",
        "candidate_skills",
    }

    assert expected_tables.issubset(tables)