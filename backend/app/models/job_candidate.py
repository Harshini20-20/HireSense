from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base


class JobCandidate(Base):
    """Associates one candidate profile with a job without duplicating either."""

    __tablename__ = "job_candidates"
    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate_link"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(30), default="APPLIED", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="NEW", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
