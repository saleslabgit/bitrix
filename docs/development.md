# Development

## Requirements

- Python 3.12.
- Node.js 20+ and npm for frontend development.
- Docker with Docker Compose.

## Environment Policy

Use `.env.example` as a placeholder template only. Docker Compose also loads a
local `.env` file when present. Real `.env` files, Bitrix webhook URLs, secrets,
raw data, local databases, Parquet snapshots, and CSV exports must not be
committed.

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

Run the full local stack:

```bash
docker compose up --build
```

Local URLs:

```text
Backend:  http://localhost:8000
Frontend: http://localhost:5173
```

Docker Compose only starts the backend and frontend services. It intentionally
does not call Bitrix, load NBRB rates, or refresh local data during startup.
Existing `data/analytics.duckdb` storage is reused when present, and generated
local databases remain gitignored.

Simple local app flow:

1. Run `docker compose up --build`.
2. Open `http://localhost:5173`.
3. If an active local dataset exists, the Contacts table loads normally.
4. If the frontend says `Локальная база не подготовлена.`, click
   `Обновить из Bitrix`.
5. Wait for the manual read-only refresh to finish; it can take several
   minutes. The backend syncs allowed Bitrix data, applies approved contact
   type rules, reruns local normalization, loads NBRB rates, and then the
   Contacts screen refetches dataset status, filters, and rows.

The Compose frontend service runs the Vite dev server on `0.0.0.0:5173` and
sets `VITE_BACKEND_URL=http://backend:8000`, so frontend `/api` and `/health`
requests are proxied to the backend service over the Compose network. It also
mounts `./ui-kits` read-only at `/ui-kits` so Vite can resolve the design-system
CSS imported from `frontend/src/styles.css`.

Run only the backend when needed:

```bash
docker compose up --build backend
```

Backend health endpoint:

```text
GET http://localhost:8000/health
```

Full-stack verification checklist:

- `http://localhost:8000/health` returns backend health.
- `http://localhost:5173` opens the frontend.
- The Contacts table loads when an active local dataset exists.
- With no active dataset, the Contacts screen shows the manual refresh panel.
- Search, filters, and pagination respond.
- If the frontend shows an API error, check `GET http://localhost:8000/api/datasets/status` and confirm an active dataset is available.

## Frontend

The first frontend milestone lives under `frontend/` and implements only the
Contacts report screen.

Install dependencies:

```bash
cd frontend
npm install
```

Run the Vite dev server:

```bash
npm run dev
```

Build the frontend:

```bash
npm run build
```

The dev server proxies `/api` and `/health` to the local backend. Default
backend URL:

```text
http://localhost:8000
```

Override the dev proxy target when needed:

```bash
VITE_BACKEND_URL=http://localhost:8000 npm run dev
```

In Docker Compose this same setting is overridden to:

```text
VITE_BACKEND_URL=http://backend:8000
```

The app can also call a non-same-origin API in built/static mode by setting:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Frontend endpoints used by the Contacts screen:

```text
GET /api/reports/contacts/analytics
GET /api/meta/filters
GET /api/datasets/status
POST /api/local/refresh-data
```

The Contacts screen uses USD analytics fields from `/api/reports/contacts/analytics`
as its primary financial metrics. It does not present original-currency sums as
converted revenue. The endpoint supports exact `contact_id` filtering plus
deal creation date filtering via `deal_created_from` / `deal_created_to`,
which filters local `normalized_deals.created_at` inclusively and separately
from the existing report-date `date_from` / `date_to` parameters. The endpoint
also supports allowlisted `sort` and `order` query parameters for stable
server-side sorting before pagination. Contact analytics rows include USD budget breakdown fields:
`budget_usd` for all assigned deals, `budget_in_work_usd` for open assigned
deals, `lost_budget_usd` for lost assigned deals, while `revenue_usd` remains
won-only and `estimated_profit_usd` remains `revenue_usd * 0.50`. The frontend
uses those local parameters and fields for the full-width verification table and
still does not call Bitrix directly. Contacts UI state is persisted locally in
browser storage under `bitrix-sales.contacts.v1`; it stores filter/sort/page
settings only, not backend rows, secrets, or raw data.

The frontend must continue to read only local backend endpoints. It must not
call Bitrix directly or display forbidden personal fields such as phone, email,
address, messengers, comments, files, requisites, or arbitrary raw Bitrix
fields.

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
GET  http://localhost:8000/api/datasets/profile
GET  http://localhost:8000/api/internal/diagnostics/contacts/{contact_id}/deal-links
GET  http://localhost:8000/api/internal/diagnostics/contacts/{contact_id}/explicit-deals?deal_ids=...
POST http://localhost:8000/api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-deals
POST http://localhost:8000/api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-explicit-deals?deal_ids=...
POST http://localhost:8000/api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-item-deals?deal_ids=...
POST http://localhost:8000/api/internal/reconciliation/contacts/{contact_id}/explicit-deals?deal_ids=...
POST http://localhost:8000/api/local/refresh-data
GET  http://localhost:8000/api/bitrix/discovery
POST http://localhost:8000/api/bitrix/sync/run
GET  http://localhost:8000/api/bitrix/sync/status
```

`POST /api/local/refresh-data` is the UI-facing operator endpoint for the full
manual local refresh. It builds the Bitrix client from environment settings,
runs the existing read-only manual Bitrix ingestion, applies the approved
contact type rules, reruns local normalization, loads NBRB rates for raw deals,
and returns only safe status, counts, and messages. It does not expose webhook
values, secrets, raw rows, generated file contents, or local absolute paths. It
does not call Bitrix write methods.

`GET /api/datasets/status` reports the active local dataset and latest run
metadata with safe messages, counts, UTC timestamps, and relative snapshot
identifiers. It does not expose raw rows, secrets, webhook URLs, file contents,
or local absolute paths.

`GET /api/datasets/profile` reports safe local-only aggregate data quality
metrics for the configured DuckDB dataset. It includes dataset status, expected
table presence, snapshot count, contact type raw value counts, missing type
counts, link integrity counts, stage/category ID counts, currency/status counts,
date ranges, active contact type rule coverage, and undefined normalization
counts. It does not call Bitrix and does not expose row samples, contact/deal
names, contact/deal IDs, snapshot paths, local absolute paths, secrets, or raw
personal fields.

`GET /api/internal/diagnostics/contacts/{contact_id}/deal-links` is a
backend-only diagnostic for one contact. It reads local DuckDB data only and
returns safe ID-level/local-allowlisted facts: contact ID and name, raw contact
type, normalized type, region, priority, local linked deal IDs, analytical deal
IDs, per-linked-deal raw existence/status group, and an explanation of where
local counts diverge. It does not call Bitrix and does not expose phones,
emails, addresses, messengers, comments, files, requisites, webhook values,
raw API payloads, or arbitrary custom fields.

`POST /api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-deals`
is an explicitly invoked, targeted read-only Bitrix verification for one
contact. It calls `crm.deal.list` with `filter: {"CONTACT_ID": contact_id}` and
the existing safe deal select list, then compares Bitrix-visible deal IDs with
local raw links and analytical deals. It does not change local data.

`GET /api/internal/diagnostics/contacts/{contact_id}/explicit-deals` compares
one contact with an explicit bounded list of supplied deal IDs. It is local-only
and returns safe ID-level facts: raw deal existence, local linked contact IDs,
whether the supplied contact link exists, analytical contact assignment, and a
per-deal divergence reason.

`POST /api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-explicit-deals`
is an explicitly invoked, targeted read-only Bitrix verification for an
explicit bounded list of supplied deal IDs. It calls `crm.deal.list` with a safe
ID-list filter and `crm.deal.contact.items.get` once per supplied deal ID. It
returns only deal IDs, contact IDs linked to those deals, method names, counts,
and divergence categories. It does not change local data.

`POST /api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-item-deals`
is an explicitly invoked, targeted read-only Bitrix verification for an
explicit bounded list of supplied deal IDs using the universal deal item API. It
calls `crm.item.fields` for `entityTypeId=2`, builds an explicit safe select
list, then calls `crm.item.list` for the supplied deal IDs. It returns only
selected safe field names, returned deal IDs, linked contact IDs, method names,
and completeness flags. It never requests `*` or `fm`.

`POST /api/internal/reconciliation/contacts/{contact_id}/explicit-deals` is the
separate mutating operator helper for explicit-ID reconciliation. It uses the
same bounded read-only Bitrix verification, inserts only confirmed missing
local links for the supplied contact/deal IDs, inserts only allowed safe deal
fields if a supplied confirmed deal is absent locally, reruns normalization, and
records a local dataset run/status. It is not part of normal page load, Docker
startup, scheduled refresh, or the regular manual Bitrix refresh flow.

`GET /api/bitrix/discovery` reads Bitrix field metadata and reports whether
`BITRIX_CONTACT_TYPE_FIELD` exists. Use it to choose the contact type field
code before running real ingestion. The response does not include webhook values
or contact/deal field values.

For contact type mapping preparation, backend helpers can extract enum labels
from `crm.contact.fields` metadata and combine them with local DuckDB aggregate
counts from `raw_contacts`. This metadata-only flow must not call
`crm.contact.list`, `crm.deal.list`, `crm.deal.contact.items.get`, or Bitrix
write methods.

Local live-data readiness helpers:

```text
app.pipeline.local_refresh.apply_approved_rules_and_renormalize
app.pipeline.currency_rates.load_currency_rates_for_raw_deals
```

The local refresh helper replaces `contact_type_rules` with the approved
source-controlled option-ID mapping and reruns normalization from existing
DuckDB raw tables. It does not call Bitrix and does not overwrite raw tables.

The currency-rate helper loads observed local deal currencies from the official
NBRB read-only API into `currency_rates`. It uses the raw deal date range,
historical NBRB currency metadata periods, and daily dynamics rows. Tests mock
the NBRB transport. Live use requires network access but does not require
Bitrix credentials.

`POST /api/bitrix/sync/run` is a manual read-only ingestion entry point. It
loads allowed contacts, deal items, locally reconstructed deal-contact links,
and stages into local raw DuckDB tables, then runs existing normalization.
Successful runs activate the new local dataset. Handled failed runs do not
activate and do not commit partial raw/normalized replacements. If
`BITRIX_WEBHOOK_URL` is missing, it returns a safe error status and does not
call Bitrix.

Normal manual sync uses `crm.item.fields` and `crm.item.list` for deals with an
explicit safe select list. It builds deal-contact links from downloaded item
fields `contactId` and `contactIds`, preserving secondary contacts without
mass-calling `crm.deal.contact.items.get` per deal.

Safe local operator flow:

```text
configure .env -> docker compose up --build -> open frontend -> click Обновить из Bitrix if dataset is not ready -> read reports
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
- NBRB rate loading is implemented for local backend readiness, but no scheduler or automatic refresh exists.
- No persisted analytics tables, authentication, scheduler, or production frontend deployment is implemented.
- Frontend is intentionally limited to the Contacts report screen.
- Docker Compose runs backend and the Vite frontend dev server for local testing.
