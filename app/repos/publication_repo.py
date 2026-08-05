"""Persistence helpers for Instagram publication records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.publication import Publication
from app.domain.schemas.publishing import InstagramPublishResult


class PublicationRepository:
    """Repository for publication state persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_scholarship_id(self, scholarship_id: int) -> Publication | None:
        statement = select(Publication).where(Publication.scholarship_id == scholarship_id)
        return self.session.scalar(statement)

    def upsert_from_publish_result(
        self,
        scholarship_id: int,
        result: InstagramPublishResult,
    ) -> Publication:
        record = self.get_by_scholarship_id(scholarship_id)
        if record is None:
            record = Publication(scholarship_id=scholarship_id)
            self.session.add(record)

        record.ig_media_container_id = result.media_container_id
        record.ig_media_id = result.media_id
        record.instagram_url = result.instagram_url
        record.publish_status = result.status
        return record
