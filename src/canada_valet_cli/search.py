from __future__ import annotations

from canada_valet_cli.models import GroupMetadata, SeriesMetadata


def search_metadata(
    query: str,
    series: list[SeriesMetadata],
    groups: list[GroupMetadata],
    limit: int = 25,
) -> list[SeriesMetadata | GroupMetadata]:
    """Search series and group metadata by key, label, and description."""
    terms = [term.casefold() for term in query.split() if term.strip()]
    scored: list[tuple[int, SeriesMetadata | GroupMetadata]] = []
    for item in [*series, *groups]:
        haystack = f"{item.key} {item.label} {item.description}".casefold()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, item))
    return [item for _, item in sorted(scored, key=lambda pair: (-pair[0], pair[1].key))[:limit]]
