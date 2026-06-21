# Project Status

## Current Phase

Initial local backend pipeline milestone for the Bitrix sales analytics MVP.

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

## Intentionally Not Done

- Real Bitrix integration.
- NBRB currency integration.
- Parquet snapshot writing.
- Real Bitrix data loading.
- Currency conversion to USD.
- ABC/RFM/reactivation/stale-deal/concentration analytics.
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

## Next Likely Steps

Plan the real Bitrix read-only ingestion boundary and field allowlist discovery, or add the next local analytics slice on top of the normalized synthetic tables.
