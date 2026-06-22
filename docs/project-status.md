# Project Status

## Current Phase

Frontend reporting milestone for the Bitrix sales analytics MVP: local analytics backend plus React/Vite Contacts, Deals, and ABC report screens reading local backend endpoints. The local app has a manual UI-triggered data refresh flow for local testing after `docker compose up --build`; Contacts, Deals, and ABC financial columns use local USD analytics metrics instead of original-currency totals.

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
- Added a metadata-only contact type enum label extraction helper and local aggregate mapping helper.
- Applied the approved live contact type option-ID mapping locally and reran normalization from persisted raw tables.
- Added read-only NBRB currency-rate loading for local USD analytics and loaded rates for the active live dataset.
- Added `frontend/` React/TypeScript/Vite app.
- Implemented the Contacts report screen with search, type/region/status filters, `limit`/`offset` pagination, loading, error, empty states, and a compact dataset status badge.
- Wired the frontend to local backend endpoints only: `/api/reports/contacts`, `/api/meta/filters`, and `/api/datasets/status`.
- Applied the approved `ui-kits/` design tokens and web-app direction to the first frontend screen.
- Added `POST /api/local/refresh-data` for the full manual local refresh flow from the UI.
- Added a Contacts empty-state panel for an unprepared local database with an `Обновить из Bitrix` action.
- The manual refresh flow runs read-only Bitrix ingestion, approved contact type rules, local renormalization, and NBRB rate loading before activating the refreshed dataset.
- Docker Compose intentionally starts services only; it does not auto-call Bitrix or refresh local data. Local DuckDB databases and generated data remain uncommitted.
- Updated the Contacts table to use `/api/reports/contacts/analytics` for `revenue_usd`, `estimated_profit_usd`, deal counts, and latest deal dates.
- Added status filtering support to the contact analytics endpoint so the existing Contacts status filter remains effective.
- Improved manual refresh UX with blocking progress text and a user-facing success message with refreshed counts.
- Added `GET /api/reports/deals/analytics` for local deal-level rows with exact deal ID, status, normalized type/region, inclusive deal creation date filters, allowlisted stable sorting, and pagination.
- Added Deals report UI with sidebar switching, local metadata-backed filters, draft/apply date behavior, Bitrix deal links, USD budget, won-only USD estimated profit, sorting, pagination, loading/error/empty/reset states, and separate browser storage under `bitrix-sales.deals.v1`.
- Refined Deals report with local analytical client search and filtered USD budget/profit totals calculated before pagination.
- Fixed report handling for local datasets with USD deals but no USD rate rows; missing non-USD rates now return a safe service-unavailable error instead of an internal server error.
- Added a frontend favicon so local browser `/favicon.ico` probing no longer returns 404.
- Linked non-zero Contacts deal counters to the Deals report with exact local analytical client ID filters and optional status filters.
- Temporarily hid frontend region filters and region columns while keeping backend region support intact.
- Added won-only filtered Deals revenue total and simplified visible totals labels to `Бюджет`, `Выручка`, and `Прибыль`.
- Added `GET /api/reports/abc/analytics` for paginated local customer ABC analysis with current-period classification, optional comparison-period transitions in the same table, allowlisted filters/sorting, filtered totals, and migration priority counts.
- Added an ABC frontend report with local-only filters, applied current/comparison date ranges, changed-only mode, separate browser state under `bitrix-sales.abc.v1`, transition badges, and comparison columns shown only when comparison is enabled.

## Intentionally Not Done

- Automatic/scheduled NBRB currency refresh.
- Persisted analytics output tables.
- Full staging-table swap mechanics beyond the current transaction-backed single active table set.
- Production migration tooling.
- Authentication.
- Frontend screens beyond Contacts, Deals, and ABC.
- Background refresh queues, schedulers, and automatic refresh on Docker startup.
- Storybook.
- CI and production deployment.

## Facts

- Bitrix is a read-only data source.
- Main analytics entity is the contact.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
- All financial analytics are normalized to USD.
- First frontend implementation uses `ui-kits/` as the approved design-system source.

## Assumptions

- Python 3.12, FastAPI, Pydantic v2, Polars, DuckDB, Parquet, and pytest are the target backend stack.
- Docker Compose is the default local runtime entry point.

## Unknowns

- Real Bitrix webhook URL remains local secret and is not documented.
- Actual pipelines, stages, and currencies in Bitrix.
- Final design-system tokens and component decisions.
- Deployment host, HTTPS setup, and backup destination.
- Final production storage layout, migration strategy, and whether a full staging-table swap will be required.
- Final frontend response-shape needs beyond the current Contacts screen.

## Next Likely Steps

Review the Contacts, Deals, and ABC frontend reports, then plan the next report screen or shared frontend refinement only after acceptance.
