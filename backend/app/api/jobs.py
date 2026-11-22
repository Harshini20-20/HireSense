from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.job import Job
from backend.app.models.analysis import Analysis
from backend.app.models.analysis_detail import AnalysisDetail
from backend.app.models.job_candidate import JobCandidate
from backend.app.models.job_requirement import JobRequirement
from backend.app.schemas.job import JobCreate, JobResponse


router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"]
)


@router.get("/", response_model=list[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.id.desc()).all()


@router.post("/", response_model=JobResponse, status_code=201)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
):
    new_job = Job(
        title=job_data.title,
        description=job_data.description
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return job


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    analysis_ids = select(Analysis.id).where(Analysis.job_id == job_id)
    try:
        db.execute(delete(AnalysisDetail).where(AnalysisDetail.analysis_id.in_(analysis_ids)))
        db.execute(delete(Analysis).where(Analysis.job_id == job_id))
        db.execute(delete(JobCandidate).where(JobCandidate.job_id == job_id))
        db.execute(delete(JobRequirement).where(JobRequirement.job_id == job_id))
        db.execute(delete(Job).where(Job.id == job_id))
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Job could not be deleted; no database changes were committed.",
        ) from exc

    return {"message": "Job deleted successfully.", "job_id": job_id}
