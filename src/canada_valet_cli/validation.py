from __future__ import annotations

from datetime import date, timedelta

from canada_valet_cli.models import Observation, ValidationResult


def validate_observations(observations: list[Observation]) -> list[ValidationResult]:
    """Validate normalized observations for common data quality issues."""
    results = [
        _result("non_empty_response", "high", bool(observations), "Response contains observations"),
    ]
    if not observations:
        return results

    dates = [observation.date for observation in observations]
    values = [observation.value for observation in observations]
    duplicates = {value for value in dates if dates.count(value) > 1}
    missing_values = sum(1 for value in values if value in (None, ""))
    non_numeric_values = sum(
        1 for value in values if value not in (None, "") and not _is_numeric(value)
    )

    results.extend(
        [
            _result(
                "observation_dates_present", "high", all(dates), "All observations include dates"
            ),
            _result(
                "duplicate_observation_dates",
                "high",
                not duplicates,
                f"Duplicate dates: {', '.join(str(item) for item in sorted(duplicates)) or 'none'}",
            ),
            _result(
                "missing_values",
                "high",
                missing_values == 0,
                f"Missing values: {missing_values}",
            ),
            _result(
                "numeric_values",
                "high",
                non_numeric_values == 0,
                f"Non-numeric values: {non_numeric_values}",
            ),
            _date_gap_result(sorted(set(dates))),
            _stale_result(max(dates)),
            _result("api_shape", "high", True, "API response normalized successfully"),
        ]
    )
    return results


def has_high_severity_failure(results: list[ValidationResult]) -> bool:
    """Return true when any high-severity validation check failed."""
    return any(result.severity == "high" and not result.passed for result in results)


def _date_gap_result(dates: list[date]) -> ValidationResult:
    gaps = [
        (previous, current)
        for previous, current in zip(dates, dates[1:], strict=False)
        if current - previous > timedelta(days=7)
    ]
    return _result(
        "unexpected_date_gaps",
        "medium",
        not gaps,
        f"Gaps longer than 7 days: {len(gaps)}",
    )


def _stale_result(latest_date: date) -> ValidationResult:
    age_days = (date.today() - latest_date).days
    return _result(
        "stale_dataset", "medium", age_days <= 14, f"Latest observation age: {age_days} days"
    )


def _is_numeric(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _result(check: str, severity: str, passed: bool, message: str) -> ValidationResult:
    return ValidationResult(check=check, severity=severity, passed=passed, message=message)
