
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.services.resume_upload import (
    ResumeUploadError,
    process_resume_upload,
)

router = APIRouter(
    prefix="/api/resumes",
    tags=["Resumes"],
)


@router.post("/upload")
async def upload_resumes(
    files: Annotated[list[UploadFile], File(description="Upload PDF or DOCX resumes")],
    job_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
):
    results = []

    for upload_file in files:
        file_name = upload_file.filename or "unknown"

        try:
            result = await process_resume_upload(upload_file, db, job_id=job_id)
            db.commit()

            results.append({
                "status": "success",
                **result,
            })

        except ResumeUploadError as exc:
            db.rollback()

            results.append({
                "status": "failed",
                "file_name": file_name,
                "error": str(exc),
            })

        except Exception:
            db.rollback()

            results.append({
                "status": "failed",
                "file_name": file_name,
                "error": "An unexpected error occurred while processing this resume.",
            })

    successful = sum(
        item["status"] == "success" for item in results
    )

    return {
        "job_id": job_id,
        "total_files": len(files),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results,
    }