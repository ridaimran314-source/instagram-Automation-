"""Higher-level generated content workflow."""

from app.core.config import Settings
from app.domain.schemas.content import GeneratedReelContent
from app.domain.schemas.scholarship import ScholarshipSheetRow
from app.repos.generated_content_repo import GeneratedContentRepository
from app.services.ai.content_generator import OpenAIContentGenerator


class ReelContentGenerationService:
    """Generate and persist structured reel content for a scholarship."""

    def __init__(self, settings: Settings, repository: GeneratedContentRepository) -> None:
        self.generator = OpenAIContentGenerator(settings)
        self.repository = repository

    def generate_and_store(
        self,
        scholarship_id: int,
        scholarship: ScholarshipSheetRow,
    ) -> GeneratedReelContent:
        content = self.generator.generate_reel_content(scholarship)
        self.repository.upsert_for_scholarship(
            scholarship_id=scholarship_id,
            content=content,
            model_name=self.generator.model_name,
        )
        self.repository.session.commit()
        return content
