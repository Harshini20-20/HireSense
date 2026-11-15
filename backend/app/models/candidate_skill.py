from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "normalized_skill",
            name="uq_candidate_skill"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE")
    )
    skill_name: Mapped[str] = mapped_column(String(100))
    normalized_skill: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))

    candidate = relationship("Candidate", back_populates="skills")