"""Background job entrypoints."""

import logging

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.db.session import SessionLocal
from app.services.google_sheets.client import GoogleSheetsClient
from app.services.google_sheets.sync_service import ScholarshipSheetSyncService
from app.services.orchestration.scholarship_pipeline import ScholarshipPipeline

logger = logging.getLogger(__name__)


def run_scholarship_sync_job() -> None:
    """Run one scholarship synchronization pass."""

    settings = get_settings()
    try:
        client = GoogleSheetsClient(settings)
    except ConfigurationError:
        logger.warning("Google Sheets sync skipped because configuration is incomplete.")
        return

    with SessionLocal() as session:
        try:
            service = ScholarshipSheetSyncService(session=session, sheets_client=client)
            result = service.sync()
            logger.info("Scholarship sync job finished: %s", result.model_dump())
        except ExternalServiceError:
            logger.exception("Scholarship sync job failed due to an external service error.")


def run_pipeline_cycle() -> None:
    """Synchronize sheet data, then process one pending scholarship if available."""

    run_scholarship_sync_job()

    settings = get_settings()
    with SessionLocal() as session:
        try:
            pipeline = ScholarshipPipeline(settings=settings, session=session)
            pipeline.run_once()
        except ConfigurationError:
            logger.warning("Scholarship pipeline skipped because configuration is incomplete.")
        except ExternalServiceError:
            logger.exception("Scholarship pipeline failed due to an external service error.")
