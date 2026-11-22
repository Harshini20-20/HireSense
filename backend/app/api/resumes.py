
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.services.resume_upload import (
    ResumeUploadError,
    process_resume_upload,
)
from backend.app.services.resume_storage import ResumeStorageError

logger = logging.getLogger(__name__)

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
        storage = None
        storage_key = None

        try:
            result = await process_resume_upload(upload_file, db, job_id=job_id)
            storage = result.pop("_storage_backend")
            storage_key = result.pop("_storage_key")
            db.commit()
            storage = None
            storage_key = None

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

            # The file is stored before the database commit. If commit failed,
            # compensate so the object does not become orphaned.
            if storage is not None and storage_key is not None:
                try:
                    storage.delete(storage_key)
                except ResumeStorageError:
                    logger.error("Unable to remove resume object after database commit failure.")

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
