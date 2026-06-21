# Backend

FastAPI backend scaffold for the Bitrix sales analytics MVP.

## Structure

```text
app/
  main.py          # FastAPI application and current routes
  core/config.py  # Environment-based settings
tests/
  test_health.py  # Health endpoint coverage
```

Future Bitrix sync, normalization, analytics, storage, authentication, and report API modules are intentionally not implemented in this task.

## Local Commands

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
