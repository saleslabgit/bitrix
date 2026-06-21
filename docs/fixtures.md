# Fixture Strategy

This document describes the future integration fixture required for analytics tests. The fixture must be synthetic and must not contain real Bitrix data, secrets, raw exports, local databases, Parquet snapshots, CSV exports, or forbidden personal fields.

## Purpose

The fixture will validate the full local pipeline once implemented:

```text
allowed Bitrix-shaped data -> local raw layer -> normalization -> analytics -> API
```

It is not implemented as a full dataset yet because real Bitrix field codes, pipelines, stages, currencies, contact type values, priorities, and region mapping are still unknown.

## Minimum Dataset

The future integration fixture must include at least:

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
