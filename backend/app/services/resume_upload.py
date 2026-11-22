
import logging
import os
import sqlite3
import tempfile
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.candidate import Candidate
from backend.app.models.resume import Resume
from backend.app.models.candidate_skill import CandidateSkill
from backend.app.models.job_candidate import JobCandidate
from backend.app.models.job import Job

from backend.app.services.resume_parser import (
    extract_resume_text,
    ResumeParsingError,
)

from backend.app.services.candidate_extractor import (
    extract_candidate_information,
)
from backend.app.services.resume_storage import (
    ResumeStorageError,
    configured_storage_reference,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = Path(os.getenv(
    "HIRESENSE_RESUME_STORAGE",
    str(BASE_DIR / "storage" / "resumes"),
))

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class ResumeUploadError(Exception):
    """Raised when resume upload processing fails."""


def _safe_sqlite_diagnostic(exc: Exception) -> tuple[int | str, str, str] | None:
    """Return safe SQLite metadata without exposing its raw error text."""
    original = getattr(exc, "orig", None)
    if not isinstance(original, sqlite3.Error):
        return None

    code = getattr(original, "sqlite_errorcode", "unavailable")
    name = getattr(original, "sqlite_errorname", "unavailable")
    if not isinstance(name, str) or not name.startswith("SQLITE_") or not all(
        character.isupper() or character.isdigit() or character == "_"
        for character in name
    ):
        name = "unavailable"

    message = str(original).casefold()
    primary_code = code & 0xFF if isinstance(code, int) else None
    if (
        primary_code in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}
        or "locked" in message
        or "database is busy" in message
    ):
        category = "database locked/busy"
    elif primary_code == sqlite3.SQLITE_READONLY or "readonly" in message or "read-only" in message:
        category = "database readonly"
    elif "no such table" in message:
        category = "missing table"
    elif "no such column" in message or "no column named" in message:
        category = "missing column"
    else:
        category = "other SQLite operational error"

    return code, name, category


async def process_resume_upload(
    upload_file: UploadFile,
    db: Session,
    job_id: int | None = None,
) -> dict:

    if job_id is not None and db.get(Job, job_id) is None:
        raise ResumeUploadError("Selected job was not found.")

    original_name = Path(upload_file.filename or "").name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ResumeUploadError(
            "Only PDF and DOCX files are supported."
        )

    content = await upload_file.read()

    if not content:
        raise ResumeUploadError("Uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise ResumeUploadError(
            "File exceeds the maximum size of 10 MB."
        )

    # Basic file-signature validation
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise ResumeUploadError("Invalid PDF file.")

    if extension == ".docx" and not content.startswith(b"PK"):
        raise ResumeUploadError("Invalid DOCX file.")

    temporary_path = None
    storage = None
    storage_key = None
    storage_reference = None
    upload_attempted = False
    stage = "temporary file preparation"
    try:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)

        stage = f"{extension[1:].upper()} parsing"
        extracted_text = extract_resume_text(temporary_path)

        stage = "candidate data extraction"
        candidate_data = extract_candidate_information(
            extracted_text
        )

        stage = "candidate profile lookup and persistence"
        email = candidate_data["email"]

        candidate = None

        # Reuse an existing candidate when a usable email is found.
        if email:
            candidate = db.scalar(
                select(Candidate).where(
                    Candidate.email == email
                )
            )

        if candidate is None:
            candidate = Candidate(
                name=candidate_data["name"],
                email=email,
                phone=candidate_data["phone"],
            )
            db.add(candidate)
            db.flush()

        else:
            # Fill missing profile details without overwriting
            # information already stored.
            if not candidate.name:
                candidate.name = candidate_data["name"]

            if not candidate.phone:
                candidate.phone = candidate_data["phone"]

        stage = "resume storage configuration and key check"
        stored_name = f"{uuid.uuid4().hex}{extension}"
        storage, storage_key, storage_reference = configured_storage_reference(stored_name)
        stage = f"{storage.name} storage object existence check"
        if storage.exists(storage_key):
            raise ResumeUploadError("Could not allocate a unique resume storage key.")

        content_type = (
            "application/pdf" if extension == ".pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        upload_attempted = True
        stage = (
            "Supabase Storage upload" if storage.name == "supabase"
            else "local filesystem upload"
        )
        storage.upload(storage_key, content, content_type)

        stage = "resume, job association, and skills database persistence"
        resume = Resume(
            candidate_id=candidate.id,
            file_name=original_name,
            file_path=storage_reference,
            extracted_text=extracted_text,
        )

        db.add(resume)
        db.flush()

        # Explicitly uploaded resumes are associated with the selected job.
        if job_id is not None:
            link = db.scalar(
                select(JobCandidate).where(
                    JobCandidate.job_id == job_id,
                    JobCandidate.candidate_id == candidate.id,
                )
            )
            if link is None:
                db.add(JobCandidate(
                    job_id=job_id,
                    candidate_id=candidate.id,
                    source="APPLIED",
                    status="APPLIED",
                ))
            else:
                link.source = "APPLIED"
                link.status = "APPLIED"

        existing_skills = {
            skill.normalized_skill
            for skill in candidate.skills
        }

        for skill_name in candidate_data["skills"]:
            normalized = skill_name.casefold()

            if normalized not in existing_skills:
                db.add(
                    CandidateSkill(
                        candidate_id=candidate.id,
                        skill_name=skill_name,
                        normalized_skill=normalized,
                        category="technical",
                    )
                )

        db.flush()

        return {
            "candidate_id": candidate.id,
            "resume_id": resume.id,
            "file_name": original_name,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "skills": candidate_data["skills"],
            "education": candidate_data["education"],
            "experience_years": candidate_data["experience_years"],
            "message": "Resume uploaded and processed successfully.",
            "_storage_backend": storage,
            "_storage_key": storage_key,
        }

    except Exception as exc:
        if not isinstance(exc, ResumeUploadError):
            # Preserve the original traceback frames and exception type while
            # suppressing exception text, which can contain SQL parameters or
            # parser input derived from candidate data.
            sqlite_diagnostic = _safe_sqlite_diagnostic(exc)
            if sqlite_diagnostic is None:
                sqlite_code, sqlite_name, sqlite_category = "n/a", "n/a", "n/a"
            else:
                sqlite_code, sqlite_name, sqlite_category = sqlite_diagnostic

            safe_exception = RuntimeError("Original exception details redacted.")
            logger.exception(
                "Resume processing failed at stage=%s format=%s backend=%s "
                "error_type=%s sqlite_error_code=%s sqlite_error_name=%s "
                "sqlite_error_category=%s",
                stage,
                extension[1:].upper(),
                storage.name if storage is not None else "not selected",
                type(exc).__name__,
                sqlite_code,
                sqlite_name,
                sqlite_category,
                exc_info=(RuntimeError, safe_exception, exc.__traceback__),
            )

        db.rollback()

        if upload_attempted and storage is not None and storage_key is not None:
            try:
                storage.delete(storage_key)
            except ResumeStorageError:
                # A request can fail after the provider accepted the upload.
                # Keep this generic so storage credentials and paths stay private.
                logger.error("Unable to remove resume object after upload processing failed.")

        if isinstance(exc, ResumeUploadError):
            raise

        if isinstance(exc, ResumeParsingError):
            raise ResumeUploadError(str(exc)) from exc

        if isinstance(exc, ResumeStorageError):
            raise ResumeUploadError(str(exc)) from exc

        raise ResumeUploadError(
            "Resume processing failed."
        ) from exc

    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Unable to remove a temporary resume parsing file.")
        await upload_file.close()
