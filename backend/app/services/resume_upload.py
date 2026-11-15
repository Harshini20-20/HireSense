
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.candidate import Candidate
from backend.app.models.resume import Resume
from backend.app.models.candidate_skill import CandidateSkill

from backend.app.services.resume_parser import (
    extract_resume_text,
    ResumeParsingError,
)

from backend.app.services.candidate_extractor import (
    extract_candidate_information,
)


BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage" / "resumes"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class ResumeUploadError(Exception):
    """Raised when resume upload processing fails."""


async def process_resume_upload(
    upload_file: UploadFile,
    db: Session,
) -> dict:

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

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

    stored_name = f"{uuid.uuid4().hex}{extension}"
    file_path = STORAGE_DIR / stored_name

    try:
        file_path.write_bytes(content)

        extracted_text = extract_resume_text(file_path)

        candidate_data = extract_candidate_information(
            extracted_text
        )

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

        resume = Resume(
            candidate_id=candidate.id,
            file_name=original_name,
            file_path=str(file_path.resolve()),
            extracted_text=extracted_text,
        )

        db.add(resume)

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
        }

    except Exception as exc:
        file_path.unlink(missing_ok=True)
        db.rollback()

        if isinstance(exc, ResumeUploadError):
            raise

        if isinstance(exc, ResumeParsingError):
            raise ResumeUploadError(str(exc)) from exc

        raise ResumeUploadError(
            f"Resume processing failed: {exc}"
        ) from exc

    finally:
        await upload_file.close()
