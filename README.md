# Canada Valet CLI

[![CI](https://github.com/corzosoft/canada-valet-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/corzosoft/canada-valet-cli/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](pyproject.toml)

A clean unofficial CLI for Bank of Canada Valet API data.

`canada-valet-cli` is an unofficial open-source command-line tool for fetching, caching, validating, searching, and exporting public Bank of Canada Valet API data.

Data source: Bank of Canada Valet API.

This project is unofficial and is not affiliated with, endorsed by, or sponsored by the Bank of Canada. Bank of Canada is attributed as the source of public data. This project does not use Bank of Canada logos or wordmarks.

This tool is for data access and educational/analytical use only. It does not provide financial, investment, trading, legal, or tax advice.

## Install

```bash
pip install canada-valet-cli
```

For Parquet export:

```bash
pip install "canada-valet-cli[parquet]"
```

Local development:

```bash
git clone https://github.com/corzosoft/canada-valet-cli.git
cd canada-valet-cli
pip install -e ".[dev,parquet]"
```

## Quick Examples

```bash
valet series FXUSDCAD --start 2024-01-01 --end 2024-12-31
valet group FX_RATES_DAILY --start 2024-01-01 --end 2024-01-31
valet search "exchange rate"
valet metadata FXUSDCAD
valet export FXUSDCAD --format csv --out fx.csv
valet validate FXUSDCAD
valet cache info
valet doctor
```

## Commands

### Fetch a series

```bash
valet series FXUSDCAD --start 2024-01-01 --end 2024-01-31 --format table
valet series FXUSDCAD --format json
valet series FXUSDCAD --format csv --out fx.csv
```

### Fetch a group

```bash
valet group FX_RATES_DAILY --start 2024-01-01 --end 2024-01-31
valet group FX_RATES_DAILY --format json
valet group FX_RATES_DAILY --format csv --out fx_group.csv
```

### Search and metadata

```bash
valet list series
valet list groups
valet search "overnight rate"
valet metadata FXUSDCAD
```

### Export

```bash
valet export FXUSDCAD --start 2024-01-01 --end 2024-12-31 --format csv --out fx.csv
valet export FXUSDCAD --format json --out fx.json
valet export FXUSDCAD --format parquet --out fx.parquet
```

Parquet export requires `pyarrow`. Install with:

```bash
pip install "canada-valet-cli[parquet]"
```

### Validate

```bash
valet validate FXUSDCAD --start 2024-01-01 --end 2024-12-31
```

Validation checks include empty responses, missing dates, duplicate dates, missing values, non-numeric values, unexpected gaps, stale datasets, and API response shape changes.

## Caching

Responses are cached locally using `platformdirs`. The default cache TTL is 24 hours.

Caching reduces repeated API calls, improves local workflows, and follows the Bank of Canada guidance to use caching and retry/backoff when possible.

```bash
valet cache info
valet cache clear --yes
```

Use `--no-cache` to bypass cache for observation commands. Use `--cache-ttl HOURS` to override the TTL for a command.

## Retry And Backoff

HTTP requests use retry with exponential backoff for transient transport failures. This avoids rapid repeated failed requests and supports polite API usage.

## Base URL Override

The default base URL is:

```text
https://www.bankofcanada.ca/valet/
```

Override with an environment variable:

```bash
export VALET_BASE_URL="https://www.bankofcanada.ca/valet/"
```

Or per command:

```bash
valet series FXUSDCAD --base-url https://www.bankofcanada.ca/valet/
```

## Output Shape

Observations are normalized into tidy records:

```text
date,series,label,value
```

Group results include the group name:

```text
date,series,label,value,group
```

## Development

```bash
pip install -e ".[dev,parquet]"
ruff check .
ruff format --check .
pytest
```

Tests mock all HTTP calls and do not call the live Bank of Canada API.

## Roadmap

- Support XML output.
- Support more metadata exploration.
- Add shell completion.
- Add SQL export.
- Add DuckDB export.
- Add Power BI examples.
- Add Azure Function scheduled ingestion example.

## Legal And Attribution

Data source: Bank of Canada Valet API.

This project is unofficial and is not affiliated with, endorsed by, or sponsored by the Bank of Canada. Bank of Canada is attributed as the source of public data. This project does not use Bank of Canada logos or wordmarks.

This tool is for data access and educational/analytical use only. It does not provide financial, investment, trading, legal, or tax advice.
