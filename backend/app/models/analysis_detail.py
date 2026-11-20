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

    semantic_score: Mapped[float | None] = mapped_column(nullable=True)
    skill_score: Mapped[float | None] = mapped_column(nullable=True)
    experience_score: Mapped[float | None] = mapped_column(nullable=True)
    education_score: Mapped[float | None] = mapped_column(nullable=True)
    project_score: Mapped[float | None] = mapped_column(nullable=True)

    matched_skills: Mapped[dict] = mapped_column(JSON)
    missing_skills: Mapped[dict] = mapped_column(JSON)

    effective_weights: Mapped[dict] = mapped_column(
        JSON,
        default=dict
    )

    unavailable_components: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    explanation: Mapped[str] = mapped_column(Text)

    analysis = relationship("Analysis", back_populates="details")