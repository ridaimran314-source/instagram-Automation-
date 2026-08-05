"""Reel job persistence model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import JobStatus


class ReelJob(Base):
    """Tracks each attempt to generate and publish a reel."""

    __tablename__ = "reel_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scholarship_id: Mapped[int] = mapped_column(ForeignKey("scholarships.id"), index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    scholarship = relationship("Scholarship")
