"""Shared API dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db_session


def get_database_session() -> Generator[Session, None, None]:
    """Expose database sessions through FastAPI dependency injection."""

    yield from get_db_session()
