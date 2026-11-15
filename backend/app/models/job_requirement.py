from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE")
    )
    requirement: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))
    importance: Mapped[str] = mapped_column(
        String(20), default="preferred"
    )

    job = relationship("Job", back_populates="requirements")