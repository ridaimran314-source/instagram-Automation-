"""End-to-end scholarship reel processing pipeline."""

import logging
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import ExternalServiceError
from app.domain.enums import ScholarshipStatus
from app.domain.schemas.publishing import InstagramPublishRequest
from app.domain.schemas.rendering import RenderRequest
from app.domain.schemas.scholarship import ScholarshipSheetRow
from app.repos.generated_content_repo import GeneratedContentRepository
from app.repos.publication_repo import PublicationRepository
from app.repos.scholarship_repo import ScholarshipRepository
from app.services.ai.generation_service import ReelContentGenerationService
from app.services.ai.tts_service import build_tts_service
from app.services.google_sheets.client import GoogleSheetsClient
from app.services.google_sheets.status_service import GoogleSheetStatusService
from app.services.instagram.graph_client import InstagramGraphClient
from app.services.instagram.publisher import InstagramPublisher
from app.services.media.subtitle_service import SubtitleService
from app.services.media.video_selector import VideoSelector
from app.services.orchestration.asset_delivery import PublicAssetResolver
from app.services.rendering.renderer import FFmpegRenderer

logger = logging.getLogger(__name__)


class ScholarshipPipeline:
    """Run the complete reel workflow for one pending scholarship."""

    def __init__(self, settings: Settings, session: Session) -> None:
        self.settings = settings
        self.session = session
        self.scholarship_repo = ScholarshipRepository(session)
        self.generated_content_repo = GeneratedContentRepository(session)
        self.publication_repo = PublicationRepository(session)

    def run_once(self) -> bool:
        scholarship = self.scholarship_repo.get_next_pending()
        if scholarship is None:
            logger.info("No pending scholarships found for processing.")
            return False

        sheets_client = GoogleSheetsClient(self.settings)
        sheet_status_service = GoogleSheetStatusService(sheets_client)

        sheet_row = ScholarshipSheetRow(
            sheet_row_id=scholarship.sheet_row_id,
            scholarship_name=scholarship.scholarship_name,
            deadline=scholarship.deadline,
            scholarship_type=scholarship.scholarship_type,
            host_country=scholarship.host_country,
            degree_type=scholarship.degree_type,
            field_of_study=scholarship.field_of_study,
            status=scholarship.status,
        )
        row_number = int(scholarship.sheet_row_id)

        try:
            self.scholarship_repo.set_status(scholarship, ScholarshipStatus.PROCESSING)
            self.session.commit()
            sheet_status_service.mark_processing(row_number)

            content_service = ReelContentGenerationService(self.settings, self.generated_content_repo)
            content = content_service.generate_and_store(scholarship.id, sheet_row)

            video_asset = VideoSelector(self.settings).select_for_country(scholarship.host_country)
            tts_service = build_tts_service(self.settings)
            file_stem = self._slugify(f"{scholarship.id}-{scholarship.scholarship_name}")
            voiceover = tts_service.synthesize(content.voiceover_text, file_stem=file_stem)

            subtitle_service = SubtitleService()
            estimated_duration = subtitle_service.estimate_duration_seconds(content.voiceover_text)
            subtitle_segments = subtitle_service.build_segments(
                content.voiceover_text,
                total_duration_seconds=estimated_duration,
            )
            subtitle_path = subtitle_service.write_srt(
                subtitle_segments,
                Path(self.settings.output_root) / "subtitles" / f"{file_stem}.srt",
            )

            render_request = RenderRequest(
                background_video_path=video_asset.video_path,
                output_video_path=str(Path(self.settings.output_root) / "renders" / f"{file_stem}.mp4"),
                hook_text=content.hook_text,
                subtitle_path=str(subtitle_path),
                voiceover_audio_path=voiceover.audio_path,
                logo_path=self._existing_file_or_none(Path(self.settings.assets_root) / "logo" / "logo.png"),
                background_music_path=self._default_music_path(),
                target_duration_seconds=max(15, round(estimated_duration) + 2),
            )
            render_result = FFmpegRenderer(self.settings).render(render_request)

            media_url = PublicAssetResolver(self.settings).resolve_public_url(render_result.output_video_path)
            publisher = InstagramPublisher(InstagramGraphClient(self.settings))
            publish_result = publisher.publish_reel(
                InstagramPublishRequest(
                    media_url=media_url,
                    caption_text=f"{content.caption_text}\n\n{content.hashtags_text}",
                )
            )
            self.publication_repo.upsert_from_publish_result(scholarship.id, publish_result)
            self.scholarship_repo.set_status(scholarship, ScholarshipStatus.PUBLISHED)
            self.session.commit()

            sheet_status_service.mark_published(row_number, publish_result.instagram_url or "")

            logger.info("Scholarship %s processed successfully.", scholarship.id)
            return True
        except Exception as exc:
            self.session.rollback()
            self.scholarship_repo.set_status(scholarship, ScholarshipStatus.FAILED)
            self.session.commit()

            error_message = str(exc)
            try:
                sheet_status_service.mark_failed(row_number, error_message)
            except ExternalServiceError:
                logger.exception("Failed to write failure status back to Google Sheets.")

            logger.exception("Scholarship %s processing failed.", scholarship.id)
            return False

    def _default_music_path(self) -> str | None:
        music_root = Path(self.settings.assets_root) / "music"
        for extension in (".mp3", ".wav", ".m4a"):
            files = sorted(music_root.glob(f"*{extension}"))
            if files:
                return str(files[0])
        return None

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
        return normalized or "scholarship-reel"

    @staticmethod
    def _existing_file_or_none(path: Path) -> str | None:
        return str(path) if path.exists() else None
