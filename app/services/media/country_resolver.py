"""Country normalization helpers for video lookup."""

import re

COUNTRY_ALIASES: dict[str, str] = {
    "united states": "USA",
    "us": "USA",
    "usa": "USA",
    "united kingdom": "UK",
    "great britain": "UK",
    "britain": "UK",
    "england": "UK",
}


def normalize_country_name(country: str) -> str:
    normalized = re.sub(r"\s+", " ", country.strip()).lower()
    return COUNTRY_ALIASES.get(normalized, country.strip())
