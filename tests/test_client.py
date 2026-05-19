from __future__ import annotations

from datetime import date

import httpx
import pytest
from pytest_httpx import HTTPXMock

from canada_valet_cli.client import ValetClient
from canada_valet_cli.config import Settings
from canada_valet_cli.exceptions import ValetResponseError


def settings(tmp_path) -> Settings:  # type: ignore[no-untyped-def]
    return Settings(cache_dir=tmp_path)


def series_payload() -> dict:
    return {
        "seriesDetail": {"FXUSDCAD": {"label": "USD/CAD"}},
        "observations": [{"d": "2024-01-02", "FXUSDCAD": {"v": "1.3312"}}],
    }


def group_payload() -> dict:
    return {
        "seriesDetail": {"FXUSDCAD": {"label": "USD/CAD"}, "FXEURCAD": {"label": "EUR/CAD"}},
        "observations": [
            {"d": "2024-01-02", "FXUSDCAD": {"v": "1.3312"}, "FXEURCAD": {"v": "1.4512"}}
        ],
    }


def test_successful_series_fetch(httpx_mock: HTTPXMock, tmp_path) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(json=series_payload())

    response = ValetClient(settings(tmp_path)).fetch_series(
        "FXUSDCAD", start=date(2024, 1, 1), end=date(2024, 1, 31)
    )

    assert response.series == "FXUSDCAD"
    assert response.observations[0].value == "1.3312"


def test_successful_group_fetch(httpx_mock: HTTPXMock, tmp_path) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(json=group_payload())

    response = ValetClient(settings(tmp_path)).fetch_group("FX_RATES_DAILY")

    assert response.group == "FX_RATES_DAILY"
    assert len(response.observations) == 2
    assert response.observations[0].group == "FX_RATES_DAILY"


def test_metadata_fetch(httpx_mock: HTTPXMock, tmp_path) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        json={"seriesDetails": {"label": "USD/CAD", "description": "Exchange rate"}}
    )

    metadata = ValetClient(settings(tmp_path)).fetch_series_metadata("FXUSDCAD")

    assert metadata.key == "FXUSDCAD"
    assert metadata.label == "USD/CAD"


def test_retry_behavior(httpx_mock: HTTPXMock, tmp_path) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_exception(httpx.ConnectError("temporary failure"))
    httpx_mock.add_response(json=series_payload())

    response = ValetClient(settings(tmp_path)).fetch_series("FXUSDCAD", use_cache=False)

    assert response.observations[0].series == "FXUSDCAD"


def test_malformed_api_response_handling(httpx_mock: HTTPXMock, tmp_path) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(json={"unexpected": []})

    with pytest.raises(ValetResponseError):
        ValetClient(settings(tmp_path)).fetch_series("FXUSDCAD")
