from canada_valet_cli.models import GroupMetadata, SeriesMetadata
from canada_valet_cli.search import search_metadata


def test_search_metadata_matches_description_and_key() -> None:
    results = search_metadata(
        "exchange rate",
        [SeriesMetadata(key="FXUSDCAD", label="USD/CAD", description="Exchange rate")],
        [GroupMetadata(key="FX_RATES_DAILY", label="Daily FX", description="Daily exchange rates")],
    )

    assert [item.key for item in results] == ["FXUSDCAD", "FX_RATES_DAILY"]
