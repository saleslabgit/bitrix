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
- one deal linked to multiple contacts;
- equal contact type priorities;
- one deal without any contact;
- one A-segment contact without sales in the last 12 months;
- one contact with a single won deal;
- one long-open deal.

Validation coverage lives in `backend/tests/test_synthetic_dataset.py`. These tests verify fixture shape and allowed fields only; they intentionally do not calculate ABC, RFM, currency conversion, stale-deal analytics, or revenue metrics yet.

## Allowed Data Shapes

Fixture records should use only the MVP fields documented in `docs/data-model.md` and represented by the domain scaffold:

- contacts;
- deals;
- deal-contact links;
- stages;
- currency rates;
- contact type and region rules.

Do not include phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.

## Future Checks

Once the local storage, normalization, and analytics layers exist, the fixture should support tests for:

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
