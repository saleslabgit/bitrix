# Task: TASK-2026-07-20-01

Status: planned
Created from: `fdcca56c5cf569ad713614f66397a6c4de8ba815`

## Title

Add KEV deal field and conversion report

## Goal

Add the approved Bitrix deal checkbox field `UF_CRM_1716895716` to the local read-only data pipeline and build a frontend report that compares closed-deal conversion:

- when KEV was held;
- when KEV was not held.

The business rule is explicit:

```text
blank or missing UF_CRM_1716895716 = KEV was not held
```

Only closed deals participate in conversion:

```text
closed deals = won + lost
conversion = won / (won + lost) * 100
```

Open deals must not participate.

## User Request

The user wants to measure whether an office KEV meeting correlates with a higher order conversion rate.

Approved field:

```text
UF_CRM_1716895716
```

Approved blank-value semantics:

```text
blank = KEV was not held
```

## Facts

- Current `main` is `fdcca56c5cf569ad713614f66397a6c4de8ba815`.
- Bitrix is read-only.
- Regular manual refresh downloads deals through `crm.item.list` and builds deal-contact links locally.
- Current deal allowlists do not include `UF_CRM_1716895716`.
- `DealSnapshot`, `raw_deals`, and `normalized_deals` do not currently store KEV data.
- Existing production DuckDB is persisted under `data/`; schema changes must work against an existing database.
- Current `initialize_schema()` creates missing tables but does not migrate existing tables with new columns.
- Deals analytics already exposes deal rows, filters, sorting, totals, and pagination.
- Frontend currently contains Contacts, Deals, and ABC report screens.
- Docker Compose must not refresh Bitrix automatically.
- The server-local webhook and `.env` must not be exposed or committed.

## Assumptions

- The approved internal boolean name is `kev_held`.
- Known checked values may arrive as boolean/integer/text forms such as `true`, `1`, or `Y`.
- Missing, empty, false, `0`, or `N` values mean `kev_held = false`.
- Unexpected non-empty values must be handled deterministically and covered by tests; do not silently leak raw values to API/UI.
- The universal CRM item field may be exposed as `ufCrm1716895716`; implementation should support metadata-based selection and payload aliases without using `select: ["*"]`.
- Conversion percentage should be `null` when a group has zero closed deals, so UI shows `—` instead of a misleading `0%`.

## Unknowns

- Exact live Bitrix payload type/value for this checkbox.
- Exact universal CRM item metadata casing returned by the live account.
- Historical date when the field started being used consistently.

Do not run a live Bitrix call for this task. Cover supported representations with mocked boundary tests.

## Scope

### 1. Add the approved deal field to the read-only Bitrix boundary

Add a source-controlled constant for:

```text
UF_CRM_1716895716
```

Requirements:

- Include the field in the traditional deal select allowlist.
- Include safe metadata candidates for universal `crm.item.list`, including the expected camel-case representation.
- Keep explicit selects only.
- Do not add arbitrary custom fields.
- Keep all existing forbidden-field checks.
- Keep the read-only method allowlist unchanged unless a currently allowed read method is reused.
- Do not add any CRM write method.

### 2. Parse and store `kev_held`

Extend the deal domain/data path with:

```text
kev_held: bool
```

Update the relevant layers:

- deal domain model;
- Bitrix transformation;
- synthetic fixture data;
- raw loader;
- `raw_deals`;
- normalization;
- `normalized_deals`;
- Parquet raw snapshot allowlist;
- schema/profile tests and documentation.

Parsing rules:

- missing or blank -> `false`;
- boolean `false` -> `false`;
- numeric/text zero -> `false`;
- `N`, `NO`, `FALSE` -> `false`;
- boolean `true` -> `true`;
- non-zero numeric/text one -> `true`;
- `Y`, `YES`, `TRUE` -> `true`.

Use a small explicit parser. Do not use generic Python truthiness for arbitrary strings.

### 3. Migrate an existing DuckDB safely

Add an idempotent schema migration inside the existing schema initialization path.

Required columns:

```text
raw_deals.kev_held BOOLEAN NOT NULL DEFAULT false
normalized_deals.kev_held BOOLEAN NOT NULL DEFAULT false
```

Requirements:

- A new empty database receives the columns.
- An existing database created by the previous schema receives the columns without losing rows.
- Repeated initialization remains safe.
- Existing rows become `false`.
- Do not delete or recreate the production database.
- Do not introduce a large migration framework for this single additive change.

Add a focused file-backed migration test that creates the previous schema shape, inserts representative rows, initializes the new schema, and verifies that rows remain and both new columns are present with `false` values.

### 4. Extend Deals analytics and UI

Expose `kev_held` in `GET /api/reports/deals/analytics`.

Add an optional filter:

```text
kev_held=true|false
```

Requirements:

- Add a visible `КЭВ` column to Deals.
- Display `Был` / `Не был`.
- Add a Deals filter with `Все`, `Был`, `Не был`.
- Preserve existing sorting, pagination, totals, client linking, and browser state behavior.
- Do not expose the raw Bitrix field value.

Sorting by KEV is optional; do not add it unless it stays simple and consistent.

### 5. Add KEV conversion analytics endpoint

Add:

```text
GET /api/reports/kev-conversion/analytics
```

Supported filters:

- `date_from` — inclusive `closed_at` date;
- `date_to` — inclusive `closed_at` date;
- `contact_type` — optional normalized analytical contact type.

The endpoint must use only local `normalized_deals` data and must not call Bitrix or external APIs.

Return two comparison groups:

```text
with_kev
without_kev
```

Each group must include:

- `closed_deals_count`;
- `won_deals_count`;
- `lost_deals_count`;
- `conversion_percent` as a decimal percentage or `null` when the denominator is zero.

Also return:

- `conversion_difference_percentage_points` = with-KEV conversion minus without-KEV conversion, or `null` when either conversion is unavailable;
- applied date range.

Rules:

- include only `status_group in {won, lost}`;
- require `closed_at IS NOT NULL`;
- exclude open deals even if they contain KEV data;
- group `kev_held = true` as with KEV;
- group `kev_held = false` as without KEV;
- filter periods by `closed_at`, not `created_at`;
- use deterministic decimal rounding consistent with existing percentage helpers.

### 6. Add frontend report screen

Add a new sidebar report:

```text
КЭВ
```

The screen must show a compact comparison table or two compact comparison cards with:

- group: `КЭВ был` / `КЭВ не был`;
- closed deals;
- won deals;
- lost deals;
- conversion;
- conversion difference in percentage points.

Filters:

- close date from;
- close date to;
- contact type.

Requirements:

- Follow the existing report workspace and design tokens.
- Add loading, error, empty/no-denominator, and retry states.
- Preserve auth behavior.
- Persist only KEV report filter state under a separate browser-storage key.
- Do not add charts in this task.
- Do not call Bitrix directly from the frontend.

### 7. Documentation

Update at least:

- `docs/data-model.md`;
- `docs/development.md`;
- `docs/project-status.md`;
- backend/frontend README files if their endpoint or field inventories require it;
- `.ai/report.md`.

Document:

- approved Bitrix field code;
- blank means KEV was not held;
- only won/lost closed deals participate;
- formula;
- period uses `closed_at`;
- existing DuckDB is migrated additively;
- after deployment, the operator must manually run `Обновить из Bitrix` to populate the new field.

## Out Of Scope

- Live Bitrix calls.
- Any Bitrix write operation.
- Proving causality between KEV and conversion.
- Statistical significance calculations.
- Funnel/category comparison.
- Responsible-manager analytics.
- Loss-reason analytics.
- Stage history or time-in-stage analytics.
- Monthly trend charts.
- Automatic or scheduled refresh.
- Background queues.
- Refactoring unrelated reports.
- Fixing the production nginx refresh timeout technical debt.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- Never add methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Never use `select: ["*"]`.
- Do not expose or commit the webhook, real `.env`, credentials, local DuckDB, Parquet, CSV, raw data, logs, `node_modules`, or `frontend/dist`.
- Do not change automatic startup behavior; Docker starts services only.
- Preserve existing deal-contact assignment and contact analytics semantics.
- Preserve won-only revenue and 50% estimated-profit rules.
- Keep changes surgical and task-focused.

## Acceptance Criteria

### Data ingestion and storage

- `UF_CRM_1716895716` is requested through explicit safe deal selects.
- Universal item metadata/payload aliases are supported through mocked tests.
- Blank/missing checkbox values become `kev_held = false`.
- Checked values become `kev_held = true`.
- `kev_held` is stored in raw and normalized deals.
- Existing DuckDB files are migrated without row loss.
- Raw Parquet snapshots include only the normalized boolean KEV column, not arbitrary payload data.

### Deals report

- Deals API returns `kev_held`.
- Deals API supports exact boolean filtering.
- Deals UI displays and filters KEV status.
- Existing filters, totals, sorting, links, and pagination remain functional.

### KEV conversion report

- A typed local endpoint returns with-KEV and without-KEV conversion groups.
- Only closed won/lost deals are counted.
- Open deals are excluded.
- Date filters use inclusive `closed_at` dates.
- Conversion is `won / (won + lost) * 100`.
- Empty denominators return `null` and UI displays `—`.
- Difference is displayed in percentage points.
- The frontend has a working `КЭВ` report with loading, error, and filter states.

### Safety and regression

- Existing analytical contact assignment is unchanged.
- No live Bitrix calls are made during tests or implementation verification.
- No Bitrix write methods are added.
- No secrets or generated/private data are committed.
- Existing backend tests pass.
- Frontend build passes.
- Documentation and `.ai/report.md` are updated.

## Checks

Before implementation:

```bash
git log --oneline -5
git status --short
```

Backend:

```bash
cd backend
python -m pytest
```

If the system interpreter lacks dependencies, use the existing project/dev environment and record the exact command.

Frontend:

```bash
cd frontend
npm run build
```

Compose:

```bash
docker compose config
docker compose -f docker-compose.prod.yml config
```

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src docs
```

Focused verification must cover:

- new database schema;
- previous-schema file migration with row preservation;
- checked and blank Bitrix payload variants;
- won/lost/open report grouping;
- close-date filtering;
- zero denominators;
- Deals KEV filtering;
- existing analytical contact assignment regression.

## Hard Workflow Gate

Before committing:

- `.ai/report.md` is updated;
- only task-related files are staged;
- no `.env`, webhook, credentials, DuckDB, Parquet, CSV, raw/generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes are staged;
- schema migration is tested against a previous-schema file;
- backend tests are recorded;
- frontend build is recorded;
- Compose config checks are recorded;
- no live Bitrix call was made;
- no Bitrix write method was added;
- Docker startup still does not refresh Bitrix automatically.

Commit message:

```text
codex: TASK-2026-07-20-01 Add KEV conversion report
```
