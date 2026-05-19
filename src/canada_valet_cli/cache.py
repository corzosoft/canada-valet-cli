from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from canada_valet_cli.config import Settings
from canada_valet_cli.exceptions import ValetCacheError
from canada_valet_cli.models import CacheInfo


class ResponseCache:
    """Small filesystem JSON cache for polite API usage."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cache_dir = settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def key_for(self, path: str, params: dict[str, str | None]) -> str:
        clean_params = {key: value for key, value in sorted(params.items()) if value is not None}
        payload = json.dumps({"path": path, "params": clean_params}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str, ttl_hours: int | None = None) -> dict[str, Any] | None:
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValetCacheError(f"Could not read cache file: {path}") from exc
        cached_at = datetime.fromisoformat(cached["cached_at"])
        ttl = timedelta(hours=ttl_hours or self.settings.cache_ttl_hours)
        if datetime.now(UTC) - cached_at > ttl:
            return None
        data = cached.get("data")
        return data if isinstance(data, dict) else None

    def set(self, key: str, data: dict[str, Any]) -> None:
        path = self._path_for(key)
        payload = {"cached_at": datetime.now(UTC).isoformat(), "data": data}
        try:
            path.write_text(json.dumps(payload), encoding="utf-8")
        except OSError as exc:
            raise ValetCacheError(f"Could not write cache file: {path}") from exc

    def clear(self) -> int:
        count = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
            count += 1
        return count

    def info(self) -> CacheInfo:
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(path.stat().st_size for path in files)
        mtimes = [datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) for path in files]
        return CacheInfo(
            cache_dir=self.cache_dir,
            file_count=len(files),
            total_size_bytes=total_size,
            default_ttl_hours=self.settings.cache_ttl_hours,
            oldest_cached_item=min(mtimes) if mtimes else None,
            newest_cached_item=max(mtimes) if mtimes else None,
        )

    def _path_for(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"
