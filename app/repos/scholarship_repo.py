"""Persistence helpers for scholarship records."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.scholarship import Scholarship
from app.domain.enums import ScholarshipStatus
from app.domain.schemas.scholarship import ScholarshipSheetRow


class ScholarshipRepository:
    """Repository for scholarship CRUD operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_sheet_row_id(self, sheet_row_id: str) -> Scholarship | None:
        statement = select(Scholarship).where(Scholarship.sheet_row_id == sheet_row_id)
        return self.session.scalar(statement)

    def get_next_pending(self) -> Scholarship | None:
        statement = (
            select(Scholarship)
            .where(Scholarship.status == ScholarshipStatus.PENDING)
            .order_by(Scholarship.id.asc())
        )
        return self.session.scalar(statement)

    def set_status(self, scholarship: Scholarship, status: ScholarshipStatus) -> Scholarship:
        scholarship.status = status
        scholarship.updated_at = datetime.now(timezone.utc)
        return scholarship

    def upsert_from_sheet_row(self, row: ScholarshipSheetRow) -> tuple[Scholarship, bool]:
        scholarship = self.get_by_sheet_row_id(row.sheet_row_id)
        created = scholarship is None

        if scholarship is None:
            scholarship = Scholarship(
                sheet_row_id=row.sheet_row_id,
                scholarship_name=row.scholarship_name,
            )
            self.session.add(scholarship)

        scholarship.scholarship_name = row.scholarship_name
        scholarship.deadline = row.deadline
        scholarship.scholarship_type = row.scholarship_type
        scholarship.host_country = row.host_country
        scholarship.degree_type = row.degree_type
        scholarship.field_of_study = row.field_of_study
        scholarship.status = row.status

        return scholarship, created
