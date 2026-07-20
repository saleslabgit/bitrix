# Backend

FastAPI backend scaffold for the Bitrix sales analytics MVP.

## Structure

```text
app/
  main.py          # FastAPI application and current routes
  local_database.py # Lazy configured DuckDB connection boundary
  api/
    models.py      # Pydantic response models for local read endpoints
  bitrix/
    allowlist.py   # Central allowed Bitrix field lists
    client.py      # Read-only Bitrix REST client
    discovery.py   # Safe metadata discovery service
    ingestion.py   # Manual Bitrix raw ingestion orchestration
    transform.py   # Bitrix payload to domain snapshot transforms
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
    connection.py         # Configured DuckDB data-dir/path connection helper
    schema.py             # DuckDB schema initializer
    loaders.py            # Synthetic raw table loading helpers
    snapshots.py          # Allowlisted raw Parquet snapshot writer
    status.py             # Dataset run and active dataset metadata helpers
tests/
  test_health.py             # Health endpoint coverage
  test_contact_selection.py  # Domain selection coverage
  test_storage_schema.py     # DuckDB schema coverage
  test_synthetic_dataset.py  # Synthetic fixture validation
  test_pipeline.py           # Storage-backed local pipeline coverage
  test_analytics.py          # Storage-backed local analytics coverage
  test_api_local.py          # Local read API coverage through endpoint functions
  test_api_bitrix.py         # Bitrix API no-credentials safety coverage
  test_bitrix_client.py      # Read-only client, allowlist, pagination coverage
  test_bitrix_discovery.py   # Metadata discovery coverage
  test_bitrix_ingestion.py   # Mocked manual ingestion coverage
  fixtures/
    synthetic_dataset.py     # Compatibility re-export for test fixture imports
```

Manual read-only Bitrix ingestion is implemented as a backend/data boundary with mocked tests. Runtime uses a configured local DuckDB store, successful synthetic/Bitrix runs activate the local dataset, and allowlisted raw Parquet snapshots can be written under the local data directory. A simple env-configured single-user auth gate protects `/api/*` routes when enabled. NBRB integration, persisted analytics tables, production storage migrations, and frontend-facing report API hardening are intentionally not implemented yet.

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
GET /api/auth/session
POST /api/auth/login
POST /api/auth/logout
POST /api/sync/run
GET /api/sync/status
GET /api/datasets/status
GET /api/meta/filters
GET /api/reports/contacts
GET /api/reports/contacts/analytics
GET /api/reports/deals/analytics
GET /api/reports/abc/analytics
GET /api/reports/kev-conversion/analytics
GET /api/reports/abc
GET /api/reports/rfm
GET /api/reports/stale-deals
GET /api/reports/deal-cycle
GET /api/reports/concentration
GET /api/reports/type-region
GET /api/reports/types-regions
```

When `APP_AUTH_ENABLED=true`, every `/api/*` endpoint except `/api/auth/*`
requires the signed HttpOnly browser session cookie. `/health` remains public.
These endpoints use the configured local DuckDB dataset. `POST /api/sync/run`
loads the synthetic fixture, writes allowlisted raw snapshots under
`APP_DATA_DIR`, and activates it as the local dataset. It is not a real Bitrix
sync. Report endpoints calculate local analytics on demand and do not call
Bitrix, NBRB, or external APIs.

Deal ingestion allowlists the approved checkbox `UF_CRM_1716895716` and stores
only `kev_held`; universal CRM exposes this deal field as
`ufCrm_1716895716`, and blank/missing means false. Schema initialization
additively migrates existing raw/normalized deal tables. The KEV conversion
endpoint counts only closed won/lost deals and filters periods inclusively by
`closed_at`.

Manual Bitrix endpoints after starting the backend:

```text
GET /api/bitrix/discovery
POST /api/bitrix/sync/run
GET /api/bitrix/sync/status
```

These endpoints require `BITRIX_WEBHOOK_URL` for live calls. Without credentials
they return safe error/status payloads and tests still pass.

Run through Docker Compose from the repository root:

```bash
docker compose up --build backend
```

## Environment

Settings use `pydantic-settings` with the `APP_` environment prefix for application values and placeholder-safe defaults.

Storage environment variables:

```text
APP_DATA_DIR=data
APP_DUCKDB_PATH=
```

Blank `APP_DUCKDB_PATH` uses `APP_DATA_DIR/analytics.duckdb`. DuckDB files and
snapshot Parquet files are generated local artifacts and must not be committed.

Bitrix environment variables:

```text
BITRIX_WEBHOOK_URL=
BITRIX_CONTACT_TYPE_FIELD=
BITRIX_PAGE_SIZE=50
```

Real Bitrix webhook URLs and secrets must stay in local environment files or deployment secrets and must not be committed.

Auth environment variables:

```text
APP_AUTH_ENABLED=false
APP_AUTH_USERNAME=
APP_AUTH_PASSWORD=
APP_AUTH_SESSION_SECRET=
APP_AUTH_SESSION_TTL_SECONDS=86400
APP_AUTH_COOKIE_SECURE=false
```

Auth is disabled by default. If `APP_AUTH_ENABLED=true`, username, password,
and session secret are required; missing values fail closed at settings load.
The password and session secret must come from local environment or deployment
secrets only. The backend validates credentials with constant-time comparison,
sets an HttpOnly SameSite=Lax signed session cookie, and clears it on logout.
Set `APP_AUTH_COOKIE_SECURE=true` for HTTPS deployments.

Deal funnels are loaded only by explicit manual refresh through read-only
`crm.category.list`. Stages are resolved by exact `(stage_id, category_id)`;
report endpoints query local data only.

Contacts analytics accepts `average_check_usd` and `average_cycle_days` as
stable sort fields. Null averages remain at the end in either direction and
contact ID is the deterministic tie-breaker. Contacts and Deals filtered
summaries are calculated before pagination.
