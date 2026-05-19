# Examples

Fetch USD/CAD daily exchange rates:

```bash
valet series FXUSDCAD --start 2024-01-01 --end 2024-12-31
```

Fetch daily FX group data:

```bash
valet group FX_RATES_DAILY --start 2024-01-01 --end 2024-01-31
```

Search metadata:

```bash
valet search "exchange rate"
valet search "overnight rate"
```

Export:

```bash
valet export FXUSDCAD --format csv --out fx.csv
valet export FXUSDCAD --format json --out fx.json
valet export FXUSDCAD --format parquet --out fx.parquet
```
