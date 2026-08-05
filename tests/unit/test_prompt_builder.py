from datetime import date

from app.domain.schemas.scholarship import ScholarshipSheetRow
from app.services.ai.prompt_builder import build_reel_content_prompt


def test_build_reel_content_prompt_includes_grounding_fields() -> None:
    scholarship = ScholarshipSheetRow(
        sheet_row_id="2",
        scholarship_name="MIDE Master's Scholarship 2026 in Germany",
        deadline=date(2026, 8, 31),
        scholarship_type="Fully Funded",
        host_country="Germany",
        degree_type="Masters",
        field_of_study="International Economics, Development Economics",
    )

    prompt = build_reel_content_prompt(scholarship)

    assert "Return valid JSON" in prompt
    assert scholarship.scholarship_name in prompt
    assert "Germany" in prompt
    assert "Fully Funded" in prompt
