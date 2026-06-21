# Architecture

## Target Flow

```text
Bitrix CRM -> read-only extraction -> raw local layer -> normalization -> analytics tables -> backend API -> web interface
```

## Layers

### Bitrix Read-Only Extraction

Bitrix is used only as a read-only source. Current sync code requests explicit
allowlisted fields and must not use `select: ["*"]`. The MVP must not download
phones, emails, addresses, messengers, requisites, comments, files, activity
fields, or arbitrary non-allowlisted fields.

Current module boundary: `backend/app/bitrix/`.

### Raw Local Layer

Stores data in the form received from Bitrix for allowed entities only: contacts, deals, deal-contact links, and required stage dictionaries. Raw exports and local data files must not be committed.

### Normalization

Transforms Bitrix identifiers, stage semantics, contact type mapping, region mapping, deal-contact selection, timestamps, and currencies into stable local representations. Contact type priorities and region rules are configuration or data, not hardcoded business constants.

### Analytics Tables

Stores reproducible outputs for reports: revenue, estimated profit, ABC, RFM, reactivation, type and region aggregates, deal-cycle metrics, stale deals, and concentration. Revenue and ABC/RFM are based only on won deals.

Current local implementation calculates these outputs on demand from normalized DuckDB tables and synthetic local currency rates. Persisted analytics tables are still future work.

### Backend API

FastAPI exposes health, local synthetic sync, Bitrix discovery/manual sync,
metadata, contact summary, and local analytics report endpoints. Current report
endpoints read only local DuckDB data and do not call Bitrix or external
currency services.

### Web Interface

The frontend will consume the backend API after the design system is approved. It must follow `SPEC.md` and must not query Bitrix directly.

## Current Implementation

The repository currently contains a local backend package:

- `backend/app/main.py` creates the FastAPI app and `/health`.
- `backend/app/core/config.py` defines environment-based settings.
- `backend/app/bitrix/` contains the read-only Bitrix client, field allowlists, metadata discovery, transforms, and manual ingestion orchestration.
- `backend/app/pipeline/` loads and normalizes the synthetic fixture.
- `backend/app/reports/local.py` provides local metadata and contact summary helpers.
- `backend/app/reports/analytics.py` provides local USD conversion, contact analytics, ABC, RFM, stale-deal, deal-cycle, concentration, and type/region calculations.
- `backend/tests/` verifies health, schema, synthetic fixture shape, normalization, analytics, and local API endpoints.

The first manual Bitrix extraction boundary is implemented and covered with
mocked tests. Live Bitrix validation, NBRB integration, persisted analytics
tables, production dataset activation, authentication, and frontend screens are
not implemented yet.
