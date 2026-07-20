# Task: TASK-2026-07-20-02

Status: planned
Created from: `2e332864698a52040db7a704f3b97afc09b4d70a`

## Title

Add deal-funnel filters, creation-date filters, average check, deal cycle, and filter-wide table summaries

## Goal

Extend the current Contacts, Deals, ABC, and KEV frontend reports so that users can consistently filter local analytics by:

- inclusive deal creation date range;
- exact Bitrix deal funnel (`category_id`).

Also extend Contacts and Deals with:

- average check;
- deal-cycle metrics;
- a bottom summary row or visually integrated bottom summary band that shows sums or weighted averages for the entire filtered result set, independent of pagination.

All Bitrix access remains read-only. Docker startup must continue to start services only and must not refresh Bitrix automatically.

## User Request

The user approved one combined iteration with these requirements:

1. Add deal creation date filtering to every current frontend report where it does not already exist.
2. Add a funnel filter to all current frontend reports.
3. Download the Bitrix funnel directory and correctly resolve stages for every funnel.
4. Add average check and average deal cycle to Contacts and Deals.
5. At the bottom of Contacts and Deals tables, show a sum or an average depending on the metric.
6. Footer values must represent the whole filtered selection, not only the current page.

Product terminology rule:

- every deal belongs to a funnel through `category_id`;
- all funnels are equal analytical dimensions;
- do not label one funnel as the primary, main, or business-default funnel in API/UI/documentation;
- Bitrix category ID `0` has only a transport-specific stage `ENTITY_ID` encoding described below.

## Facts

- Current `main` is `2e332864698a52040db7a704f3b97afc09b4d70a`.
- Current frontend reports are Contacts, Deals, ABC, and KEV.
- Contacts and Deals already support inclusive `deal_created_from` / `deal_created_to` filtering.
- ABC and KEV do not currently support deal creation date filtering.
- Deals already download and store `category_id` in `raw_deals` and `normalized_deals`.
- The local database does not store a Bitrix funnel/category directory or funnel names.
- Current filter metadata exposes contact types, regions, statuses, and date boundaries, but not funnels.
- Current manual ingestion calls `crm.status.list` only for `ENTITY_ID = DEAL_STAGE`.
- Current status derivation also has a stage-ID-only fallback, which can incorrectly reuse a stage semantic from another funnel.
- Current Bitrix read-only allowlist does not include `crm.category.list`.
- Official Bitrix REST documentation confirms:
  - `crm.category.list` with `entityTypeId = 2` returns deal funnels;
  - a deal links to a funnel through `categoryId`;
  - every funnel has its own stage reference;
  - category ID `0` uses stage `ENTITY_ID = DEAL_STAGE`;
  - category IDs greater than zero use `ENTITY_ID = DEAL_STAGE_{category_id}`;
  - stage semantics may be returned under `EXTRA.SEMANTICS`.
- Current deal-cycle code calculates closed-deal duration as `closed_at - created_at` and excludes negative durations.
- Revenue remains won-only and estimated profit remains `revenue_usd * 0.50`.
- Local analytics are calculated from DuckDB and do not call Bitrix from report endpoints.

## Assumptions

- The approved local funnel entity name is `DealCategorySnapshot` or an equivalently clear existing-style name.
- The approved storage table name is `raw_deal_categories` or an equivalently clear existing-style reference-table name.
- Funnel filters use numeric `category_id` as the stable value and Bitrix category name only as the display label.
- New live/manual Bitrix deal rows are expected to contain a non-negative `categoryId`/`CATEGORY_ID`.
- Existing persisted rows may predate the local funnel directory. They may remain readable, but funnel names/options are populated only after a manual Bitrix refresh.
- Average check is a won-only weighted metric:

```text
average_check_usd = won_revenue_usd / won_deals_count
```

- Deal cycle for this task uses all valid closed deals:

```text
closed deal = status_group in {won, lost} and closed_at is not null
cycle_days = closed_at.date - created_at.date
average_cycle_days = sum(valid cycle_days) / valid closed deals count
```

- Open deals have no cycle value.
- Negative cycle durations are excluded from cycle calculations.
- Average check is rounded as money to two decimal places.
- Average cycle is rounded deterministically to one decimal place.
- Missing denominators return `null`; the UI shows `—`, not `0`.
- Filter-wide averages are weighted from underlying deals, never calculated as the arithmetic mean of per-contact averages.

## Unknowns

- Exact live `crm.category.list` response values and the set of funnel names visible to the configured webhook user.
- Whether the production account contains duplicate funnel names.
- Whether any currently persisted deal row has a missing `category_id`.
- Whether the live account returns stage semantics only in `EXTRA.SEMANTICS`, only in a top-level field, or both.

Do not make live Bitrix calls during implementation or automated verification. Cover the supported contracts through mocked boundary tests. The operator will perform a manual refresh after deployment.

## Scope

### 1. Add the read-only Bitrix funnel boundary

Add only this read method to the Bitrix read-only allowlist:

```text
crm.category.list
```

Implement a focused client method for deal funnels/categories using:

```text
entityTypeId = 2
```

Requirements:

- Support the actual nested `categories` response shape.
- Handle pagination safely when the response reports more categories than one page.
- Extract only the approved fields needed locally, at minimum:
  - category ID;
  - category name;
  - sort order when available.
- Do not store or expose arbitrary category payload fields.
- Do not use any `crm.category.add`, `crm.category.update`, `crm.category.delete`, or other write method.
- Preserve existing safe Bitrix error handling and do not expose webhook data or raw response rows.

### 2. Load stages for every returned funnel

Replace the single-funnel stage download with a category-aware read-only flow.

For every returned `category_id`, call `crm.status.list` with:

```text
category_id == 0  -> filter.ENTITY_ID = DEAL_STAGE
category_id > 0   -> filter.ENTITY_ID = DEAL_STAGE_{category_id}
```

Requirements:

- Treat the ID `0` rule only as a Bitrix transport encoding. Do not present category `0` as primary/main/default in user-facing text.
- Attach the requested `category_id` to each transformed stage from call context; do not trust an unrelated raw category field.
- Parse stage semantics from the supported top-level aliases and nested `EXTRA.SEMANTICS`.
- Map semantics deterministically:
  - success/won -> `won`;
  - failure/apology/lost -> `lost`;
  - process/open/blank -> `open`.
- Resolve deal status only by the exact key:

```text
(stage_id, category_id)
```

- Remove the current stage-ID-only cross-category fallback.
- If a newly downloaded deal cannot be matched to a downloaded funnel and exact stage semantic, fail the manual refresh with a safe message and do not activate or partially replace the previous dataset.
- Never silently classify an unknown cross-funnel stage as `open`.

### 3. Store the local funnel directory

Add a minimal local reference entity and table, for example:

```text
raw_deal_categories
- category_id BIGINT PRIMARY KEY
- category_name VARCHAR NOT NULL
- sort_order INTEGER
```

Requirements:

- Add the table through the existing idempotent schema initialization path.
- Existing DuckDB files must open without destructive migration or row loss.
- Add categories to the transactional raw replacement flow.
- Add only the approved category fields to raw Parquet snapshots.
- Update schema/profile/snapshot allowlists and tests.
- Extend the synthetic fixture with at least two funnels and category-specific stages.
- Include a regression fixture where identical `stage_id` text exists in two categories with different semantics, proving that exact category-aware mapping is used.

### 4. Expose funnel metadata to the frontend

Extend `GET /api/meta/filters` with a typed funnel/category option list containing:

```text
category_id
category_name
```

Requirements:

- Sort options deterministically by local sort order and then category ID, or by category ID when sort order is absent.
- The frontend select value must be category ID, not category name.
- Display the actual Bitrix funnel name.
- Do not expose raw Bitrix category payloads.
- Preserve existing contact type/status/date metadata and cached-filter behavior.

### 5. Add exact funnel filtering to all current frontend reports

Add optional exact query parameter:

```text
category_id=<non-negative integer>
```

Apply it to:

- `GET /api/reports/contacts/analytics`;
- `GET /api/reports/deals/analytics`;
- `GET /api/reports/abc/analytics`;
- `GET /api/reports/kev-conversion/analytics`.

Rules:

- Filter using local `normalized_deals.category_id`.
- When category filtering is active in Contacts, return only contacts with at least one matching deal after all deal-level filters.
- In ABC, apply category filtering to deal facts before both the `Было` and optional `Стало` closed-date periods are calculated.
- In KEV, combine category filtering with the existing close-date and contact-type filters.
- Preserve existing status, type, KEV, client, sorting, totals, and pagination behavior.

Frontend requirements:

- Add a `Воронка` select to Contacts, Deals, ABC, and KEV filter drawers.
- Options come from local filter metadata.
- Persist each report's category selection only inside that report's existing browser-storage key.
- Reset clears the category filter.
- Active filter counts include the category filter.
- Do not call Bitrix directly from the frontend.
- Add a visible `Воронка` column to Deals using the local category name. Category sorting is optional; add it only if implemented end-to-end and covered by tests.

### 6. Complete deal creation date filtering across reports

Preserve the existing inclusive deal creation filters in Contacts and Deals:

```text
deal_created_from
deal_created_to
```

Add the same optional parameters to:

- `GET /api/reports/abc/analytics`;
- `GET /api/reports/kev-conversion/analytics`.

Rules:

- Filter by `normalized_deals.created_at` date, inclusively.
- The creation-date range is independent from existing close-date periods.
- In ABC, the creation range is a global deal filter applied before both `Было` and optional `Стало` close-date calculations.
- In KEV, a deal must satisfy both the creation-date range and the existing close-date range when both are present.
- Preserve existing close-date semantics and labels.

Frontend requirements:

- Add `Сделка создана с` and `Сделка создана по` controls to ABC and KEV.
- Use existing draft/apply, validation, reset, metadata min/max, local-storage, loading, error, and retry patterns.
- Keep the existing close-date controls in ABC and KEV; do not replace them.

### 7. Add Contacts average check and average cycle

Extend each Contacts analytics row with:

```text
average_check_usd: Decimal | null
average_cycle_days: Decimal | null
```

Per-contact rules after all active filters:

- `average_check_usd` uses the contact's won-only USD revenue divided by won deals count.
- `average_cycle_days` uses valid closed won/lost deals assigned to that contact.
- Open deals and negative cycle durations do not participate in cycle average.
- A zero denominator returns `null`.
- Add visible sortable columns `Средний чек` and `Средний цикл, дн.` unless sorting would require an unrelated refactor; if sorting is omitted, document it explicitly in `.ai/report.md`.

### 8. Add Deals cycle values and filtered average metrics

Extend each Deals analytics row with:

```text
category_id
category_name
cycle_days: int | null
```

Row rules:

- Closed won/lost deal with a non-negative duration -> integer cycle days.
- Open deal, missing close date, or negative duration -> `null` and UI `—`.

Extend the filter-wide Deals page summary with at least:

```text
filtered_won_deals_count
filtered_open_deals_count
filtered_lost_deals_count
filtered_average_check_usd: Decimal | null
filtered_average_cycle_days: Decimal | null
```

Preserve existing:

```text
filtered_budget_usd
filtered_revenue_usd
filtered_estimated_profit_usd
```

Rules:

- Average check is won-only filtered revenue divided by filtered won count.
- Average cycle is calculated directly from all valid filtered closed won/lost deal durations.
- Do not average per-row or per-contact averages.
- Calculate all summary fields before pagination.

Frontend requirements:

- Add visible `Воронка` and `Цикл, дн.` columns to Deals.
- Show filtered average check and average cycle at the bottom of the table.
- Open deals show `—` for cycle.

### 9. Add filter-wide bottom summaries to Contacts and Deals

The bottom summary must represent the entire filtered selection, not the visible page.

Implement a typed Contacts filter-wide summary, either as a dedicated nested response object or clearly named page-level fields, containing at least:

```text
filtered_contacts_count
filtered_total_deals_count
filtered_won_deals_count
filtered_open_deals_count
filtered_lost_deals_count
filtered_budget_usd
filtered_budget_in_work_usd
filtered_lost_budget_usd
filtered_revenue_usd
filtered_estimated_profit_usd
filtered_average_check_usd: Decimal | null
filtered_average_cycle_days: Decimal | null
```

Calculation rules:

- Count and money fields are sums from all filtered underlying data.
- Average check and average cycle are weighted from underlying deals.
- Do not sum per-contact values if that would double count a deal.
- Preserve the one-deal/one-analytical-contact rule.
- All summary calculations occur before pagination.

UI rules for Contacts and Deals:

- Add a visually integrated bottom summary row or bottom summary band immediately below the table rows and above pagination.
- Label it `Итого по выборке`.
- Use sums for additive metrics:
  - deal counts;
  - budget;
  - budget in work;
  - lost budget;
  - revenue;
  - estimated profit.
- Use weighted averages for:
  - average check;
  - average cycle.
- Use `—` for non-aggregatable text/date fields and unavailable averages.
- Do not calculate footer values in the browser from the current page rows.
- Keep the footer usable with horizontal scrolling and the existing compact workspace.
- Preserve existing top/bottom Deals totals only if they do not duplicate or conflict with the new single authoritative bottom summary. Prefer one clear bottom summary instead of repeated totals.

### 10. Preserve cross-report and browser behavior

Requirements:

- Existing Contacts -> Deals navigation must still apply exact analytical client ID and optional status.
- When practical without expanding scope, propagate active category and deal-creation filters during Contacts -> Deals navigation so the deal list explains the clicked Contacts metric.
- Preserve authentication and session-expiry behavior.
- Preserve loading, error, empty, retry, reset, sorting, pagination, and browser-storage behavior.
- Refresh success must invalidate Contacts, Deals, ABC, KEV, dataset status, and filter metadata queries.

### 11. Documentation

Update at least:

- `SPEC.md`;
- `backend/README.md`;
- `frontend/README.md`;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/deployment.md`;
- `docs/project-status.md`;
- `.ai/report.md`.

Document:

- `crm.category.list` is the only newly allowed Bitrix method;
- every deal is filtered by numeric `category_id` and displayed with the local funnel name;
- the technical stage `ENTITY_ID` encoding for category `0` and positive category IDs;
- exact category-aware stage semantic resolution;
- creation-date versus close-date filter semantics;
- average-check and average-cycle formulas;
- weighted whole-selection footer semantics;
- after deployment/update, the operator must manually run `Обновить из Bitrix` once to populate the funnel directory and category-aware stage dictionary.

## Out Of Scope

- Any Bitrix write operation.
- Live Bitrix calls during implementation or automated verification.
- Creating, updating, deleting, reordering, or renaming Bitrix funnels or stages.
- A new funnel-comparison report or chart.
- Stage history, time-in-stage analytics, or `crm.stagehistory.list`.
- Responsible-manager analytics.
- Loss-reason analytics.
- Product-line analytics.
- New frontend report screens.
- Automatic or scheduled refresh.
- Background queues.
- Refactoring unrelated legacy report endpoints.
- Replacing the current DuckDB storage architecture or adding a migration framework.
- Fixing unrelated production nginx refresh-timeout technical debt.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- Newly allowed Bitrix method:

```text
crm.category.list
```

- Existing read-only `crm.status.list` remains allowed.
- Never add methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Never use `select: ["*"]`.
- Do not expose or commit the webhook, real `.env`, credentials, local DuckDB, Parquet, CSV, raw data, logs, `node_modules`, `frontend/dist`, or `ui-kits` changes.
- Docker Compose must start services only.
- Report endpoints must use only local data.
- Preserve analytical contact assignment and one-deal/one-contact counting.
- Preserve won-only revenue and 50% estimated-profit rules.
- Keep changes task-focused and avoid unrelated refactors.

## Acceptance Criteria

### Bitrix and storage

- `crm.category.list` is the only new Bitrix method and is read-only.
- Deal categories are downloaded with `entityTypeId = 2` through mocked tests.
- Nested category response parsing and pagination are covered.
- Every downloaded category gets its own `crm.status.list` request with the correct technical `ENTITY_ID`.
- Nested `EXTRA.SEMANTICS` and supported aliases are parsed.
- Status is resolved only through exact `(stage_id, category_id)` matching.
- Duplicate stage IDs in different funnels cannot contaminate each other's semantics.
- Unknown category/stage mappings fail safely and do not activate partial data.
- The local funnel table is created idempotently and existing database rows are preserved.
- Category snapshots contain only approved local fields.
- Synthetic data contains multiple funnels.

### Filters

- Filter metadata returns typed funnel ID/name options.
- Contacts, Deals, ABC, and KEV support exact funnel filtering.
- Contacts and Deals retain inclusive creation-date filtering.
- ABC and KEV gain inclusive creation-date filtering.
- ABC and KEV keep their existing close-date filters independently.
- Funnel and creation-date filters compose with existing filters.
- Frontend funnel/date controls persist and reset correctly.
- Deals visibly shows the funnel name.

### Contacts metrics and footer

- Contacts rows expose correct won-only average check.
- Contacts rows expose correct average cycle over valid closed won/lost deals.
- Contacts page exposes filter-wide sums and weighted averages before pagination.
- The Contacts bottom summary shows sums and averages for the entire filtered selection.
- Empty denominators return `null` and display `—`.

### Deals metrics and footer

- Deals rows expose category ID/name and nullable cycle days.
- Open deals display no cycle.
- Deals page exposes filtered status counts, weighted average check, and weighted average cycle before pagination.
- Existing filtered budget/revenue/profit totals remain correct.
- The Deals bottom summary shows sums and averages for the entire filtered selection.
- Footer values do not change incorrectly when pagination changes.

### Safety and regression

- Existing contact 661/multi-contact analytical-assignment regression remains passing.
- Existing KEV behavior and conversion calculations remain passing.
- Existing ABC comparison behavior remains passing.
- Existing sorting, pagination, authentication, refresh, and local-only API behavior remain passing.
- Automated tests make no live Bitrix calls.
- No Bitrix write method is added.
- No secrets or generated/private data are committed.
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

Operator flow when Docker is available:

```bash
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
docker compose down -v
```

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src docs SPEC.md
```

Focused verification must cover:

- category list parsing and pagination;
- category-specific stage request encoding for ID `0` and positive IDs;
- nested stage semantics;
- duplicate stage IDs across categories;
- unknown mapping failure and previous dataset preservation;
- schema and snapshot allowlists;
- funnel metadata and exact funnel filters in all four reports;
- ABC/KEV inclusive deal creation filters;
- independent creation/close-date filter composition;
- contact average check and average cycle;
- deal nullable cycle;
- filter-wide sums and weighted averages before pagination;
- null averages/empty denominators;
- Contacts/Deals bottom summaries;
- existing contact assignment, KEV, ABC, auth, and refresh regressions.

## Hard Workflow Gate

Before committing:

- `.ai/report.md` is updated with exact files, checks, facts, assumptions, unknowns, and remaining risks.
- Only task-related files and `.ai/report.md` are staged.
- No `.env`, webhook, credentials, DuckDB, Parquet, CSV, raw/generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits` changes are staged.
- Backend tests are recorded.
- Frontend build is recorded.
- Compose config checks are recorded.
- Operator flow is recorded when Docker is available, or the limitation is explicit.
- No live Bitrix call was made.
- `crm.category.list` is the only newly allowed Bitrix method.
- No Bitrix write method was added.
- Docker startup still does not refresh Bitrix automatically.
- Filter-wide footer values are verified against more rows than one page.
- Unknown category/stage mapping is verified to preserve the previous active dataset.

Commit message:

```text
codex: TASK-2026-07-20-02 Add funnel filters and summary metrics
```
