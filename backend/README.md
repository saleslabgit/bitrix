# Backend

FastAPI backend scaffold for the Bitrix sales analytics MVP.

## Structure

```text
app/
  main.py          # FastAPI application and current routes
  local_database.py # In-memory DuckDB connection for the local synthetic milestone
  api/
    models.py      # Pydantic response models for local read endpoints
  core/config.py  # Environment-based settings
  domain/
    models.py             # Pydantic domain snapshots for allowed MVP entities
    contact_selection.py  # Pure analytical contact selection logic
  pipeline/
    synthetic_dataset.py  # Synthetic allowed local dataset
    synthetic.py          # Local synthetic pipeline orchestration
    normalization.py      # Raw-to-normalized local transforms
  reports/
    analytics.py          # Local analytics calculations over normalized DuckDB data
    local.py              # Read helpers for local report endpoints
  storage/
    schema.py             # Minimal DuckDB schema initializer
    loaders.py            # Synthetic raw table loading helpers
tests/
  test_health.py             # Health endpoint coverage
  test_contact_selection.py  # Domain selection coverage
  test_storage_schema.py     # DuckDB schema coverage
  test_synthetic_dataset.py  # Synthetic fixture validation
  test_pipeline.py           # Storage-backed local pipeline coverage
  test_analytics.py          # Storage-backed local analytics coverage
  test_api_local.py          # Local read API coverage through endpoint functions
  fixtures/
    synthetic_dataset.py     # Compatibility re-export for test fixture imports
```

Future Bitrix sync, NBRB integration, persisted analytics tables, production storage migrations, authentication, and frontend-facing report API hardening are intentionally not implemented yet.

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

Local synthetic pipeline endpoints after starting the backend:

```text
POST /api/sync/run
GET /api/sync/status
GET /api/meta/filters
GET /api/reports/contacts
GET /api/reports/contacts/analytics
GET /api/reports/abc
GET /api/reports/rfm
GET /api/reports/stale-deals
GET /api/reports/deal-cycle
GET /api/reports/concentration
GET /api/reports/type-region
GET /api/reports/types-regions
```

These endpoints use an in-memory DuckDB dataset and synthetic data only. `POST /api/sync/run` is not a real Bitrix sync. Report endpoints calculate local analytics on demand and do not call Bitrix, NBRB, or external APIs.

Run through Docker Compose from the repository root:

```bash
docker compose up --build backend
```

## Environment

Settings use `pydantic-settings` with the `APP_` environment prefix for application values and placeholder-safe defaults. The Bitrix webhook placeholder is read from `BITRIX_WEBHOOK_URL`. Real Bitrix webhook URLs and secrets must stay in local environment files or deployment secrets and must not be committed.
