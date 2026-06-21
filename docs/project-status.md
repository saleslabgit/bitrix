# Project Status

## Current Phase

Initial backend domain scaffold for the Bitrix sales analytics MVP.

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

## Intentionally Not Done

- Real Bitrix integration.
- NBRB currency integration.
- DuckDB schemas and Parquet snapshot writing.
- Contact normalization, storage schemas, or analytics calculations.
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
- Whether pytest and Docker checks pass in an environment with `pip`, test dependencies, and Docker available.

## Next Likely Steps

Plan the local storage schema, synthetic integration fixture data, and first normalization tests before adding real Bitrix integration.
