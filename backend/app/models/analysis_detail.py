from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class AnalysisDetail(Base):
    __tablename__ = "analysis_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        unique=True
    )

    semantic_score: Mapped[float]
    skill_score: Mapped[float]
    experience_score: Mapped[float]
    education_score: Mapped[float]
    project_score: Mapped[float]

    matched_skills: Mapped[dict] = mapped_column(JSON)
    missing_skills: Mapped[dict] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)

    analysis = relationship("Analysis", back_populates="details")