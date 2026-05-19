from pytest_httpx import HTTPXMock
from typer.testing import CliRunner

from canada_valet_cli.cli import app
from tests.test_client import group_payload, series_payload

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Unofficial CLI" in result.output


def test_cli_series_outputs_table(httpx_mock: HTTPXMock, tmp_path) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(json=series_payload())
    result = runner.invoke(
        app,
        [
            "series",
            "FXUSDCAD",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-31",
            "--no-cache",
            "--cache-ttl",
            "1",
            "--base-url",
            "https://www.bankofcanada.ca/valet/",
        ],
    )

    assert result.exit_code == 0
    assert "FXUSDCAD" in result.output


def test_cli_group_json_output(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=group_payload())

    result = runner.invoke(app, ["group", "FX_RATES_DAILY", "--format", "json", "--no-cache"])

    assert result.exit_code == 0
    assert "FXEURCAD" in result.output


def test_cli_export_writes_file(httpx_mock: HTTPXMock, tmp_path) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(json=series_payload())
    output = tmp_path / "fx.csv"

    result = runner.invoke(
        app,
        ["export", "FXUSDCAD", "--format", "csv", "--out", str(output), "--no-cache"],
    )

    assert result.exit_code == 0
    assert output.exists()
