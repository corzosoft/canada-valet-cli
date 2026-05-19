# Caching

`canada-valet-cli` caches JSON API responses in the user cache directory selected by `platformdirs`.

Why caching matters:

- Reduces repeated calls for data that changes slowly.
- Makes local exploration faster.
- Supports polite use of public infrastructure.

Defaults:

- TTL: 24 hours
- Cache key: endpoint path plus query parameters

Commands:

```bash
valet cache info
valet cache clear --yes
```
