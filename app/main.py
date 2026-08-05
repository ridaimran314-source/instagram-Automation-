"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.api.routes.operations import router as operations_router
from app.core.config import get_settings
from app.core.logging import configure_logging
import app.db.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine
from app.services.orchestration.bootstrap import ensure_runtime_directories
from app.workers.scheduler import build_scheduler

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize application dependencies on startup."""

    configure_logging(settings.log_level)
    ensure_runtime_directories(settings)
    Base.metadata.create_all(bind=engine)

    scheduler = None
    if settings.scheduler_enabled:
        scheduler = build_scheduler(settings)
        scheduler.start()
        logger.info("Scheduler started.")

    logger.info("Application startup complete.")
    try:
        yield
    finally:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped.")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(operations_router)
app.mount("/public/output", StaticFiles(directory=settings.output_root), name="public-output")
