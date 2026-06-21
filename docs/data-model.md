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

In the local synthetic milestone, rates are deterministic fixture rows only. No NBRB or external API calls are made. Conversion is calculated on demand for reports:

```text
amount_usd = amount_original * source_rate_byn / usd_rate_byn
```

The selected rate is the latest local rate for the deal currency on or before the target date. Closed deals use `closed_at`; open deals use `created_at`. USD is still converted through the local rate formula, with equal source and USD rates in the fixture.

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

The first local analytics outputs are calculated on demand from `normalized_contacts`, `normalized_deals`, and `currency_rates` in `backend/app/reports/analytics.py`. They are not persisted as analytics tables yet.

Implemented local report outputs:

- contact analytics with deal counts, won revenue USD, estimated profit USD, first/last won dates, latest deal date, and sales flag;
- ABC comparison for full period vs last 12 months, with `Нет продаж` for contacts without won revenue in a period;
- RFM rows with 1-5 scores, segment, and a reactivation flag;
- stale open deals based on open age compared with the P75 won-deal cycle for the same contact type, falling back to overall P75;
- deal-cycle metrics overall, by normalized contact type, and by normalized region;
- revenue concentration for top 1, top 3, and top 5 contacts;
- type, region, and type-region aggregate rows.

Revenue, ABC, RFM monetary values, concentration, and estimated profit use only won deals. Estimated profit is always `revenue_usd * 0.50`. Deals without an analytical contact remain represented as `Без контакта` / `Не определено` in deal, type, and region outputs and do not create a fake contact.

For deterministic synthetic reports, the default analysis date is the maximum local report date from normalized deals. Last-12-month ABC starts from the same month/day one year before that analysis date.

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

It uses only synthetic fixture data and does not call Bitrix, NBRB, or external APIs. Currency conversion to USD is implemented in the report layer using synthetic local `currency_rates`, not during normalization.

## Domain Logic

`backend/app/domain/contact_selection.py` contains pure analytical contact selection logic. It selects one contact per deal by configured priority, then `is_primary`, then minimum `contact_id`. Deals without contacts return `None`; no fake contact is created.

## Safety Rules

- Do not store phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.
- Do not commit raw Bitrix exports, local databases, Parquet snapshots, CSV exports, or secrets.
- Store time in UTC. Default display timezone is `Europe/Minsk`.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
