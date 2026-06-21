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

Local synthetic API endpoints:

```text
GET  http://localhost:8000/api/sync/status
POST http://localhost:8000/api/sync/run
GET  http://localhost:8000/api/meta/filters
GET  http://localhost:8000/api/reports/contacts
GET  http://localhost:8000/api/reports/contacts/analytics
GET  http://localhost:8000/api/reports/abc
GET  http://localhost:8000/api/reports/rfm
GET  http://localhost:8000/api/reports/stale-deals
GET  http://localhost:8000/api/reports/deal-cycle
GET  http://localhost:8000/api/reports/concentration
GET  http://localhost:8000/api/reports/type-region
```

`POST /api/sync/run` runs only the local synthetic fixture pipeline in an in-memory DuckDB connection. It does not call Bitrix and does not create a local database file.

The report endpoints calculate analytics on demand from normalized local DuckDB tables and synthetic local currency rates. They do not call Bitrix, NBRB, or any external API. Period parameters `date_from` and `date_to` are supported where meaningful.

## Backend Tests

From the backend directory:

```bash
pip install -e ".[dev]"
pytest
```

## Tooling Troubleshooting

If `python3 -m pip --version` fails on Ubuntu/WSL, install Python package tooling on the host distro before running backend checks:

```bash
sudo apt update
sudo apt install python3-pip python3-venv
```

If Docker commands print a WSL integration error, enable Docker Desktop integration for this WSL distro or install/connect a Docker daemon before running `docker compose config`.

## Current Limitations

- The API currently uses an in-memory local synthetic DuckDB dataset.
- No real Bitrix sync, NBRB integration, Parquet writing, persisted analytics tables, authentication, or frontend is implemented.
- Future frontend implementation should use `ui-kits/` as the design-system source; no frontend screens are implemented in this backend milestone.
- Docker Compose currently runs only the backend service.
