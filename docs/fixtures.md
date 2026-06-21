# Fixture Strategy

This document describes the synthetic integration fixture required for analytics tests. The fixture must be synthetic and must not contain real Bitrix data, secrets, raw exports, local databases, Parquet snapshots, CSV exports, or forbidden personal fields.

## Purpose

The fixture will validate the full local pipeline once implemented:

```text
allowed Bitrix-shaped data -> local raw layer -> normalization -> analytics -> API
```

The first reusable fixture dataset is implemented at `backend/tests/fixtures/synthetic_dataset.py`. It uses invented test-only values through the existing domain models. Real Bitrix field codes, pipelines, stages, currencies, contact type values, priorities, and region mapping are still unknown.

## Minimum Dataset

The current fixture includes at least:

- 10 contacts;
- 30 deals;
- won, open, and lost deals;
- several currencies;
- synthetic local currency rates for 2023-01-01 and 2025-01-01;
- one deal linked to multiple contacts;
- equal contact type priorities;
- one deal without any contact;
- one A-segment contact without sales in the last 12 months;
- one contact with a single won deal;
- one long-open deal.

Validation coverage lives in `backend/tests/test_synthetic_dataset.py`. Analytics coverage in `backend/tests/test_analytics.py` reuses the fixture to calculate ABC, RFM, currency conversion, stale-deal analytics, revenue metrics, concentration, and type/region aggregates.

## Allowed Data Shapes

Fixture records should use only the MVP fields documented in `docs/data-model.md` and represented by the domain scaffold:

- contacts;
- deals;
- deal-contact links;
- stages;
- currency rates;
- contact type and region rules.

Do not include phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.

## Current And Future Checks

The fixture currently supports local tests for:

- analytical contact selection;
- status derivation;
- type and region normalization;
- currency conversion to USD;
- revenue and estimated profit;
- ABC and ABC migration;
- RFM segments;
- reactivation candidates;
- deal-cycle and stale-deal metrics;
- concentration analytics.

Future production-oriented fixture work should cover real Bitrix field allowlist discovery, NBRB rate behavior, and dataset activation only after those features are planned.
