import logging
import shutil
import tempfile
from pathlib import Path
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.resume import Resume
from backend.app.services.resume_upload import STORAGE_DIR


logger = logging.getLogger(__name__)


class DeletionError(Exception):
    """Raised when a deletion cannot safely complete."""


def _managed_resume_path(stored_path: str) -> Path:
    storage_root = STORAGE_DIR.resolve()
    raw_path = str(stored_path)
    candidate = Path(raw_path)

    # Windows absolute paths can remain in the database when the same data
    # directory is later mounted into the Linux Docker container.
    if candidate.is_absolute() and candidate.resolve(strict=False).is_relative_to(storage_root):
        resolved = candidate.resolve(strict=False)
    else:
        normalized_parts = [part for part in raw_path.replace("\\", "/").split("/") if part]
        lower_parts = [part.casefold() for part in normalized_parts]
        if len(normalized_parts) < 3 or lower_parts[-3:-1] != ["storage", "resumes"]:
            raise DeletionError(
                "The resume file path is outside managed resume storage; deletion was cancelled."
            )
        resolved = (storage_root / normalized_parts[-1]).resolve(strict=False)

    if not resolved.is_relative_to(storage_root):
        raise DeletionError(
            "The resume file path is outside managed resume storage; deletion was cancelled."
        )
    if resolved.exists() and not resolved.is_file():
        raise DeletionError("The resume path does not point to a regular file.")
    return resolved


def _remaining_resume_paths(db: Session, deleting_resume_ids: set[int]) -> set[Path]:
    remaining_paths = set()
    rows = db.execute(select(Resume.id, Resume.file_path)).all()
    for resume_id, file_path in rows:
        if resume_id in deleting_resume_ids:
            continue
        try:
            remaining_paths.add(_managed_resume_path(file_path))
        except DeletionError:
            # An unrelated legacy path must not prevent deletion of this profile.
            continue
    return remaining_paths


def delete_database_rows_and_files(
    db: Session,
    resume_rows: list[Resume],
    delete_rows: Callable[[], None],
) -> None:
    """Delete database rows and now-unreferenced files with rollback recovery."""
    deleting_ids = {resume.id for resume in resume_rows}
    remaining_paths = _remaining_resume_paths(db, deleting_ids)
    file_paths = {
        _managed_resume_path(resume.file_path)
        for resume in resume_rows
    } - remaining_paths
    existing_paths = [path for path in file_paths if path.exists()]

    backup_dir = None
    removed_paths: list[Path] = []
    try:
        if existing_paths:
            backup_dir = Path(tempfile.mkdtemp(prefix="hiresense-delete-"))
            for index, path in enumerate(existing_paths):
                shutil.copy2(path, backup_dir / str(index))

        delete_rows()
        db.flush()

        for path in existing_paths:
            path.unlink()
            removed_paths.append(path)

        db.commit()
    except Exception as exc:
        db.rollback()
        restoration_errors = []
        if backup_dir is not None:
            for index, path in enumerate(existing_paths):
                if path in removed_paths:
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_dir / str(index), path)
                    except OSError as restore_exc:
                        restoration_errors.append(str(restore_exc))
        if backup_dir is not None and not restoration_errors:
            shutil.rmtree(backup_dir, ignore_errors=True)
        if restoration_errors:
            logger.critical(
                "Resume deletion rollback could not restore files: %s",
                "; ".join(restoration_errors),
            )
            raise DeletionError(
                "Deletion failed and file restoration needs administrator attention."
            ) from exc
        if isinstance(exc, DeletionError):
            raise
        raise DeletionError("Deletion failed; database changes were rolled back.") from exc
    else:
        if backup_dir is not None:
            try:
                shutil.rmtree(backup_dir)
            except OSError:
                logger.exception("Could not remove temporary resume deletion backup %s", backup_dir)
