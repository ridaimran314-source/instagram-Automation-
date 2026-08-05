"""Synchronization logic for Google Sheets scholarship rows."""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import DataMappingError
from app.domain.schemas.scholarship import ScholarshipSyncResult
from app.repos.scholarship_repo import ScholarshipRepository
from app.services.google_sheets.client import GoogleSheetsClient
from app.services.google_sheets.mapper import map_sheet_row

logger = logging.getLogger(__name__)


class ScholarshipSheetSyncService:
    """Synchronize scholarship rows from Google Sheets into the local database."""

    def __init__(self, session: Session, sheets_client: GoogleSheetsClient) -> None:
        self.session = session
        self.sheets_client = sheets_client
        self.repository = ScholarshipRepository(session)

    def sync(self) -> ScholarshipSyncResult:
        values = self.sheets_client.get_all_values()
        if not values:
            logger.info("Google Sheet is empty; nothing to sync.")
            return ScholarshipSyncResult()

        headers = values[0]
        result = ScholarshipSyncResult()

        for row_index, row_values in enumerate(values[1:], start=2):
            result.fetched_rows += 1
            try:
                sheet_row = map_sheet_row(headers, row_values, row_index)
            except DataMappingError:
                logger.warning("Skipping invalid scholarship row %s.", row_index, exc_info=True)
                result.skipped_rows += 1
                continue

            _, created = self.repository.upsert_from_sheet_row(sheet_row)
            if created:
                result.created_records += 1
            else:
                result.updated_records += 1

        self.session.commit()
        logger.info(
            "Scholarship sync complete: fetched=%s created=%s updated=%s skipped=%s",
            result.fetched_rows,
            result.created_records,
            result.updated_records,
            result.skipped_rows,
        )
        return result
