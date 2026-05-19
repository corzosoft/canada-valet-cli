from __future__ import annotations

from rich.console import Console
from rich.table import Table

from canada_valet_cli.models import (
    CacheInfo,
    GroupMetadata,
    Observation,
    SeriesMetadata,
    ValidationResult,
)


def print_observations_table(observations: list[Observation], console: Console) -> None:
    table = Table(title="Valet Observations")
    for column in ["date", "series", "label", "value", "group"]:
        table.add_column(column)
    for observation in observations:
        table.add_row(
            observation.date.isoformat(),
            observation.series,
            observation.label,
            observation.value or "",
            observation.group or "",
        )
    console.print(table)


def print_metadata_table(items: list[SeriesMetadata | GroupMetadata], console: Console) -> None:
    table = Table(title="Valet Metadata")
    for column in ["key", "label", "description", "type"]:
        table.add_column(column)
    for item in items:
        item_type = "group" if isinstance(item, GroupMetadata) else "series"
        table.add_row(item.key, item.label, item.description, item_type)
    console.print(table)


def print_validation_table(results: list[ValidationResult], console: Console) -> None:
    table = Table(title="Validation Results")
    for column in ["check", "severity", "status", "message"]:
        table.add_column(column)
    for result in results:
        table.add_row(
            result.check, result.severity, "PASS" if result.passed else "FAIL", result.message
        )
    console.print(table)


def print_cache_info(info: CacheInfo, console: Console) -> None:
    table = Table(title="Valet Cache")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("cache directory", str(info.cache_dir))
    table.add_row("cached files", str(info.file_count))
    table.add_row("total size bytes", str(info.total_size_bytes))
    table.add_row("default TTL hours", str(info.default_ttl_hours))
    table.add_row("oldest cached item", str(info.oldest_cached_item or "n/a"))
    table.add_row("newest cached item", str(info.newest_cached_item or "n/a"))
    console.print(table)
