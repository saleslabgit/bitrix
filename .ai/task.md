# Task: TASK-2026-06-22-23

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-22`

## Title

Build ABC customer report

## Goal

Implement a full customer ABC report screen over local analytics data.

The report must support classic ABC analysis for a selected period and optional comparison with another period in the same table. When comparison is enabled, the table still shows current-period ABC values, while previous-period ABC values and segment changes are shown as additional columns/markers.

## User Request

Add an ABC analysis report by customers.

The report should include:

- classic ABC analysis for a selected period;
- comparison between periods to see who moved from one segment to another;
- comparison should not be a separate table. When a comparison range is selected, the same table updates for the new/current dates and marks rows where there was a transition from one state to another.

## Facts

- Bitrix is read-only and report page loads must not call Bitrix.
- All report filters and calculations run against local DuckDB-backed normalized data.
- Main analytics entity is the contact/customer.
- Revenue means won-only USD revenue.
- Estimated profit is always `revenue_usd * 0.50`, but ABC itself is based on revenue, not profit.
- Deals are assigned to exactly one analytical contact through current normalization rules.
- ABC logic already exists in `backend/app/reports/analytics.py` as `get_abc_report()`, but the current implementation is fixed to full-period vs last-12-month comparison and is not a paginated frontend report screen.
- Current frontend has Contacts and Deals screens in `frontend/src/App.tsx`, using local backend APIs through `frontend/src/api.ts`.
- Contacts and Deals table state is persisted in browser local storage.
- Region filters and columns are temporarily hidden in the frontend while region detection is unfinished.
- Existing report endpoints do not persist analytics output tables.

## Assumptions

- Customer and contact mean the same entity for this report.
- The primary/current period is the period selected by the main date range.
- The optional comparison period is a separate date range used only to calculate previous ABC values and transition markers.
- When comparison is enabled, include contacts that have won revenue in either the current period or the comparison period. This is required to show transitions into `Нет продаж`, for example `A -> Нет продаж`.
- When comparison is not enabled, include contacts that have won revenue in the current period.
- A contact with no won revenue in a period gets segment `Нет продаж` for that period.
- Default primary/current period should be all available won-deal history unless the user selects dates.
- Comparison is disabled by default.
- First click on sortable numeric/date columns should sort from high to low / newest to oldest, consistent with the current table behavior.
- Frontend region controls remain hidden in this task.

## Unknowns

- Browser-level visual verification depends on the execution environment. If unavailable, document the limitation in `.ai/report.md`.
- Exact visual treatment for changed rows is not specified. Use a simple, readable marker/badge that fits the existing UI style.

## Scope

### 1. Backend ABC analytics endpoint

Implement or extend a backend local-only ABC analytics page endpoint, recommended:

```text
GET /api/reports/abc/analytics
```

The endpoint must support classic ABC for the current period and optional comparison in one response.

Required query parameters:

```text
limit
offset
sort
order
```

Recommended filters:

```text
contact_id
search
contact_type
segment
migration_priority
changed_only
date_from
date_to
compare_date_from
compare_date_to
```

Do not expose frontend region filters for this task. Backend may keep internal/backend region support if it already exists, but frontend must not show or send region controls.

ABC calculation rules:

- Use only won deals.
- Use `closed_at` for period filtering.
- Use local USD revenue.
- Group by analytical contact ID.
- Sort by revenue descending, then `contact_id` ascending for classification.
- Calculate `revenue_share_percent` and `cumulative_share_percent` for the period being classified.
- Segment rules:
  - `A` when cumulative share before the current row is below 80%;
  - `B` when cumulative share before the current row is from 80% to below 95%;
  - `C` when cumulative share before the current row is 95% or above;
  - the current row is included in the segment that crosses the threshold, so the largest customer is always `A`.
- If total revenue for a period is zero, no positive rows are classified and contacts in that period are `Нет продаж`.

Response row should include at minimum:

```text
contact_id
contact_name
contact_type_normalized
current_revenue_usd
current_revenue_share_percent
current_cumulative_share_percent
current_segment
current_won_deals_count
current_last_won_date
compare_revenue_usd
compare_segment
segment_change
migration_priority
segment_changed
```

Response page should include at minimum:

```text
total
limit
offset
current_total_revenue_usd
compare_total_revenue_usd
current_segment_counts
compare_segment_counts
migration_priority_counts
items
```

Segment change examples:

```text
A -> B
A -> Нет продаж
Нет продаж -> A
Без изменений
```

Migration priority rules:

- `A -> Нет продаж`: `срочно`
- `A -> C`: `срочно`
- `A -> B`: `важно`
- `B -> Нет продаж`: `важно`
- `B -> C`: `наблюдать`
- `B -> A` or `C -> A`: `развивать`
- `Нет продаж -> A`: `закрепить`
- unchanged rows: `без изменений`
- any other changed row not listed above: `изменение`

Sorting must be allowlisted and stable. Recommended sort fields:

```text
contact_id
contact_name
contact_type_normalized
current_revenue_usd
current_revenue_share_percent
current_cumulative_share_percent
current_segment
current_won_deals_count
current_last_won_date
compare_revenue_usd
compare_segment
segment_change
migration_priority
```

Filtering semantics:

- `contact_id` is exact numeric customer ID.
- `search` matches local contact name only.
- `contact_type` filters normalized contact type.
- `segment` filters current segment.
- `migration_priority` filters migration priority.
- `changed_only=true` returns only rows with `segment_changed=true`.
- Pagination is applied after filtering and sorting.
- Totals/counts are calculated for the filtered set before pagination unless explicitly documented otherwise.

Preserve existing `GET /api/reports/abc` behavior if current tests depend on it, or update tests/docs consistently if it is intentionally replaced. Do not break existing report endpoints.

### 2. Frontend ABC report screen

Add an `ABC` report to the existing frontend navigation alongside Contacts and Deals.

The screen must use only local backend endpoints.

Filters:

- ID клиента;
- client search by customer name;
- Тип;
- ABC сегмент;
- Приоритет перехода;
- checkbox/toggle `Только изменения`;
- current period date range;
- optional comparison period date range.

Date UX requirements:

- Follow the current applied-date pattern from Contacts/Deals: typing in a date input should not refetch the table until dates are applied.
- Invalid ranges should show a clear validation message and should not query the endpoint.
- Comparison is disabled when both comparison dates are empty.
- If only one comparison date is filled, treat the comparison range as incomplete and do not query until the range is complete or cleared.

Table columns:

- ID + Bitrix contact link;
- Клиент;
- Тип;
- Выручка;
- Доля;
- Накопленная доля;
- ABC;
- Успешные сделки;
- Последняя успешная сделка;
- Выручка сравнения;
- ABC сравнения;
- Переход;
- Приоритет.

When comparison is disabled, comparison-specific columns may be hidden or shown empty, but the UI must remain clear and not misleading. Prefer hiding comparison columns until comparison is enabled.

Rows where `segment_changed=true` must be visibly marked using the existing style system, for example a badge or subtle row highlight.

Top/bottom summary should show at least:

- current total revenue;
- comparison total revenue when comparison is enabled;
- counts by current ABC segment;
- changed rows count when comparison is enabled.

State/persistence:

- Persist ABC filters, sort, pagination, and comparison settings in browser local storage under a new key, for example `bitrix-sales.abc.v1`.
- Reset clears only ABC report state, not Contacts/Deals state and not filter metadata cache.
- Existing Contacts and Deals behavior must remain unchanged.

Layout:

- Keep the full-width work area style already used for large Contacts/Deals tables.
- Use horizontal scroll for wide tables.
- Keep loading, error, empty, invalid-date, and database-not-ready states consistent with existing screens.
- Do not reintroduce region filters or region columns.

### 3. Tests

Add focused backend tests for:

- ABC segment assignment at 80/95 boundaries;
- largest revenue contact is always `A`;
- tie-breaker by `contact_id` for equal revenue;
- won-only revenue and `closed_at` period filtering;
- current period single-mode rows, shares, cumulative shares, and totals;
- comparison mode includes contacts from both periods;
- `A -> Нет продаж`, `Нет продаж -> A`, and unchanged transitions;
- migration priority mapping;
- `changed_only`, `segment`, `migration_priority`, `contact_id`, `search`, and `contact_type` filters;
- sorting and pagination are applied after filtering;
- response does not expose forbidden personal fields.

Add/adjust API tests for the new endpoint and response model.

Frontend tests are not currently established; run the frontend build.

### 4. Documentation and report

Update relevant docs:

- `docs/development.md` for the new endpoint and UI flow;
- `docs/data-model.md` for ABC analytics page semantics;
- `docs/project-status.md` for the new ABC report screen;
- `frontend/README.md` for the frontend report behavior.

Update `.ai/report.md` with:

- backend endpoint implemented;
- ABC algorithm and comparison semantics;
- frontend screen and state persistence;
- tests/checks run;
- confirmation that no Bitrix calls/write methods were added.

## Out Of Scope

- RFM report screen.
- Reactivation report screen.
- Charts/graphs for ABC.
- CSV/export.
- Authentication.
- Persisted analytics tables or migrations.
- Changing Bitrix ingestion, refresh, reconciliation, contact-deal link extraction, NBRB rate loading, or normalization rules.
- Live Bitrix diagnostics or any external service calls from report endpoints.
- Region filter/columns in the frontend.
- Editing `ui-kits/`.
- Showing phone, email, address, messenger, comments, files, requisites, raw Bitrix rows, webhook values, or arbitrary custom fields.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- Frontend must call only local backend endpoints.
- Report APIs must read local DuckDB-backed data only.
- Do not add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit `.env`, DuckDB files, Parquet snapshots, raw exports, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Do not expose webhook values, raw rows, local absolute paths, stack traces, or forbidden personal fields.
- Keep all financial values in USD.
- Keep revenue semantics won-only.
- Keep estimated profit formula unchanged, though profit is not required in the ABC table.

## Acceptance Criteria

- A new ABC report is available in the frontend navigation.
- ABC report loads from a local backend endpoint only.
- Current-period ABC is calculated from won USD revenue by `closed_at` period.
- ABC segment assignment follows the documented 80/95 cumulative-share algorithm.
- Current-period table includes customer ID/link, customer name, type, revenue, share, cumulative share, ABC segment, won deals count, and last won date.
- Optional comparison period can be selected in the same report screen.
- When comparison is enabled, the same table shows comparison revenue/segment and marks segment transitions.
- Comparison mode includes contacts with won revenue in either current or comparison period so lost customers can appear as `A -> Нет продаж`.
- `changed_only` shows only changed segment rows.
- Filters, sorting, reset, pagination, loading, error, empty, and invalid-date states work clearly.
- ABC frontend state persists separately from Contacts and Deals.
- Region filters/columns are not shown in the ABC frontend.
- Existing Contacts and Deals behavior is not regressed.
- Backend tests cover ABC algorithm, comparison, filters, sorting, pagination, and safe fields.
- Frontend build passes.
- No Bitrix calls or external service calls are added to report page loads.
- No Bitrix write methods are added.
- Documentation and `.ai/report.md` are updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-23 Build ABC customer report
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run backend tests after backend changes:

```bash
cd backend
python -m pytest
```

Use the existing backend dev environment if system Python lacks pytest and document the exact command.

Run frontend build after frontend changes:

```bash
cd frontend
npm run build
```

Run safety search before committing:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src
```

Before committing:

```bash
git status --short --branch
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

If practical for the environment, run an operator smoke check:

```bash
docker compose config
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
docker compose down
```

If Docker/browser checks cannot be run, document the reason in `.ai/report.md`.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- latest relevant commit is this planner commit;
- ABC backend endpoint and frontend screen are implemented, tested, and documented;
- comparison is implemented in the same table, not as a separate report/table;
- transition rows are visibly marked;
- comparison mode includes both-period contacts so lost/reappeared customers are visible;
- no frontend region filters/columns are added;
- existing Contacts and Deals behavior remains intact;
- no frontend Bitrix calls are added;
- no backend report endpoint calls Bitrix, NBRB, or external services;
- no Bitrix write methods are added anywhere;
- required backend tests and frontend build are run, or inability is explicitly documented;
- `.ai/report.md` describes implementation, checks, facts, unknowns, and risks;
- staged files are only task files plus `.ai/report.md` and relevant docs/code/tests;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
