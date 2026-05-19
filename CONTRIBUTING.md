# Contributing

Contributions are welcome.

Guidelines:

- Use only public Bank of Canada Valet API data.
- Do not use Bank of Canada logos, icons, wordmarks, or official-looking design.
- Do not imply affiliation, sponsorship, approval, or endorsement by the Bank of Canada.
- Do not add scraping of private pages or mechanisms that bypass public API limits.
- Keep tests mocked. Unit tests must not call the live API.
- Keep commands small, typed, and easy to understand.

Before opening a pull request:

```bash
ruff check .
ruff format --check .
pytest
```
