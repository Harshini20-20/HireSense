
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.services.candidate_evaluation import (
    evaluate_job_candidates,
)


router = APIRouter(
    prefix="/api/matching",
    tags=["Candidate Matching"],
)


@router.post("/{job_id}/evaluate")
def evaluate_candidates(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Evaluate and rank all uploaded candidates against a job.
    """

    try:
        return evaluate_job_candidates(db, job_id)

    except ValueError as exc:
        if str(exc) == "Job not found.":
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Candidate evaluation failed.",
        ) from exc
