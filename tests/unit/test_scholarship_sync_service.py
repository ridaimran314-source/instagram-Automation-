from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
import app.db.models  # noqa: F401
from app.services.google_sheets.sync_service import ScholarshipSheetSyncService


class FakeGoogleSheetsClient:
    def get_all_values(self) -> list[list[str]]:
        return [
            [
                "Scholarship Name",
                "Deadline",
                "Scholarship Type",
                "Host Country",
                "Degree Type",
                "Field of Study",
                "Status",
            ],
            [
                "MIDE Master's Scholarship 2026 in Germany",
                "2026-08-31",
                "Fully Funded",
                "Germany",
                "Masters",
                "International Economics",
                "Pending",
            ],
        ]


def test_sync_creates_scholarship_records() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        service = ScholarshipSheetSyncService(session, FakeGoogleSheetsClient())

        result = service.sync()

        assert result.fetched_rows == 1
        assert result.created_records == 1
        assert result.updated_records == 0
        assert result.skipped_rows == 0
