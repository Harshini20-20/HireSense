"""Additive SQLite migration for job-specific candidate associations.

Run from the project root:
    python -m backend.app.database.migrate_job_candidates

This creates only the new association table. Existing candidates, resumes,
analyses, and files are not updated or deleted.
"""
from backend.app.database.connection import engine
from backend.app.database.base import Base
from backend.app import models  # noqa: F401


def migrate():
    Base.metadata.create_all(bind=engine, tables=[models.JobCandidate.__table__])


if __name__ == "__main__":
    migrate()
    print("HireSense job-candidate association table is ready.")
