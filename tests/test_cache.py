import json
from datetime import UTC, datetime, timedelta

from canada_valet_cli.cache import ResponseCache
from canada_valet_cli.config import Settings


def test_cache_miss(tmp_path) -> None:  # type: ignore[no-untyped-def]
    cache = ResponseCache(Settings(cache_dir=tmp_path))

    assert cache.get("missing") is None


def test_cache_hit(tmp_path) -> None:  # type: ignore[no-untyped-def]
    cache = ResponseCache(Settings(cache_dir=tmp_path))
    key = cache.key_for("observations/FXUSDCAD/json", {"start_date": "2024-01-01"})
    cache.set(key, {"ok": True})

    assert cache.get(key) == {"ok": True}


def test_cache_expired(tmp_path) -> None:  # type: ignore[no-untyped-def]
    cache = ResponseCache(Settings(cache_dir=tmp_path))
    key = "expired"
    (tmp_path / f"{key}.json").write_text(
        json.dumps(
            {
                "cached_at": (datetime.now(UTC) - timedelta(hours=48)).isoformat(),
                "data": {"ok": True},
            }
        ),
        encoding="utf-8",
    )

    assert cache.get(key, ttl_hours=1) is None


def test_cache_clear(tmp_path) -> None:  # type: ignore[no-untyped-def]
    cache = ResponseCache(Settings(cache_dir=tmp_path))
    cache.set("one", {"ok": True})
    cache.set("two", {"ok": True})

    assert cache.clear() == 2
    assert cache.info().file_count == 0
