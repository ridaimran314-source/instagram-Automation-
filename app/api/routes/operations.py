"""Operational routes for manual workflow execution."""

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.db.session import SessionLocal
from app.domain.schemas.operations import OperationResponse
from app.services.google_sheets.client import GoogleSheetsClient
from app.services.google_sheets.sync_service import ScholarshipSheetSyncService
from app.services.orchestration.scholarship_pipeline import ScholarshipPipeline

router = APIRouter(prefix="/operations", tags=["operations"])


@router.post("/sync-scholarships", response_model=OperationResponse)
def sync_scholarships() -> OperationResponse:
    settings = get_settings()
    try:
        client = GoogleSheetsClient(settings)
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    with SessionLocal() as session:
        result = ScholarshipSheetSyncService(session, client).sync()

    return OperationResponse(
        status="ok",
        detail=(
            f"Sync complete: fetched={result.fetched_rows}, created={result.created_records}, "
            f"updated={result.updated_records}, skipped={result.skipped_rows}"
        ),
    )


@router.post("/run-pipeline-once", response_model=OperationResponse)
def run_pipeline_once() -> OperationResponse:
    settings = get_settings()

    with SessionLocal() as session:
        try:
            processed = ScholarshipPipeline(settings=settings, session=session).run_once()
        except ConfigurationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except ExternalServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    return OperationResponse(
        status="ok",
        detail="Processed one pending scholarship." if processed else "No pending scholarships available.",
    )
