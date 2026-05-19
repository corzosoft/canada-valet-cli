from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from pathlib import Path

from platformdirs import user_cache_dir

DEFAULT_BASE_URL = "https://www.bankofcanada.ca/valet/"
DEFAULT_CACHE_TTL_HOURS = 24


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Valet client."""

    base_url: str = DEFAULT_BASE_URL
    cache_ttl_hours: int = DEFAULT_CACHE_TTL_HOURS
    cache_dir: Path = Path(user_cache_dir("canada-valet-cli", "canada-valet-cli"))
    timeout_seconds: float = 20.0


def load_settings(base_url: str | None = None, cache_ttl_hours: int | None = None) -> Settings:
    """Load settings from defaults, environment variables, and CLI overrides."""
    configured_base_url = base_url or getenv("VALET_BASE_URL") or DEFAULT_BASE_URL
    configured_ttl = cache_ttl_hours or int(
        getenv("VALET_CACHE_TTL_HOURS", DEFAULT_CACHE_TTL_HOURS)
    )
    normalized_base_url = configured_base_url.rstrip("/") + "/"
    return Settings(base_url=normalized_base_url, cache_ttl_hours=configured_ttl)
