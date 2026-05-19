from __future__ import annotations

import json
import sys
from datetime import date
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.console import Console

from canada_valet_cli.cache import ResponseCache
from canada_valet_cli.client import ValetClient
from canada_valet_cli.config import DEFAULT_CACHE_TTL_HOURS, load_settings
from canada_valet_cli.exceptions import ValetApiError, ValetExportError
from canada_valet_cli.export import observations_to_csv, observations_to_json, write_observations
from canada_valet_cli.formatting import (
    print_cache_info,
    print_metadata_table,
    print_observations_table,
    print_validation_table,
)
from canada_valet_cli.models import GroupMetadata, Observation, SeriesMetadata
from canada_valet_cli.search import search_metadata
from canada_valet_cli.validation import has_high_severity_failure, validate_observations

app = typer.Typer(
    help="Unofficial CLI for public Bank of Canada Valet API data.",
    no_args_is_help=True,
)
list_app = typer.Typer(help="List available Valet metadata.")
cache_app = typer.Typer(help="Inspect or clear local response cache.")
app.add_typer(list_app, name="list")
app.add_typer(cache_app, name="cache")
console = Console()


def _client(base_url: str | None = None, cache_ttl_hours: int | None = None) -> ValetClient:
    settings = load_settings(base_url=base_url, cache_ttl_hours=cache_ttl_hours)
    return ValetClient(settings=settings)


def _parse_date_option(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter("Dates must use YYYY-MM-DD format") from exc


def _write_or_print_text(text: str, out: Path | None) -> None:
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        console.print(f"Wrote {out}")
    else:
        console.print(text)


def _output_observations(
    observations: list[Observation],
    output_format: str,
    out: Path | None,
) -> None:
    if output_format == "table":
        print_observations_table(observations, console)
    elif output_format == "json":
        _write_or_print_text(observations_to_json(observations), out)
    elif output_format == "csv":
        _write_or_print_text(observations_to_csv(observations), out)
    else:
        raise typer.BadParameter(f"Unsupported format: {output_format}")


def _metadata_to_json(items: list[SeriesMetadata | GroupMetadata]) -> str:
    return json.dumps([item.model_dump(mode="json") for item in items], indent=2)


def _metadata_to_csv(items: list[SeriesMetadata | GroupMetadata]) -> str:
    import pandas as pd

    rows = []
    for item in items:
        rows.append(
            {
                "key": item.key,
                "label": item.label,
                "description": item.description,
                "link": item.link,
                "type": "group" if isinstance(item, GroupMetadata) else "series",
            }
        )
    return pd.DataFrame(rows).to_csv(index=False)


def _output_metadata(
    items: list[SeriesMetadata | GroupMetadata],
    output_format: str,
    out: Path | None,
) -> None:
    if output_format == "table":
        print_metadata_table(items, console)
    elif output_format == "json":
        _write_or_print_text(_metadata_to_json(items), out)
    elif output_format == "csv":
        _write_or_print_text(_metadata_to_csv(items), out)
    else:
        raise typer.BadParameter(f"Unsupported format: {output_format}")


@app.command()
def series(
    series_name: Annotated[str, typer.Argument(help="Bank of Canada Valet series name.")],
    start: Annotated[str | None, typer.Option(help="Start date as YYYY-MM-DD.")] = None,
    end: Annotated[str | None, typer.Option(help="End date as YYYY-MM-DD.")] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: table, json, or csv.")
    ] = "table",
    out: Annotated[Path | None, typer.Option(help="Optional output file path.")] = None,
    no_cache: Annotated[bool, typer.Option(help="Bypass local response cache.")] = False,
    cache_ttl: Annotated[
        int, typer.Option("--cache-ttl", help="Cache TTL in hours.")
    ] = DEFAULT_CACHE_TTL_HOURS,
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Fetch observations for a single series."""
    try:
        response = _client(base_url, cache_ttl).fetch_series(
            series_name,
            start=_parse_date_option(start),
            end=_parse_date_option(end),
            use_cache=not no_cache,
            cache_ttl_hours=cache_ttl,
        )
        _output_observations(response.observations, output_format, out)
    except ValetApiError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def group(
    group_name: Annotated[str, typer.Argument(help="Bank of Canada Valet group name.")],
    start: Annotated[str | None, typer.Option(help="Start date as YYYY-MM-DD.")] = None,
    end: Annotated[str | None, typer.Option(help="End date as YYYY-MM-DD.")] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: table, json, or csv.")
    ] = "table",
    out: Annotated[Path | None, typer.Option(help="Optional output file path.")] = None,
    no_cache: Annotated[bool, typer.Option(help="Bypass local response cache.")] = False,
    cache_ttl: Annotated[
        int, typer.Option("--cache-ttl", help="Cache TTL in hours.")
    ] = DEFAULT_CACHE_TTL_HOURS,
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Fetch observations for a Valet group."""
    try:
        response = _client(base_url, cache_ttl).fetch_group(
            group_name,
            start=_parse_date_option(start),
            end=_parse_date_option(end),
            use_cache=not no_cache,
            cache_ttl_hours=cache_ttl,
        )
        _output_observations(response.observations, output_format, out)
    except ValetApiError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def metadata(
    name: Annotated[str, typer.Argument(help="Series or group name.")],
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Show metadata for a series or group."""
    client = _client(base_url)
    try:
        item: SeriesMetadata | GroupMetadata = client.fetch_series_metadata(name)
    except ValetApiError:
        try:
            item = client.fetch_group_metadata(name)
        except ValetApiError as exc:
            console.print(f"[red]No metadata found for {name}[/red]")
            raise typer.Exit(1) from exc
    print_metadata_table([item], console)


@list_app.command("series")
def list_series(
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: table, json, or csv.")
    ] = "table",
    out: Annotated[Path | None, typer.Option(help="Optional output file path.")] = None,
    refresh: Annotated[bool, typer.Option(help="Bypass metadata cache.")] = False,
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """List available series metadata."""
    try:
        _output_metadata(_client(base_url).list_series(use_cache=not refresh), output_format, out)
    except ValetApiError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@list_app.command("groups")
def list_groups(
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: table, json, or csv.")
    ] = "table",
    out: Annotated[Path | None, typer.Option(help="Optional output file path.")] = None,
    refresh: Annotated[bool, typer.Option(help="Bypass metadata cache.")] = False,
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """List available group metadata."""
    try:
        _output_metadata(_client(base_url).list_groups(use_cache=not refresh), output_format, out)
    except ValetApiError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query.")],
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Search cached or fetched series and group metadata."""
    try:
        client = _client(base_url)
        results = search_metadata(query, client.list_series(), client.list_groups())
        print_metadata_table(results, console)
    except ValetApiError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def export(
    name: Annotated[str, typer.Argument(help="Series or group name.")],
    start: Annotated[str | None, typer.Option(help="Start date as YYYY-MM-DD.")] = None,
    end: Annotated[str | None, typer.Option(help="End date as YYYY-MM-DD.")] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Export format: csv, json, or parquet.")
    ] = "csv",
    out: Annotated[Path, typer.Option(help="Output file path.")] = Path("valet-export.csv"),
    data_type: Annotated[str, typer.Option("--type", help="series or group.")] = "series",
    no_cache: Annotated[bool, typer.Option(help="Bypass local response cache.")] = False,
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Export observations to CSV, JSON, or Parquet."""
    try:
        client = _client(base_url)
        if data_type == "series":
            observations = client.fetch_series(
                name,
                _parse_date_option(start),
                _parse_date_option(end),
                use_cache=not no_cache,
            ).observations
        elif data_type == "group":
            observations = client.fetch_group(
                name,
                _parse_date_option(start),
                _parse_date_option(end),
                use_cache=not no_cache,
            ).observations
        else:
            raise typer.BadParameter("--type must be series or group")
        path = write_observations(observations, out, output_format)
        console.print(f"Wrote {path}")
    except (ValetApiError, ValetExportError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def validate(
    series_name: Annotated[str, typer.Argument(help="Bank of Canada Valet series name.")],
    start: Annotated[str | None, typer.Option(help="Start date as YYYY-MM-DD.")] = None,
    end: Annotated[str | None, typer.Option(help="End date as YYYY-MM-DD.")] = None,
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Fetch and validate observations for a series."""
    try:
        observations = (
            _client(base_url)
            .fetch_series(series_name, _parse_date_option(start), _parse_date_option(end))
            .observations
        )
        results = validate_observations(observations)
        print_validation_table(results, console)
        if has_high_severity_failure(results):
            raise typer.Exit(1)
    except ValetApiError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@cache_app.command("info")
def cache_info(
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Show local cache information."""
    print_cache_info(ResponseCache(load_settings(base_url)).info(), console)


@cache_app.command("clear")
def cache_clear(
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation.")] = False,
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Clear cached API responses."""
    if not yes and not typer.confirm("Clear all cached Valet API responses?"):
        raise typer.Exit()
    count = ResponseCache(load_settings(base_url)).clear()
    console.print(f"Cleared {count} cached files")


@app.command()
def doctor(
    base_url: Annotated[str | None, typer.Option(help="Override Valet base URL.")] = None,
) -> None:
    """Check local setup and API connectivity."""
    settings = load_settings(base_url)
    checks: list[tuple[str, str]] = []
    checks.append(("Python", sys.version.split()[0]))
    checks.append(("Package", version("canada-valet-cli")))
    checks.append(("Base URL", settings.base_url))
    cache = ResponseCache(settings)
    checks.append(("Cache writable", "yes" if cache.cache_dir.exists() else "no"))
    try:
        import pyarrow  # noqa: F401

        checks.append(("pyarrow", "available"))
    except ImportError:
        checks.append(("pyarrow", "not installed"))
    try:
        response = httpx.get(f"{settings.base_url}lists/groups/json", timeout=10)
        checks.append(("API connectivity", f"HTTP {response.status_code}"))
    except httpx.HTTPError as exc:
        checks.append(("API connectivity", f"failed: {exc}"))

    from rich.table import Table

    table = Table(title="Valet Doctor")
    table.add_column("Check")
    table.add_column("Result")
    for check, result in checks:
        table.add_row(check, result)
    console.print(table)


if __name__ == "__main__":
    app()
