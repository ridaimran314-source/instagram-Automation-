"""Google Sheets API client wrapper."""

import logging
from collections.abc import Sequence
from string import ascii_uppercase

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)

SHEETS_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GoogleSheetsClient:
    """Thin wrapper around the Google Sheets API."""

    def __init__(self, settings: Settings) -> None:
        if not settings.google_application_credentials:
            raise ConfigurationError("GOOGLE_APPLICATION_CREDENTIALS is required.")
        if not settings.google_sheet_id:
            raise ConfigurationError("GOOGLE_SHEET_ID is required.")
        if not settings.google_sheet_worksheet_name:
            raise ConfigurationError("GOOGLE_SHEET_WORKSHEET_NAME is required.")

        credentials = Credentials.from_service_account_file(
            settings.google_application_credentials,
            scopes=[SHEETS_READ_WRITE_SCOPE],
        )
        self.sheet_id = settings.google_sheet_id
        self.worksheet_name = settings.google_sheet_worksheet_name
        self.service = build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def get_all_values(self) -> list[list[str]]:
        """Return all sheet values, including the header row."""

        range_name = f"{self.worksheet_name}!A:Z"
        try:
            response = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.sheet_id, range=range_name)
                .execute()
            )
        except HttpError as exc:
            logger.exception("Failed to fetch rows from Google Sheets.")
            raise ExternalServiceError("Failed to fetch rows from Google Sheets.") from exc

        return response.get("values", [])

    def update_row_values(self, row_number: int, values: Sequence[str]) -> None:
        """Replace a row with updated values."""

        range_name = f"{self.worksheet_name}!A{row_number}:Z{row_number}"
        body = {"values": [list(values)]}
        try:
            (
                self.service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=self.sheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body=body,
                )
                .execute()
            )
        except HttpError as exc:
            logger.exception("Failed to update Google Sheets row %s.", row_number)
            raise ExternalServiceError("Failed to update Google Sheets row.") from exc

    def update_cells(self, row_number: int, values_by_column_name: dict[str, str]) -> None:
        """Update a subset of row cells based on header names."""

        all_values = self.get_all_values()
        if not all_values:
            raise ExternalServiceError("Cannot update cells on an empty sheet.")

        headers = all_values[0]
        data = []
        for column_name, value in values_by_column_name.items():
            try:
                column_index = headers.index(column_name)
            except ValueError as exc:
                raise ExternalServiceError(f"Column '{column_name}' not found in sheet header.") from exc

            data.append(
                {
                    "range": f"{self.worksheet_name}!{self._column_letter(column_index)}{row_number}",
                    "values": [[value]],
                }
            )

        body = {
            "valueInputOption": "RAW",
            "data": data,
        }

        try:
            (
                self.service.spreadsheets()
                .values()
                .batchUpdate(spreadsheetId=self.sheet_id, body=body)
                .execute()
            )
        except HttpError as exc:
            logger.exception("Failed to update cells for row %s.", row_number)
            raise ExternalServiceError("Failed to update Google Sheets cells.") from exc

    @staticmethod
    def _column_letter(index: int) -> str:
        if index < len(ascii_uppercase):
            return ascii_uppercase[index]
        raise ExternalServiceError("Column index exceeds supported sheet range.")
