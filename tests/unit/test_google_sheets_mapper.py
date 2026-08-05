from datetime import date

import pytest

from app.core.exceptions import DataMappingError
from app.domain.enums import ScholarshipStatus
from app.services.google_sheets.mapper import map_sheet_row


def test_map_sheet_row_returns_normalized_schema() -> None:
    headers = [
        "Scholarship Name",
        "Deadline",
        "Scholarship Type",
        "Host Country",
        "Degree Type",
        "Field of Study",
        "Status",
    ]
    values = [
        "MIDE Master's Scholarship 2026 in Germany",
        "2026-08-31",
        "Fully Funded",
        "Germany",
        "Masters",
        "International Economics, Development Economics",
        "Pending",
    ]

    result = map_sheet_row(headers, values, row_number=2)

    assert result.sheet_row_id == "2"
    assert result.scholarship_name == "MIDE Master's Scholarship 2026 in Germany"
    assert result.deadline == date(2026, 8, 31)
    assert result.status == ScholarshipStatus.PENDING


def test_map_sheet_row_raises_for_missing_name() -> None:
    headers = ["Scholarship Name", "Deadline"]
    values = ["", "2026-08-31"]

    with pytest.raises(DataMappingError):
        map_sheet_row(headers, values, row_number=3)
