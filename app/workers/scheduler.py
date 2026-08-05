"""Scheduler setup for background polling jobs."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import Settings
from app.workers.jobs import run_pipeline_cycle

logger = logging.getLogger(__name__)


def build_scheduler(settings: Settings) -> BackgroundScheduler:
    """Create and configure the application scheduler."""

    scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)
    scheduler.add_job(
        run_pipeline_cycle,
        trigger=CronTrigger.from_crontab(
            settings.scheduler_poll_cron,
            timezone=settings.scheduler_timezone,
        ),
        id="pending-scholarship-sync",
        replace_existing=True,
    )
    return scheduler
