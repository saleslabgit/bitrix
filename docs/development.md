# Development

## Requirements

- Python 3.12.
- Docker with Docker Compose.

## Environment Policy

Use `.env.example` as a placeholder template only. Real `.env` files, Bitrix webhook URLs, secrets, raw data, local databases, Parquet snapshots, and CSV exports must not be committed.

Default display timezone is `Europe/Minsk`. Store future persisted timestamps in UTC.

## Docker Compose

Validate Compose configuration:

```bash
docker compose config
```

Run the backend:

```bash
docker compose up --build backend
```

Backend health endpoint:

```text
GET http://localhost:8000/health
```

## Backend Tests

From the backend directory:

```bash
pytest
```

## Current Limitations

- Only the health endpoint is implemented.
- No Bitrix, NBRB, DuckDB, Parquet, analytics, authentication, or report APIs are implemented.
- Frontend implementation is blocked until the approved design system is available.
- Docker Compose currently runs only the backend service.
