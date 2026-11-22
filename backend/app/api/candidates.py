from datetime import datetime
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from backend.app.database.connection import get_db
from backend.app.models.analysis import Analysis
from backend.app.models.analysis_detail import AnalysisDetail
from backend.app.models.candidate import Candidate
from backend.app.models.candidate_skill import CandidateSkill
from backend.app.models.job_candidate import JobCandidate
from backend.app.models.resume import Resume
from backend.app.services.deletion import (
    DeletionError,
    delete_database_rows_and_files,
)
from backend.app.services.resume_upload import STORAGE_DIR


router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


def _resolve_resume_file(stored_path: str) -> Path:
    storage_root = STORAGE_DIR.resolve()
    raw_path = str(stored_path)
    requested_path = Path(raw_path)

    if requested_path.is_absolute() and requested_path.resolve(strict=False).is_relative_to(storage_root):
        resolved = requested_path.resolve(strict=False)
    else:
        path_parts = [part for part in raw_path.replace("\\", "/").split("/") if part]
        if len(path_parts) < 3 or [part.casefold() for part in path_parts[-3:-1]] != ["storage", "resumes"]:
            raise HTTPException(status_code=404, detail="Resume file is unavailable.")
        resolved = (storage_root / path_parts[-1]).resolve(strict=False)

    if not resolved.is_relative_to(storage_root) or not resolved.is_file():
        raise HTTPException(status_code=404, detail="Resume file is unavailable.")
    return resolved


def _safe_download_filename(file_name: str, resume_id: int, extension: str) -> str:
    name = str(file_name).replace("\\", "/").split("/")[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip().strip(".")
    if not name or Path(name).suffix.lower() != extension:
        name = f"resume-{resume_id}{extension}"
    return name


@router.get("/")
def list_candidates(db: Session = Depends(get_db)):
    candidates = db.scalars(
        select(Candidate)
        .options(selectinload(Candidate.resumes))
        .order_by(Candidate.name, Candidate.id)
    ).all()

    return [
        {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "resumes": [
                {
                    "id": resume.id,
                    "file_name": resume.file_name,
                    "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
                }
                for resume in sorted(
                    candidate.resumes,
                    key=lambda item: (item.uploaded_at or datetime.min, item.id),
                    reverse=True,
                )
            ],
        }
        for candidate in candidates
    ]


@router.get("/{candidate_id}/resumes/{resume_id}/file")
def view_candidate_resume(
    candidate_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
):
    if db.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    resume = db.scalar(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.candidate_id == candidate_id,
        )
    )
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found for this candidate.")

    file_path = _resolve_resume_file(resume.file_path)
    extension = file_path.suffix.lower()
    if extension == ".pdf":
        media_type = "application/pdf"
        disposition = "inline"
    elif extension == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        disposition = "attachment"
    else:
        raise HTTPException(status_code=415, detail="This resume file type cannot be served.")

    download_name = _safe_download_filename(resume.file_name, resume.id, extension)
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=download_name,
        content_disposition_type=disposition,
        headers={"Cache-Control": "private, no-store"},
    )


@router.delete("/{candidate_id}/resumes/{resume_id}")
def delete_candidate_resume(
    candidate_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    resume = db.get(Resume, resume_id)
    if resume is None or resume.candidate_id != candidate_id:
        raise HTTPException(status_code=404, detail="Resume not found for this candidate.")

    analysis_ids = select(Analysis.id).where(Analysis.resume_id == resume_id)

    def delete_rows():
        db.execute(delete(AnalysisDetail).where(AnalysisDetail.analysis_id.in_(analysis_ids)))
        db.execute(delete(Analysis).where(Analysis.resume_id == resume_id))
        db.execute(delete(Resume).where(Resume.id == resume_id))

    try:
        delete_database_rows_and_files(db, [resume], delete_rows)
    except DeletionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "message": "Resume removed successfully.",
        "candidate_id": candidate_id,
        "resume_id": resume_id,
    }


@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    resumes = db.scalars(
        select(Resume).where(Resume.candidate_id == candidate_id)
    ).all()
    analysis_ids = select(Analysis.id).where(Analysis.candidate_id == candidate_id)

    def delete_rows():
        db.execute(delete(AnalysisDetail).where(AnalysisDetail.analysis_id.in_(analysis_ids)))
        db.execute(delete(Analysis).where(Analysis.candidate_id == candidate_id))
        db.execute(delete(JobCandidate).where(JobCandidate.candidate_id == candidate_id))
        db.execute(delete(CandidateSkill).where(CandidateSkill.candidate_id == candidate_id))
        db.execute(delete(Resume).where(Resume.candidate_id == candidate_id))
        db.execute(delete(Candidate).where(Candidate.id == candidate_id))

    try:
        delete_database_rows_and_files(db, resumes, delete_rows)
    except DeletionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"message": "Candidate deleted successfully.", "candidate_id": candidate_id}

