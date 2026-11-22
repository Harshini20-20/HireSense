
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


@router.post("/{job_id}/candidates/{candidate_id}/add")
def add_recommended_candidate(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
):
    """Move an AI-discovered candidate into the selected job's recruiter workflow."""
    from sqlalchemy import select
    from backend.app.models.job import Job
    from backend.app.models.candidate import Candidate
    from backend.app.models.job_candidate import JobCandidate

    if db.get(Job, job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if db.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    link = db.scalar(select(JobCandidate).where(
        JobCandidate.job_id == job_id,
        JobCandidate.candidate_id == candidate_id,
    ))
    if link is None:
        link = JobCandidate(
            job_id=job_id,
            candidate_id=candidate_id,
            source="RECRUITER_ADDED",
            status="NEW",
        )
        db.add(link)
    else:
        link.source = "RECRUITER_ADDED"
        link.status = "NEW"

    db.commit()
    return {
        "message": "Candidate added to this job's workflow.",
        "job_id": job_id,
        "candidate_id": candidate_id,
        "source": link.source,
        "status": link.status,
    }
