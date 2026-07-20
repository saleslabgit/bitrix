# Data Model

This file documents the MVP data model at a high level. The first Python domain scaffold lives under `backend/app/domain/`. The DuckDB storage schema scaffold lives under `backend/app/storage/`, and the first local synthetic pipeline lives under `backend/app/pipeline/`.

## Core Entities

### Contacts

The main analytics entity. Allowed MVP fields include the Bitrix contact ID, display name, and the approved raw contact type field once discovered.

Current scaffold model: `ContactSnapshot`.

Current raw storage table: `raw_contacts`.

Real Bitrix ingestion stores only the allowed contact columns:

- `ID` -> `contact_id`;
- `NAME`, `SECOND_NAME`, and `LAST_NAME` -> `contact_name`;
- configured `BITRIX_CONTACT_TYPE_FIELD` -> `contact_type_raw`, only when explicitly configured.

### Deals

Used for revenue, lifecycle, ABC, RFM, stale-deal, and concentration analytics. Required fields include deal ID, name, original amount, original currency, created and closed timestamps, stage, category, and calculated status group.

Current scaffold model: `DealSnapshot`.

Current raw storage table: `raw_deals`.

Real Bitrix ingestion stores only the allowed deal columns:

- `ID` -> `deal_id`;
- `TITLE` -> `deal_name`;
- `OPPORTUNITY` -> `amount_original`;
- `CURRENCY_ID` -> `currency_original`;
- `DATE_CREATE` -> `created_at`;
- `CLOSEDATE` -> `closed_at`;
- `STAGE_ID` -> `stage_id`;
- `CATEGORY_ID` -> `category_id`;
- `UF_CRM_1716895716` -> universal CRM key `ufCrm_1716895716` -> `kev_held`.
- `contactId` and `contactIds` from `crm.item.list` are selected only to build
  local deal-contact links; they are not stored in `raw_deals`.

`status_group` is derived locally from loaded Bitrix stage semantics.
The approved KEV checkbox is parsed through an explicit boolean allowlist;
missing or blank values mean `kev_held = false` (KEV was not held). Only the
normalized boolean is stored and written to raw Parquet snapshots. Universal
CRM deal selects use the metadata key with the underscore after `ufCrm`;
compatible aliases remain accepted at the transformation boundary.

### Deal-Contact Links

Stores all allowed links between deals and contacts. A deal is counted once in contact analytics by selecting one analytical contact according to configured type priority, Bitrix primary flag, and contact ID tie-breaker.

Current scaffold model: `DealContactLink`.

Current raw storage table: `raw_deal_contact_links`.

Real Bitrix ingestion builds links locally from downloaded `crm.item.list` deal
rows. Current live-safe fields are `contactId` and `contactIds`. A `contactId`
link is stored as primary. Extra IDs from `contactIds` are stored as
non-primary unless they duplicate the primary link. Empty, zero, and missing
contact IDs are skipped. Sort order and role are stored as `NULL` because the
normal sync does not call the per-deal link API.

The backend also has targeted diagnostics for one contact and an explicit
bounded list of deal IDs. Diagnostics are read-only by default. A separate
explicit reconciliation helper can be invoked by an operator/developer for a
supplied contact ID and supplied deal IDs only. It verifies Bitrix
`crm.deal.contact.items.get` relation data for those deal IDs, inserts only
confirmed missing local links and allowed safe deal rows when needed, reruns
normalization, and records a local dataset run/status. This path is not part of
Docker startup, normal page load, broad scheduled sync, or the regular manual
Bitrix refresh flow.

### Stages

Stage dictionaries define whether a deal is `won`, `open`, or `lost`, taking Bitrix pipelines into account.

Current scaffold model: `StageSnapshot`.

Current raw storage table: `raw_stages`.

Real Bitrix ingestion stores only stage ID, category ID, and local `status_group`
derived from Bitrix stage semantics (`won`, `open`, or `lost`).

### Currency Rates

Rates are used to normalize all financial analytics to USD. The target source is the official NBRB API. Rate details and fetch timestamps are stored locally.

Current scaffold model: `CurrencyRateSnapshot`.

Current storage table: `currency_rates`.

Synthetic tests use deterministic fixture rows. Live local readiness can load
NBRB rates into `currency_rates` with `load_currency_rates_for_raw_deals()`.
The loader inspects local `raw_deals`, fetches historical NBRB currency metadata
periods and daily dynamics for the observed date range and currencies, and
stores BYN-per-unit source and USD rates locally. No Bitrix calls are made for
currency work. Conversion is calculated on demand for reports:

```text
amount_usd = amount_original * source_rate_byn / usd_rate_byn
```

The selected rate is the latest local rate for the deal currency on or before
the target date. Closed deals use `closed_at`; open deals use `created_at`. If a
deal date is after the last loaded NBRB date, reports use the latest loaded rate
on or before that deal date.

### Contact Type And Region Config

Contact type normalization, priority, and region mapping are configuration or local data.

Current scaffold model: `ContactTypeRule`.

Current storage table: `contact_type_rules`.

For the live Bitrix dataset, `contact_type_rules.raw_value` stores an individual
Bitrix enum option ID as text, for example `61`, not the full raw combination
string from `raw_contacts.contact_type_raw`. The special source-controlled
raw value `__MISSING__` represents `NULL`, empty string, `False`, and `[]`.

Current approved live rules are source-controlled in
`backend/app/pipeline/approved_contact_type_rules.py` and loaded into DuckDB by
`apply_approved_rules_and_renormalize()`. Active normalization parses option IDs
from raw combination values such as `[61, 59, 65]`, ignores inactive/unknown
options, and chooses the active option with the smallest priority number.
Tie-breaker for multiple active options with the same priority is the smallest
Bitrix option ID. Missing type uses the approved `__MISSING__` rule:
`Конечный клиент / Без региона / priority 4`.

### Normalized Contacts

Stores contact records after applying active contact type rules.

Current normalized storage table: `normalized_contacts`.

Fields:

- `contact_id`;
- `contact_name`;
- `contact_type_raw`;
- `contact_type_normalized`;
- `region_normalized`.
- `kev_held`.

`initialize_schema()` additively migrates existing DuckDB `raw_deals` and
`normalized_deals` tables with `kev_held BOOLEAN NOT NULL DEFAULT false`.
Existing rows are preserved and default to `false`; repeated initialization is safe.

Unknown or inactive type rules normalize to `Не определено`.

For live option-ID rules, missing contact type is not unknown: it uses the
approved `__MISSING__` rule and normalizes to `Конечный клиент / Без региона`.
Non-empty raw values that contain only inactive or unknown option IDs still
normalize to `Не определено`.

### Normalized Deals

Stores one row per deal after stage status derivation and analytical contact assignment.

Current normalized storage table: `normalized_deals`.

Fields include original deal fields plus:

- `analytical_contact_id`;
- `analytical_contact_name`;
- `contact_type_normalized`;
- `region_normalized`.

Deals without contacts are preserved with `analytical_contact_id = NULL`, `analytical_contact_name = "Без контакта"`, and normalized type/region as `Не определено`.

Analytical contact selection uses only active resolved contact type rules.
Priority `1` is highest. If linked contacts have equal resolved priority,
Bitrix primary flag wins, then the smallest contact ID wins. Contacts whose raw
type resolves only to inactive/unknown options are not eligible for analytical
selection.

### Local Dataset Runs And Activation

Dataset runs are stored as local metadata and are the activation boundary for the
single current raw/normalized table set.

Current dataset names are:

- `synthetic-fixture` for the local synthetic fixture pipeline;
- `bitrix-manual` for the manual read-only Bitrix ingestion pipeline.

`local_dataset_runs` is append-only run metadata with a run ID, dataset name,
dataset kind, state, safe message, row counts, UTC timestamps, relative snapshot
identifiers, and an active flag. `local_active_dataset` points to the latest
successful active run. `local_dataset_status` remains as a compact
backward-compatible latest-status table for existing sync status endpoints.

Successful synthetic and manual Bitrix runs replace the current raw/normalized
tables in a DuckDB transaction and become active. Handled failed Bitrix runs are
recorded as error runs but do not activate and do not commit partial
raw/normalized replacements.

Backend FastAPI endpoints use one process-local DuckDB connection for local
storage access. The connection is initialized lazily, its schema is initialized
once per connection lifecycle, and endpoint operations that use this shared
connection run inside a process lock. This avoids concurrent use of the same
DuckDB connection while preserving transaction boundaries for synthetic runs,
manual Bitrix refresh, diagnostics, and local report reads. `reset_connection()`
closes the current connection and resets the schema initialization state for
tests and storage reconfiguration.

### Raw Parquet Snapshots

Successful runs can write Parquet snapshots under the configured local data
directory:

```text
snapshots/<dataset_kind>/<run_id>/<raw_table>.parquet
```

Snapshot status values expose only relative identifiers, not local absolute
paths. The current snapshot allowlist is limited to these raw tables and their
schema columns:

- `raw_contacts`;
- `raw_deals`;
- `raw_deal_contact_links`;
- `raw_stages`.

Snapshots do not include phones, emails, addresses, messengers, comments,
files, activity fields, arbitrary Bitrix fields, webhook values, local database
files, CSV exports, or raw source exports.

### Analytics Outputs

The first local analytics outputs are calculated on demand from `normalized_contacts`, `normalized_deals`, and `currency_rates` in `backend/app/reports/analytics.py`. They are not persisted as analytics tables yet.

Implemented local report outputs:

- contact analytics with deal counts, USD budget breakdown for all/open/lost assigned deals, won revenue USD, estimated profit USD, first/last won dates, latest deal date, and sales flag;
- contact won revenue series with one row per close date for one analytical
  contact, aggregating closed `won` deals in USD and exposing only totals,
  counts, and close dates for charting;
- deal analytics with one row per normalized deal: deal ID/name, status group, KEV boolean, normalized analytical type/region, USD budget, USD estimated profit, created date, and closed date;
- KEV conversion comparison for closed deals with and without KEV;
- ABC comparison for full period vs last 12 months, with `Нет продаж` for contacts without won revenue in a period;
- paginated ABC analytics with filters, sorting, source/base `Было`
  classification, and optional target/result `Стало` segment transitions in
  the same row set;
- RFM rows with 1-5 scores, segment, and a reactivation flag;
- stale open deals based on open age compared with the P75 won-deal cycle for the same contact type, falling back to overall P75;
- deal-cycle metrics overall, by normalized contact type, and by normalized region;
- revenue concentration for top 1, top 3, and top 5 contacts;
- type, region, and type-region aggregate rows.

Contact analytics budget fields use all assigned deals in local USD: `budget_usd` includes all statuses, `budget_in_work_usd` includes open deals, and `lost_budget_usd` includes lost deals. Revenue, ABC, RFM monetary values, concentration, and estimated profit use only won deals. Estimated profit is always `revenue_usd * 0.50`. Deals without an analytical contact remain represented as `Без контакта` / `Не определено` in deal, type, and region outputs and do not create a fake contact.

Deal analytics budget is the single normalized deal amount in USD. Deal
estimated profit is won-only: `budget_usd * 0.50` when `status_group == "won"`,
otherwise `0.00` for open or lost deals. Deal analytics supports exact deal ID,
exact client ID over local `normalized_deals.analytical_contact_id`, client
search over local `normalized_deals.analytical_contact_name`, status,
normalized type, normalized region, and inclusive created-date filters, with
stable allowlisted sorting before pagination. Deal analytics page totals
`filtered_budget_usd`, `filtered_revenue_usd`, and
`filtered_estimated_profit_usd` are calculated across all filtered rows before
pagination. `filtered_revenue_usd` is won-only and sums deal budget only for
filtered rows where `status_group == "won"`.
The Deals endpoint also supports exact `kev_held=true|false` filtering and never
returns the raw Bitrix checkbox value.

`GET /api/reports/kev-conversion/analytics` reads only local
`normalized_deals`. It includes rows with `closed_at IS NOT NULL` and
`status_group IN ('won', 'lost')`; open deals never participate. Each KEV group
returns closed, won, and lost counts plus `won / (won + lost) * 100`, rounded to
one decimal place. A zero denominator returns `null`. The difference is
`with_kev - without_kev` in percentage points and is `null` when either group
has no denominator. Optional `date_from` / `date_to` filters apply inclusively
to `closed_at`, and `contact_type` filters the normalized analytical type.

`GET /api/reports/contacts/{contact_id}/won-revenue-series` calculates a
customer chart series on demand from local normalized data. It includes only
deals whose `analytical_contact_id` matches the requested contact,
`status_group == "won"`, and `closed_at` is not null. Optional `date_from` /
`date_to` filters apply inclusively to `closed_at.date()`. Multiple won deals
closed on the same date are summed into one point. The output does not include
deal names, raw rows, private Bitrix fields, local paths, or secrets.

USD deal conversion does not require a stored `currency_rates` row because the
amount is already denominated in the target currency. Non-USD reports still
require local currency rates; missing non-USD rates are treated as unavailable
local analytics data rather than silently estimated.

`GET /api/reports/abc/analytics` calculates classic customer ABC on demand from
local normalized data. ABC uses only won deals, local USD revenue, and
`normalized_deals.closed_at` for period filtering. Rows are grouped by
`analytical_contact_id`; deals without an analytical contact are not shown as
fake customers. Classification sorts positive-revenue customers by revenue
descending and then `contact_id` ascending. Segment assignment uses cumulative
share before the current row: below 80% is `A`, from 80% to below 95% is `B`,
and 95% or above is `C`; the row that crosses a threshold remains in the
segment that started before the threshold, so the largest customer is always
`A`. Customers with no won revenue in a period have segment `Нет продаж` for
that period.

For ABC analytics, `date_from` / `date_to` are the source/base period
(`Было`), and `compare_date_from` / `compare_date_to` are the target/result
period (`Стало`). Without target dates, the ABC page includes customers with
base-period won revenue and behaves as a single-period ABC report. With target
dates, it includes customers with won revenue in either period, so lost and
reappeared customers remain visible. The transition direction is always
`base segment -> target segment` (`ABC было -> ABC стало`). Filtered totals and
counts are calculated after filters and before pagination. ABC output is not
persisted as an analytics table.

For deterministic synthetic reports, the default analysis date is the maximum local report date from normalized deals. Last-12-month ABC starts from the same month/day one year before that analysis date.

### Dataset Quality Profile

`backend/app/reports/profile.py` calculates safe local-only dataset quality
aggregates from the configured DuckDB database. The profile is exposed through
`GET /api/datasets/profile` and is intended for operator/product decisions about
contact type, priority, and region configuration.

The profile reports only aggregate data: active/latest dataset status, expected
table presence, snapshot count, contact type raw value distribution, missing
type count, active rule coverage, link integrity counts, status/currency counts,
category and stage ID counts, date ranges, and undefined normalization counts.
Bitrix empty field representations such as `False` and `[]` are counted in the
missing contact type bucket for profiling. The profile does not call Bitrix and
does not expose row samples, contact/deal names, contact/deal IDs, local paths,
snapshot paths, secrets, or personal fields outside the allowlist.

`backend/app/bitrix/contact_type_metadata.py` extracts contact type enum option
IDs and labels from Bitrix contact field metadata. `backend/app/reports/contact_type_mapping.py`
combines those metadata labels with local DuckDB aggregate counts by option ID
and raw option combination. This helper is metadata/local-aggregate only: it
does not fetch contact/deal rows and does not create normalization rules.

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
- `local_dataset_status`;
- `local_dataset_runs`;
- `local_active_dataset`.

`APP_DATA_DIR` and `APP_DUCKDB_PATH` define the local persistent DuckDB storage
boundary for runtime. Tests can still pass in-memory or temporary file
connections directly.

Analytics output tables and production migration tooling are still future work.

## Local Synthetic Pipeline

`backend/app/pipeline/synthetic.py` runs the local synthetic pipeline:

```text
initialize schema -> transaction -> load synthetic raw data -> normalize contacts/deals -> write optional snapshots -> activate dataset
```

It uses only synthetic fixture data and does not call Bitrix, NBRB, or external APIs. Currency conversion to USD is implemented in the report layer using synthetic local `currency_rates`, not during normalization.

## Real Bitrix Boundary

`backend/app/bitrix/` contains the first read-only Bitrix boundary:

- `allowlist.py` is the single source of truth for allowed Bitrix select fields.
- `client.py` calls only approved read-only REST methods and handles pagination.
- `discovery.py` reads contact/deal metadata and reports whether the configured contact type field exists.
- `ingestion.py` orchestrates manual raw loading into DuckDB and then runs existing normalization.
- `transform.py` maps allowed Bitrix payload fields into the current domain snapshots.

The manual Bitrix loader clears and reloads only the Bitrix raw tables:
`raw_contacts`, `raw_deals`, `raw_deal_contact_links`, and `raw_stages`.
It does not clear `contact_type_rules` or `currency_rates`; those remain local
configuration/data until later production storage milestones.

Normal manual Bitrix sync does not call `crm.deal.contact.items.get` per deal.
Deal-contact links are reconstructed from already downloaded deal/contact list
data. Any future diagnostic use of the per-deal link API must be planned
separately and must not be reintroduced into the mass sync path.

Manual Bitrix storage replacement, normalization, snapshot writing, run metadata
storage, and activation happen inside a transaction. If a handled client,
transform, or DuckDB error occurs, the transaction is rolled back and the
previous successful active dataset remains available to read/report endpoints.

Discovery may show candidate custom contact fields to help choose
`BITRIX_CONTACT_TYPE_FIELD`, but ingestion never stores arbitrary custom fields.

## Domain Logic

`backend/app/domain/contact_selection.py` contains pure analytical contact selection logic. It selects one contact per deal by configured priority, then `is_primary`, then minimum `contact_id`. Deals without contacts return `None`; no fake contact is created.

## Safety Rules

- Do not store phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.
- Do not use `select: ["*"]` for Bitrix extraction.
- Do not log, return, or document real Bitrix webhook URLs.
- Do not commit raw Bitrix exports, local databases, Parquet snapshots, CSV exports, or secrets.
- Store time in UTC. Default display timezone is `Europe/Minsk`.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
