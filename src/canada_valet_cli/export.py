from __future__ import annotations

from pathlib import Path

import pandas as pd

from canada_valet_cli.exceptions import ValetExportError
from canada_valet_cli.models import Observation


def observations_to_frame(observations: list[Observation]) -> pd.DataFrame:
    """Convert normalized observations to a tidy pandas DataFrame."""
    return pd.DataFrame([observation.model_dump(mode="json") for observation in observations])


def observations_to_csv(observations: list[Observation]) -> str:
    """Render observations as CSV text."""
    return observations_to_frame(observations).to_csv(index=False)


def observations_to_json(observations: list[Observation]) -> str:
    """Render observations as JSON records."""
    return observations_to_frame(observations).to_json(orient="records", indent=2)


def write_observations(
    observations: list[Observation],
    output_path: str | Path,
    output_format: str,
) -> Path:
    """Write observations to CSV, JSON, or Parquet."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = observations_to_frame(observations)
    if output_format == "csv":
        frame.to_csv(path, index=False)
    elif output_format == "json":
        frame.to_json(path, orient="records", indent=2)
    elif output_format == "parquet":
        try:
            import pyarrow  # noqa: F401
        except ImportError as exc:
            raise ValetExportError(
                "Parquet export requires pyarrow. Install with: "
                "pip install 'canada-valet-cli[parquet]'"
            ) from exc
        frame.to_parquet(path, index=False)
    else:
        raise ValetExportError(f"Unsupported export format: {output_format}")
    return path
