"""Scholarship-related data contracts."""

from datetime import date

from pydantic import BaseModel, Field

from app.domain.enums import ScholarshipStatus


class ScholarshipSheetRow(BaseModel):
    """Normalized scholarship row read from Google Sheets."""

    sheet_row_id: str
    scholarship_name: str
    deadline: date | None = None
    scholarship_type: str | None = None
    host_country: str | None = None
    degree_type: str | None = None
    field_of_study: str | None = None
    status: ScholarshipStatus = ScholarshipStatus.PENDING


class ScholarshipSyncResult(BaseModel):
    """Summary of one synchronization pass."""

    fetched_rows: int = Field(default=0, ge=0)
    created_records: int = Field(default=0, ge=0)
    updated_records: int = Field(default=0, ge=0)
    skipped_rows: int = Field(default=0, ge=0)
