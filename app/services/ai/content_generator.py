"""AI content generation service."""

import json
import logging

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.domain.schemas.content import GeneratedReelContent
from app.domain.schemas.scholarship import ScholarshipSheetRow
from app.services.ai.prompt_builder import build_reel_content_prompt

logger = logging.getLogger(__name__)


class OpenAIContentGenerator:
    """Generate reel content from scholarship data using OpenAI."""

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required.")
        if not settings.openai_model_text:
            raise ConfigurationError("OPENAI_MODEL_TEXT is required.")

        self.model_name = settings.openai_model_text
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate_reel_content(self, scholarship: ScholarshipSheetRow) -> GeneratedReelContent:
        prompt = build_reel_content_prompt(scholarship)

        try:
            response = self.client.responses.create(
                model=self.model_name,
                input=prompt,
            )
            payload = json.loads(response.output_text)
            return GeneratedReelContent.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.exception("Failed to parse AI response into reel content.")
            raise ExternalServiceError("AI returned invalid structured content.") from exc
        except Exception as exc:  # pragma: no cover - provider/network dependent
            logger.exception("OpenAI content generation failed.")
            raise ExternalServiceError("Failed to generate reel content.") from exc
