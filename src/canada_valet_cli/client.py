from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from canada_valet_cli.cache import ResponseCache
from canada_valet_cli.config import Settings, load_settings
from canada_valet_cli.exceptions import ValetHttpError, ValetResponseError
from canada_valet_cli.models import (
    GroupMetadata,
    GroupObservationResponse,
    Observation,
    SeriesMetadata,
    SeriesObservationResponse,
)


class ValetClient:
    """HTTP client for public Bank of Canada Valet API JSON endpoints."""

    def __init__(
        self,
        settings: Settings | None = None,
        cache: ResponseCache | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.cache = cache or ResponseCache(self.settings)
        self.http_client = http_client or httpx.Client(
            base_url=self.settings.base_url,
            timeout=self.settings.timeout_seconds,
            headers={"User-Agent": "canada-valet-cli/0.1.0"},
        )

    def series_path(self, series_name: str) -> str:
        return f"observations/{series_name}/json"

    def group_path(self, group_name: str) -> str:
        return f"observations/group/{group_name}/json"

    def series_metadata_path(self, series_name: str) -> str:
        return f"series/{series_name}/json"

    def group_metadata_path(self, group_name: str) -> str:
        return f"group/{group_name}/json"

    def list_series_path(self) -> str:
        return "lists/series/json"

    def list_groups_path(self) -> str:
        return "lists/groups/json"

    def fetch_series(
        self,
        series_name: str,
        start: date | None = None,
        end: date | None = None,
        use_cache: bool = True,
        cache_ttl_hours: int | None = None,
    ) -> SeriesObservationResponse:
        data = self._get_json(
            self.series_path(series_name),
            _date_params(start, end),
            use_cache=use_cache,
            cache_ttl_hours=cache_ttl_hours,
        )
        return normalize_series_observations(series_name, data)

    def fetch_group(
        self,
        group_name: str,
        start: date | None = None,
        end: date | None = None,
        use_cache: bool = True,
        cache_ttl_hours: int | None = None,
    ) -> GroupObservationResponse:
        data = self._get_json(
            self.group_path(group_name),
            _date_params(start, end),
            use_cache=use_cache,
            cache_ttl_hours=cache_ttl_hours,
        )
        return normalize_group_observations(group_name, data)

    def fetch_series_metadata(self, series_name: str, use_cache: bool = True) -> SeriesMetadata:
        data = self._get_json(self.series_metadata_path(series_name), {}, use_cache=use_cache)
        details = data.get("seriesDetails") or data.get("series") or data
        if not isinstance(details, dict):
            raise ValetResponseError("Series metadata response shape changed")
        return _series_metadata(series_name, details)

    def fetch_group_metadata(self, group_name: str, use_cache: bool = True) -> GroupMetadata:
        data = self._get_json(self.group_metadata_path(group_name), {}, use_cache=use_cache)
        details = data.get("groupDetails") or data.get("group") or data
        if not isinstance(details, dict):
            raise ValetResponseError("Group metadata response shape changed")
        return _group_metadata(group_name, details)

    def list_series(self, use_cache: bool = True) -> list[SeriesMetadata]:
        data = self._get_json(self.list_series_path(), {}, use_cache=use_cache)
        raw = data.get("series") or data.get("seriesDetails")
        if not isinstance(raw, dict):
            raise ValetResponseError("Series list response shape changed")
        return [_series_metadata(key, value) for key, value in sorted(raw.items())]

    def list_groups(self, use_cache: bool = True) -> list[GroupMetadata]:
        data = self._get_json(self.list_groups_path(), {}, use_cache=use_cache)
        raw = data.get("groups") or data.get("groupDetails")
        if not isinstance(raw, dict):
            raise ValetResponseError("Group list response shape changed")
        return [_group_metadata(key, value) for key, value in sorted(raw.items())]

    def _get_json(
        self,
        path: str,
        params: dict[str, str | None],
        use_cache: bool = True,
        cache_ttl_hours: int | None = None,
    ) -> dict[str, Any]:
        key = self.cache.key_for(path, params)
        if use_cache:
            cached = self.cache.get(key, ttl_hours=cache_ttl_hours)
            if cached is not None:
                return cached
        data = self._request_json(path, params)
        if use_cache:
            self.cache.set(key, data)
        return data

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _request_json(self, path: str, params: dict[str, str | None]) -> dict[str, Any]:
        clean_params = {key: value for key, value in params.items() if value is not None}
        response = self.http_client.get(path, params=clean_params)
        if response.status_code >= 400:
            raise ValetHttpError(f"Valet API returned HTTP {response.status_code} for {path}")
        try:
            data = response.json()
        except ValueError as exc:
            raise ValetResponseError("Valet API returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValetResponseError("Valet API response shape changed")
        return data


def normalize_series_observations(
    series_name: str, data: dict[str, Any]
) -> SeriesObservationResponse:
    observations = data.get("observations")
    if not isinstance(observations, list):
        raise ValetResponseError("Series observation response missing observations list")
    details = data.get("seriesDetail") or data.get("seriesDetails") or {}
    label = _label_for(series_name, details)
    normalized = [
        Observation(
            date=_parse_date(row),
            series=series_name,
            label=label,
            value=_value_for(row, series_name),
        )
        for row in observations
    ]
    return SeriesObservationResponse(series=series_name, observations=normalized, raw=data)


def normalize_group_observations(group_name: str, data: dict[str, Any]) -> GroupObservationResponse:
    observations = data.get("observations")
    if not isinstance(observations, list):
        raise ValetResponseError("Group observation response missing observations list")
    details = data.get("seriesDetail") or data.get("seriesDetails") or {}
    normalized: list[Observation] = []
    for row in observations:
        obs_date = _parse_date(row)
        for key, value in row.items():
            if key == "d" or not isinstance(value, dict):
                continue
            normalized.append(
                Observation(
                    date=obs_date,
                    series=key,
                    label=_label_for(key, details),
                    value=_extract_value(value),
                    group=group_name,
                )
            )
    return GroupObservationResponse(group=group_name, observations=normalized, raw=data)


def _date_params(start: date | None, end: date | None) -> dict[str, str | None]:
    return {
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
    }


def _parse_date(row: dict[str, Any]) -> date:
    value = row.get("d")
    if not isinstance(value, str):
        raise ValetResponseError("Observation missing date field 'd'")
    return date.fromisoformat(value)


def _value_for(row: dict[str, Any], series_name: str) -> str | None:
    raw = row.get(series_name)
    return _extract_value(raw) if isinstance(raw, dict) else None


def _extract_value(raw: dict[str, Any]) -> str | None:
    value = raw.get("v")
    return str(value) if value is not None else None


def _label_for(series_name: str, details: Any) -> str:
    if isinstance(details, dict):
        raw = details.get(series_name)
        if isinstance(raw, dict):
            return str(raw.get("label") or raw.get("description") or "")
    return ""


def _series_metadata(key: str, raw: Any) -> SeriesMetadata:
    data = raw if isinstance(raw, dict) else {}
    return SeriesMetadata(
        key=key,
        label=str(data.get("label") or data.get("name") or ""),
        description=str(data.get("description") or ""),
        link=str(data.get("link") or ""),
    )


def _group_metadata(key: str, raw: Any) -> GroupMetadata:
    data = raw if isinstance(raw, dict) else {}
    series_raw = data.get("groupSeries") or data.get("series") or {}
    series = []
    if isinstance(series_raw, dict):
        series = [_series_metadata(name, value) for name, value in sorted(series_raw.items())]
    return GroupMetadata(
        key=key,
        label=str(data.get("label") or data.get("name") or ""),
        description=str(data.get("description") or ""),
        link=str(data.get("link") or ""),
        series=series,
    )
