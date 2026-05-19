# Usage

Install:

```bash
pip install canada-valet-cli
```

Commands:

```bash
valet series SERIES_NAME [--start YYYY-MM-DD] [--end YYYY-MM-DD]
valet group GROUP_NAME [--start YYYY-MM-DD] [--end YYYY-MM-DD]
valet metadata NAME
valet list series
valet list groups
valet search QUERY
valet export SERIES_OR_GROUP --format csv|json|parquet --out PATH
valet validate SERIES_NAME
valet cache info
valet cache clear --yes
valet doctor
```

Global API behavior:

- Default base URL: `https://www.bankofcanada.ca/valet/`
- Environment override: `VALET_BASE_URL`
- Per-command override: `--base-url`
- Default cache TTL: 24 hours
