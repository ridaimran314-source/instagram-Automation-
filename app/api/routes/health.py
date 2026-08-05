"""Health-related API routes."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.domain.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return a lightweight liveness response."""

    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
    )


@router.get("/ready", response_model=HealthResponse)
def readiness_check() -> HealthResponse:
    """Return a lightweight readiness response."""

    settings = get_settings()
    return HealthResponse(
        status="ready",
        app_name=settings.app_name,
        environment=settings.app_env,
    )
