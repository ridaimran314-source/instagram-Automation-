"""Generated reel content persistence model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeneratedContent(Base):
    """Stores AI-generated content for a scholarship reel."""

    __tablename__ = "generated_contents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scholarship_id: Mapped[int] = mapped_column(ForeignKey("scholarships.id"), index=True, unique=True)
    hook_text: Mapped[str] = mapped_column(String(120))
    script_text: Mapped[str] = mapped_column(Text)
    voiceover_text: Mapped[str] = mapped_column(Text)
    caption_text: Mapped[str] = mapped_column(Text)
    hashtags_text: Mapped[str] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    scholarship = relationship("Scholarship")
