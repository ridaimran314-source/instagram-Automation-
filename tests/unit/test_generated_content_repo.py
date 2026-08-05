from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.db.models  # noqa: F401
from app.db.base import Base
from app.db.models.scholarship import Scholarship
from app.domain.schemas.content import GeneratedReelContent
from app.repos.generated_content_repo import GeneratedContentRepository


def test_generated_content_repo_upserts_content() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        scholarship = Scholarship(
            sheet_row_id="2",
            scholarship_name="MIDE Master's Scholarship 2026 in Germany",
        )
        session.add(scholarship)
        session.commit()

        repository = GeneratedContentRepository(session)
        repository.upsert_for_scholarship(
            scholarship_id=scholarship.id,
            content=GeneratedReelContent(
                hook_text="Fully Funded Master's Scholarship in Germany",
                script_text="Applications are open. Study in Germany with funding.",
                voiceover_text="Applications are now open for a fully funded master's scholarship in Germany.",
                caption_text="Apply now for this scholarship opportunity in Germany.",
                hashtags_text="#scholarship #germany #masters",
            ),
            model_name="test-model",
        )
        session.commit()

        stored = repository.get_by_scholarship_id(scholarship.id)

        assert stored is not None
        assert stored.model_name == "test-model"
        assert stored.hook_text.startswith("Fully Funded")
