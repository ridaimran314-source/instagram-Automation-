"""Database engine and session helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session for request-scoped usage."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
