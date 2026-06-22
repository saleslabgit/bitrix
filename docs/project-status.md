# Project Status

## Current Phase

Backend/data milestone for the Bitrix sales analytics MVP: local analytics, read-only Bitrix ingestion boundary, and persistent local DuckDB storage with active dataset metadata.

## Done In This Task

- Created a minimal FastAPI backend.
- Added `GET /health`.
- Added pytest coverage for the health endpoint.
- Added Docker Compose wiring for the backend service.
- Added placeholder environment configuration.
- Added repository hygiene rules in `.gitignore`.
- Created the initial documentation backbone.
- Added Pydantic domain snapshots for allowed MVP entities.
- Added pure analytical contact selection logic.
- Added focused unit tests for contact selection.
- Added the future integration fixture plan.
- Added a minimal DuckDB schema initializer for allowed MVP scaffold tables.
- Added a synthetic integration fixture dataset for future normalization and analytics tests.
- Added storage schema and fixture validation tests.
- Added local synthetic fixture loading into DuckDB raw tables.
- Added normalized contacts and normalized deals tables.
- Added contact type/region normalization, stage status representation, and analytical contact assignment.
- Added local synthetic pipeline status storage.
- Added minimal read API endpoints for local synthetic status, pipeline run, filters, and contact summaries.
- Added storage-backed pipeline and API tests.
- Added deterministic local USD conversion helpers over synthetic `currency_rates`.
- Added contact analytics with won revenue USD, estimated profit USD, deal counts, dates, and sales flags.
- Added ABC full-period vs last-12-month comparison with `Нет продаж` handling.
- Added RFM scoring, segment output, and reactivation signal.
- Added deal-cycle metrics and stale open deal detection.
- Added revenue concentration, type analytics, region analytics, and type-region matrix rows.
- Added typed FastAPI report endpoints for the new local analytics outputs.
- Added storage-backed analytics and report API coverage.
- Added safe Bitrix settings for webhook URL, contact type field, and page size.
- Added a read-only Bitrix REST client with allowlisted methods, pagination, and safe errors.
- Added centralized Bitrix field allowlists for contacts, deals, links, and stages.
- Added Bitrix metadata discovery for contact/deal fields and configured contact type field presence.
- Added manual Bitrix raw ingestion into existing DuckDB raw tables with existing normalization.
- Added typed backend endpoints for Bitrix discovery, manual sync run, and manual sync status.
- Added mocked Bitrix boundary tests for allowlists, pagination, discovery, ingestion, idempotency, and no-credentials safety.
- Added configurable local DuckDB storage with `APP_DATA_DIR` and `APP_DUCKDB_PATH`.
- Added lazy shared backend connection initialization for configured runtime storage.
- Added dataset run metadata and active dataset metadata tables.
- Added transaction-backed activation for successful synthetic and manual Bitrix runs.
- Added safe failed-run handling so handled Bitrix failures do not commit partial replacements or deactivate the previous successful dataset.
- Added allowlisted raw Parquet snapshots for successful local runs.
- Added `GET /api/datasets/status` for active dataset and latest run metadata.
- Added tests for persistent temp DuckDB storage, schema idempotency on file storage, snapshots, activation, failed Bitrix run safety, and safe status output.
- Confirmed live Bitrix contact type field `UF_CRM_1595304971232` exists in metadata.
- Corrected manual Bitrix sync to build deal-contact links locally from downloaded deal fields instead of mass-calling `crm.deal.contact.items.get`.
- Ran the first successful live read-only manual Bitrix sync with active local dataset status.
- Added a local-only safe dataset quality profile helper and `GET /api/datasets/profile`.
- Profiled the first active live Bitrix dataset from local DuckDB aggregates without Bitrix calls.

## Intentionally Not Done

- NBRB currency integration.
- Persisted analytics output tables.
- Full staging-table swap mechanics beyond the current transaction-backed single active table set.
- Production migration tooling.
- Authentication.
- Frontend screens, UI components, design tokens, or Storybook.
- CI and production deployment.

## Facts

- Bitrix is a read-only data source.
- Main analytics entity is the contact.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
- All financial analytics are normalized to USD.
- Frontend implementation waits for the approved design system.

## Assumptions

- Python 3.12, FastAPI, Pydantic v2, Polars, DuckDB, Parquet, and pytest are the target backend stack.
- Docker Compose is the default local runtime entry point.

## Unknowns

- Real Bitrix webhook URL remains local secret and is not documented.
- Actual contact types, priorities, and region mapping.
- Actual pipelines, stages, and currencies in Bitrix.
- Final design-system tokens and component decisions.
- Deployment host, HTTPS setup, and backup destination.
- Final production storage layout, migration strategy, and whether a full staging-table swap will be required.
- Final frontend response-shape needs beyond the current compact local report API.

## Next Likely Steps

Confirm business mappings for observed contact type raw values, configure active contact type/priority/region rules, rerun local normalization from persisted data, then plan NBRB currency integration.
