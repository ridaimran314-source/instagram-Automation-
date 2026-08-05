"""Instagram publication persistence model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Publication(Base):
    """Stores Instagram publishing identifiers and result URLs."""

    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scholarship_id: Mapped[int] = mapped_column(ForeignKey("scholarships.id"), index=True)
    ig_media_container_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ig_media_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    publish_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    scholarship = relationship("Scholarship")
