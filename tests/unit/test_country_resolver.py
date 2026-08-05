from app.services.media.country_resolver import normalize_country_name


def test_normalize_country_name_resolves_common_aliases() -> None:
    assert normalize_country_name("United States") == "USA"
    assert normalize_country_name("britain") == "UK"
    assert normalize_country_name("Germany") == "Germany"
