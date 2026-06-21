# Development

## Requirements

- Python 3.12.
- Docker with Docker Compose.

## Environment Policy

Use `.env.example` as a placeholder template only. Real `.env` files, Bitrix webhook URLs, secrets, raw data, local databases, Parquet snapshots, and CSV exports must not be committed.

Default display timezone is `Europe/Minsk`. Store future persisted timestamps in UTC.

Bitrix settings:

```text
APP_DATA_DIR=data                  # local generated storage directory
APP_DUCKDB_PATH=                   # optional override; blank uses APP_DATA_DIR/analytics.duckdb
BITRIX_WEBHOOK_URL=              # secret read-only webhook base URL; blank disables live calls
BITRIX_CONTACT_TYPE_FIELD=       # optional discovered contact type field code
BITRIX_PAGE_SIZE=50              # optional Bitrix list page size, max 50
```

Tests and regular local development do not require live Bitrix credentials.
Generated DuckDB files and Parquet snapshots live under `APP_DATA_DIR` by
default and are gitignored.

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

Manual Bitrix backend endpoints:

```text
GET  http://localhost:8000/api/datasets/status
GET  http://localhost:8000/api/bitrix/discovery
POST http://localhost:8000/api/bitrix/sync/run
GET  http://localhost:8000/api/bitrix/sync/status
```

`GET /api/datasets/status` reports the active local dataset and latest run
metadata with safe messages, counts, UTC timestamps, and relative snapshot
identifiers. It does not expose raw rows, secrets, webhook URLs, file contents,
or local absolute paths.

`GET /api/bitrix/discovery` reads Bitrix field metadata and reports whether
`BITRIX_CONTACT_TYPE_FIELD` exists. Use it to choose the contact type field
code before running real ingestion. The response does not include webhook values
or contact/deal field values.

`POST /api/bitrix/sync/run` is a manual read-only ingestion entry point. It
loads allowed contacts, deals, deal-contact links, and stages into local raw
DuckDB tables, then runs existing normalization. Successful runs activate the
new local dataset. Handled failed runs do not activate and do not commit partial
raw/normalized replacements. If `BITRIX_WEBHOOK_URL` is missing, it returns a
safe error status and does not call Bitrix.

Safe local operator flow:

```text
configure .env -> docker compose up --build backend -> run discovery -> set BITRIX_CONTACT_TYPE_FIELD -> run manual Bitrix sync -> read /api/datasets/status and reports
```

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

- The API uses a configured local DuckDB connection. Default runtime storage is persistent under `APP_DATA_DIR`; tests can still use in-memory or temporary connections.
- Dataset activation is transaction-backed for the current single-table-set storage model, not a full staging-table swap system.
- No NBRB integration, persisted analytics tables, authentication, scheduler, or frontend is implemented.
- Future frontend implementation should use `ui-kits/` as the design-system source; no frontend screens are implemented in this backend milestone.
- Docker Compose currently runs only the backend service.
