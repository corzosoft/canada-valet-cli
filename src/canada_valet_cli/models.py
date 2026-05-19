from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """A normalized tidy observation."""

    date: date
    series: str
    label: str = ""
    value: str | None = None
    group: str | None = None


class SeriesObservationResponse(BaseModel):
    """Normalized observations for one series."""

    series: str
    observations: list[Observation]
    raw: dict[str, Any] = Field(default_factory=dict)


class GroupObservationResponse(BaseModel):
    """Normalized observations for a Valet group."""

    group: str
    observations: list[Observation]
    raw: dict[str, Any] = Field(default_factory=dict)


class SeriesMetadata(BaseModel):
    """Metadata for a Valet series."""

    key: str
    label: str = ""
    description: str = ""
    link: str = ""


class GroupMetadata(BaseModel):
    """Metadata for a Valet group."""

    key: str
    label: str = ""
    description: str = ""
    link: str = ""
    series: list[SeriesMetadata] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """One validation check result."""

    check: str
    severity: str
    passed: bool
    message: str


class CacheInfo(BaseModel):
    """Summary of local API cache state."""

    cache_dir: Path
    file_count: int
    total_size_bytes: int
    default_ttl_hours: int
    oldest_cached_item: datetime | None = None
    newest_cached_item: datetime | None = None
