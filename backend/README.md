# Backend

FastAPI backend scaffold for the Bitrix sales analytics MVP.

## Structure

```text
app/
  main.py          # FastAPI application and current routes
  core/config.py  # Environment-based settings
  domain/
    models.py             # Pydantic domain snapshots for allowed MVP entities
    contact_selection.py  # Pure analytical contact selection logic
  storage/
    schema.py             # Minimal DuckDB schema initializer
tests/
  test_health.py             # Health endpoint coverage
  test_contact_selection.py  # Domain selection coverage
  test_storage_schema.py     # DuckDB schema coverage
  test_synthetic_dataset.py  # Synthetic fixture validation
  fixtures/
    synthetic_dataset.py     # Test-only dataset for future integration coverage
```

Future Bitrix sync, normalization, analytics, production storage migrations, authentication, and report API modules are intentionally not implemented yet.

## Local Commands

Install backend runtime and development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run locally after installing dependencies:

```bash
uvicorn app.main:app --reload
```

Run through Docker Compose from the repository root:

```bash
docker compose up --build backend
```

## Environment

Settings use `pydantic-settings` with the `APP_` environment prefix for application values and placeholder-safe defaults. The Bitrix webhook placeholder is read from `BITRIX_WEBHOOK_URL`. Real Bitrix webhook URLs and secrets must stay in local environment files or deployment secrets and must not be committed.
