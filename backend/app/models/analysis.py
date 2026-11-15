from datetime import datetime

from sqlalchemy import (
    DateTime, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Analysis(Base):
    __tablename__ = "analyses"

    __table_args__ = (
        UniqueConstraint(
            "job_id", "candidate_id",
            name="uq_job_candidate"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id")
    )
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    overall_score: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    job = relationship("Job", back_populates="analyses")
    candidate = relationship("Candidate", back_populates="analyses")
    resume = relationship("Resume", back_populates="analyses")
    details = relationship(
        "AnalysisDetail",
        back_populates="analysis",
        cascade="all, delete-orphan",
        uselist=False
    )