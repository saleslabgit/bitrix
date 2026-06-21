# Data Model

This file documents the MVP data model at a high level. The first Python domain scaffold lives under `backend/app/domain/`. The DuckDB storage schema scaffold lives under `backend/app/storage/`, and the first local synthetic pipeline lives under `backend/app/pipeline/`.

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

### Normalized Contacts

Stores contact records after applying active contact type rules.

Current normalized storage table: `normalized_contacts`.

Fields:

- `contact_id`;
- `contact_name`;
- `contact_type_raw`;
- `contact_type_normalized`;
- `region_normalized`.

Unknown, missing, or inactive type rules normalize to `Не определено`.

### Normalized Deals

Stores one row per deal after stage status derivation and analytical contact assignment.

Current normalized storage table: `normalized_deals`.

Fields include original deal fields plus:

- `analytical_contact_id`;
- `analytical_contact_name`;
- `contact_type_normalized`;
- `region_normalized`.

Deals without contacts are preserved with `analytical_contact_id = NULL`, `analytical_contact_name = "Без контакта"`, and normalized type/region as `Не определено`.

### Local Dataset Status

`local_dataset_status` stores the current local synthetic pipeline state and row counts. It is not real Bitrix sync status.

### Analytics Outputs

Future analytics outputs include contact aggregates, ABC, ABC migration, RFM, reactivation, type and region aggregates, deal cycle metrics, stale open deals, and revenue concentration.

No full analytics output models are implemented yet.

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
- `normalized_contacts`;
- `normalized_deals`;
- `local_dataset_status`.

Analytics output tables, migrations, production dataset activation, Parquet snapshots, and production storage layout are still future work.

## Local Synthetic Pipeline

`backend/app/pipeline/synthetic.py` runs the local synthetic milestone:

```text
initialize schema -> load synthetic raw data -> normalize contacts/deals -> store local status
```

It uses only synthetic fixture data and does not call Bitrix, NBRB, or external APIs. Currency conversion to USD remains future work.

## Domain Logic

`backend/app/domain/contact_selection.py` contains pure analytical contact selection logic. It selects one contact per deal by configured priority, then `is_primary`, then minimum `contact_id`. Deals without contacts return `None`; no fake contact is created.

## Safety Rules

- Do not store phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.
- Do not commit raw Bitrix exports, local databases, Parquet snapshots, CSV exports, or secrets.
- Store time in UTC. Default display timezone is `Europe/Minsk`.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
