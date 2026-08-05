"""Helpers for writing workflow status updates back to Google Sheets."""

from datetime import datetime, timezone

from app.services.google_sheets.client import GoogleSheetsClient


class GoogleSheetStatusService:
    """Update scholarship workflow columns in Google Sheets."""

    def __init__(self, client: GoogleSheetsClient) -> None:
        self.client = client

    def mark_processing(self, row_number: int) -> None:
        self.client.update_cells(
            row_number=row_number,
            values_by_column_name={
                "Status": "Processing",
                "Error": "",
                "Last Processed At": self._timestamp(),
            },
        )

    def mark_published(self, row_number: int, instagram_url: str) -> None:
        self.client.update_cells(
            row_number=row_number,
            values_by_column_name={
                "Status": "Published",
                "Instagram URL": instagram_url,
                "Publish Date": self._timestamp(),
                "Error": "",
            },
        )

    def mark_failed(self, row_number: int, error_message: str) -> None:
        self.client.update_cells(
            row_number=row_number,
            values_by_column_name={
                "Status": "Failed",
                "Error": error_message[:500],
                "Last Processed At": self._timestamp(),
            },
        )

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
