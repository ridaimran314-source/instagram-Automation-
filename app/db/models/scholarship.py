"""Scholarship persistence model."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import ScholarshipStatus


class Scholarship(Base):
    """Normalized scholarship record mirrored from Google Sheets."""

    __tablename__ = "scholarships"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sheet_row_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scholarship_name: Mapped[str] = mapped_column(String(255))
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    scholarship_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    host_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    degree_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ScholarshipStatus] = mapped_column(
        Enum(ScholarshipStatus),
        default=ScholarshipStatus.PENDING,
        nullable=False,
    )
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
