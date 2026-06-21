# Project Status

## Current Phase

Backend/data milestone for the Bitrix sales analytics MVP: local analytics plus the first read-only Bitrix ingestion boundary.

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

## Intentionally Not Done

- NBRB currency integration.
- Parquet snapshot writing.
- Production Bitrix dataset activation/swap mechanics.
- Live Bitrix credential validation against a real account.
- Persisted analytics output tables.
- Production migration tooling or dataset activation mechanics.
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

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual contact types, priorities, and region mapping.
- Actual pipelines, stages, and currencies in Bitrix.
- Final design-system tokens and component decisions.
- Deployment host, HTTPS setup, and backup destination.
- Final production storage layout, migration strategy, and dataset activation mechanics.
- Final frontend response-shape needs beyond the current compact local report API.

## Next Likely Steps

Run discovery against a real read-only Bitrix credential, choose `BITRIX_CONTACT_TYPE_FIELD`, then plan production storage/dataset activation mechanics and NBRB currency integration.
