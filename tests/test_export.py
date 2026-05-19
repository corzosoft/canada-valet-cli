from __future__ import annotations

import builtins
from datetime import date

import pytest

from canada_valet_cli.exceptions import ValetExportError
from canada_valet_cli.export import observations_to_csv, observations_to_json, write_observations
from canada_valet_cli.models import Observation


def observations() -> list[Observation]:
    return [Observation(date=date(2024, 1, 2), series="FXUSDCAD", label="USD/CAD", value="1.33")]


def test_export_to_csv(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = write_observations(observations(), tmp_path / "fx.csv", "csv")

    assert path.read_text(encoding="utf-8").startswith("date,series,label,value,group")


def test_export_to_json(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = write_observations(observations(), tmp_path / "fx.json", "json")

    assert "FXUSDCAD" in path.read_text(encoding="utf-8")
    assert "FXUSDCAD" in observations_to_json(observations())
    assert "date,series" in observations_to_csv(observations())


def test_parquet_missing_dependency_error(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "pyarrow":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ValetExportError, match="Parquet export requires pyarrow"):
        write_observations(observations(), tmp_path / "fx.parquet", "parquet")
