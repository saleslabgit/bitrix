# Data Model

This file documents the MVP data model at a high level. The first Python domain scaffold lives under `backend/app/domain/`. The first DuckDB storage schema scaffold lives under `backend/app/storage/`.

## Core Entities

### Contacts

The main analytics entity. Allowed MVP fields include the Bitrix contact ID, display name, and the approved raw contact type field once discovered.

Current scaffold model: `ContactSnapshot`.

Current raw storage table: `raw_contacts`.

### Deals

Used for revenue, lifecycle, ABC, RFM, stale-deal, and concentration analytics. Required fields include deal ID, name, original amount, original currency, created and closed timestamps, stage, category, and calculated status group.

Current scaffold model: `DealSnapshot`.

Current raw storage table: `raw_deals`.

### Deal-Contact Links

Stores all allowed links between deals and contacts. A deal is counted once in contact analytics by selecting one analytical contact according to configured type priority, Bitrix primary flag, and contact ID tie-breaker.

Current scaffold model: `DealContactLink`.

Current raw storage table: `raw_deal_contact_links`.

### Stages

Stage dictionaries define whether a deal is `won`, `open`, or `lost`, taking Bitrix pipelines into account.

Current scaffold model: `StageSnapshot`.

Current raw storage table: `raw_stages`.

### Currency Rates

Rates are used to normalize all financial analytics to USD. The target source is the official NBRB API. Rate details and fetch timestamps are stored locally once implemented.

Current scaffold model: `CurrencyRateSnapshot`.

Current storage table: `currency_rates`.

### Contact Type And Region Config

Contact type normalization, priority, and region mapping are configuration or local data. Concrete values are unknown until real Bitrix data is inspected.

Current scaffold model: `ContactTypeRule`.

Current storage table: `contact_type_rules`.

### Analytics Outputs

Future analytics outputs include contact aggregates, ABC, ABC migration, RFM, reactivation, type and region aggregates, deal cycle metrics, stale open deals, and revenue concentration.

No analytics output models are implemented yet.

## Storage Schema

`backend/app/storage/schema.py` exposes a minimal DuckDB schema API:

- `initialize_schema(connection)` creates the current MVP scaffold tables.
- `list_expected_tables()` returns the expected table names for tests and future setup code.

The current tables are limited to allowed MVP data:

- `raw_contacts`;
- `raw_deals`;
- `raw_deal_contact_links`;
- `raw_stages`;
- `contact_type_rules`;
- `currency_rates`.

Normalized tables, analytics output tables, migrations, dataset activation, Parquet snapshots, and production storage layout are still future work.

## Domain Logic

`backend/app/domain/contact_selection.py` contains pure analytical contact selection logic. It selects one contact per deal by configured priority, then `is_primary`, then minimum `contact_id`. Deals without contacts return `None`; no fake contact is created.

## Safety Rules

- Do not store phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.
- Do not commit raw Bitrix exports, local databases, Parquet snapshots, CSV exports, or secrets.
- Store time in UTC. Default display timezone is `Europe/Minsk`.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
