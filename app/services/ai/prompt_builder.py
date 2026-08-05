"""Prompt construction for AI-generated reel content."""

from app.domain.schemas.scholarship import ScholarshipSheetRow


def build_reel_content_prompt(scholarship: ScholarshipSheetRow) -> str:
    """Build a grounded prompt for short-form reel content generation."""

    return f"""
You are generating structured Instagram Reel copy for a scholarship platform.

Use only the scholarship facts provided below. Do not invent benefits, eligibility, deadlines, or locations.
Keep the tone professional, concise, and social-media friendly.

Return valid JSON with exactly these keys:
- hook_text
- script_text
- voiceover_text
- caption_text
- hashtags_text

Constraints:
- hook_text: max 120 characters
- script_text: 2 short sentences
- voiceover_text: 2 to 4 short sentences
- caption_text: concise Instagram caption with CTA
- hashtags_text: space-separated hashtags only

Scholarship data:
- Scholarship Name: {scholarship.scholarship_name}
- Deadline: {scholarship.deadline}
- Scholarship Type: {scholarship.scholarship_type}
- Host Country: {scholarship.host_country}
- Degree Type: {scholarship.degree_type}
- Field of Study: {scholarship.field_of_study}
""".strip()
