from datetime import date

from canada_valet_cli.models import Observation
from canada_valet_cli.validation import has_high_severity_failure, validate_observations


def test_validation_rules_find_high_severity_issues() -> None:
    observations = [
        Observation(date=date(2024, 1, 1), series="TEST", value="1.0"),
        Observation(date=date(2024, 1, 1), series="TEST", value=None),
        Observation(date=date(2024, 1, 10), series="TEST", value="not-number"),
    ]

    results = validate_observations(observations)

    assert has_high_severity_failure(results)
    assert {result.check for result in results if not result.passed} >= {
        "duplicate_observation_dates",
        "missing_values",
        "numeric_values",
    }


def test_empty_response_is_invalid() -> None:
    results = validate_observations([])

    assert has_high_severity_failure(results)
