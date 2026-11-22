import logging
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.resume import Resume
from backend.app.services.resume_storage import (
    ResumeStorageError,
    storage_for_reference,
)


logger = logging.getLogger(__name__)


class DeletionError(Exception):
    """Raised when a deletion cannot safely complete."""


def _storage_identity(reference: str):
    try:
        return storage_for_reference(reference)
    except ResumeStorageError as exc:
        raise DeletionError(
            "A resume storage reference is invalid; deletion was cancelled."
        ) from exc


def _remaining_resume_references(db: Session, deleting_resume_ids: set[int]) -> set[str]:
    remaining_references = set()
    rows = db.execute(select(Resume.id, Resume.file_path)).all()
    for resume_id, file_path in rows:
        if resume_id in deleting_resume_ids:
            continue
        try:
            _, _, canonical = _storage_identity(file_path)
            remaining_references.add(canonical)
        except DeletionError:
            # An unrelated legacy path must not prevent deletion of this profile.
            continue
    return remaining_references


def delete_database_rows_and_files(
    db: Session,
    resume_rows: list[Resume],
    delete_rows: Callable[[], None],
) -> None:
    """Delete database rows and unreferenced storage objects with compensation."""
    deleting_ids = {resume.id for resume in resume_rows}
    remaining_references = _remaining_resume_references(db, deleting_ids)
    objects_to_delete = {}
    for resume in resume_rows:
        storage, key, canonical = _storage_identity(resume.file_path)
        if canonical not in remaining_references:
            objects_to_delete[canonical] = (storage, key)

    backups = {}
    attempted_deletes = []
    try:
        for canonical, (storage, key) in objects_to_delete.items():
            if storage.exists(key):
                backups[canonical] = (storage, key, storage.retrieve(key))

        delete_rows()
        db.flush()

        for canonical, (storage, key, _) in backups.items():
            # Include the current item before calling delete because a remote
            # timeout may occur after the provider has accepted the request.
            attempted_deletes.append(canonical)
            storage.delete(key)

        db.commit()
    except Exception as exc:
        db.rollback()
        restoration_errors = []
        for canonical in attempted_deletes:
            storage, key, contents = backups[canonical]
            extension = ".pdf" if key.lower().endswith(".pdf") else ".docx"
            content_type = (
                "application/pdf" if extension == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            try:
                storage.upload(key, contents, content_type, upsert=True)
            except ResumeStorageError:
                restoration_errors.append(canonical)
        if restoration_errors:
            logger.critical(
                "Resume deletion rollback could not restore %s storage object(s).",
                len(restoration_errors),
            )
            raise DeletionError(
                "Deletion failed and storage restoration needs administrator attention."
            ) from exc
        if isinstance(exc, DeletionError):
            raise
        if isinstance(exc, ResumeStorageError):
            raise DeletionError("Resume storage could not complete the deletion.") from exc
        raise DeletionError("Deletion failed; database changes were rolled back.") from exc
