"""Mapping helpers for Google Sheets rows."""

from datetime import date

from app.core.exceptions import DataMappingError
from app.domain.enums import ScholarshipStatus
from app.domain.schemas.scholarship import ScholarshipSheetRow


def normalize_header(header: str) -> str:
    return header.strip().lower().replace(" ", "_")


def parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise DataMappingError(f"Invalid deadline format: {value}") from exc


def parse_status(value: str | None) -> ScholarshipStatus:
    if not value:
        return ScholarshipStatus.PENDING

    normalized = value.strip().lower()
    for status in ScholarshipStatus:
        if status.value == normalized:
            return status
    return ScholarshipStatus.PENDING


def map_sheet_row(headers: list[str], row_values: list[str], row_number: int) -> ScholarshipSheetRow:
    """Map a raw sheet row into the normalized scholarship schema."""

    normalized_headers = [normalize_header(header) for header in headers]
    row_data = {
        header: row_values[index].strip()
        for index, header in enumerate(normalized_headers)
        if index < len(row_values)
    }

    scholarship_name = row_data.get("scholarship_name")
    if not scholarship_name:
        raise DataMappingError(f"Row {row_number} is missing Scholarship Name.")

    return ScholarshipSheetRow(
        sheet_row_id=str(row_number),
        scholarship_name=scholarship_name,
        deadline=parse_optional_date(row_data.get("deadline")),
        scholarship_type=row_data.get("scholarship_type") or None,
        host_country=row_data.get("host_country") or None,
        degree_type=row_data.get("degree_type") or None,
        field_of_study=row_data.get("field_of_study") or None,
        status=parse_status(row_data.get("status")),
    )
