"""Persistence helpers for generated content."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.generated_content import GeneratedContent
from app.domain.schemas.content import GeneratedReelContent


class GeneratedContentRepository:
    """Repository for generated content records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_scholarship_id(self, scholarship_id: int) -> GeneratedContent | None:
        statement = select(GeneratedContent).where(GeneratedContent.scholarship_id == scholarship_id)
        return self.session.scalar(statement)

    def upsert_for_scholarship(
        self,
        scholarship_id: int,
        content: GeneratedReelContent,
        model_name: str | None,
    ) -> GeneratedContent:
        record = self.get_by_scholarship_id(scholarship_id)
        if record is None:
            record = GeneratedContent(scholarship_id=scholarship_id)
            self.session.add(record)

        record.hook_text = content.hook_text
        record.script_text = content.script_text
        record.voiceover_text = content.voiceover_text
        record.caption_text = content.caption_text
        record.hashtags_text = content.hashtags_text
        record.model_name = model_name
        return record
