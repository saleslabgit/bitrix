# Task: TASK-2026-07-20-03

Status: planned
Created from: `e2244cd49ae78c7b97fc4336ebf07f44d4614406`

## Title

Complete and verify funnel analytics, creation-date filters, average metrics, and filter-wide table summaries

## Goal

Finish and correct the partial implementation from `TASK-2026-07-20-02` so the funnel-aware data flow and all requested report behavior are production-ready, internally consistent, and fully tested.

Repair the existing implementation rather than replacing it. Preserve correct parts, make surgical changes, and do not expand product scope.

## Facts

- Current `main` includes partial task commit `e2244cd49ae78c7b97fc4336ebf07f44d4614406`.
- `.ai/report.md` for the previous task is marked `partial`.
- Funnel ingestion, category-aware stages, API filters, average metrics, and table footers were partially implemented.
- The current implementation has known frontend alignment, filter-state, sorting, test, and documentation defects.
- Bitrix remains strictly read-only.
- Revenue remains won-only.
- Estimated profit remains `revenue_usd * 0.50`.
- Average check is won revenue divided by won deal count.
- Average cycle uses valid closed `won` and `lost` deals, excluding open deals, missing close dates, and negative durations.
- Filter-wide summaries must be calculated from the entire filtered selection before pagination.

## Assumptions

- Existing correct funnel storage and exact `(stage_id, category_id)` resolution should be retained.
- Missing average denominators return `null`; frontend displays `—`.
- Average check is rounded as USD money to two decimals.
- Average cycle is rounded deterministically to one decimal place.
- Funnel select values use numeric `category_id`; labels use local Bitrix funnel names.

## Unknowns

- Exact live `crm.category.list` payload and funnel names remain unverified.
- No live Bitrix calls are required or allowed for this task.

## Scope

### 1. Repair and complete Bitrix funnel boundary tests

Update all fake/mock Bitrix clients to support:

```python
client.list_deal_categories()
client.list_stages(category_id=...)
```

Add focused tests for:

- `crm.category.list` read-only parameters with `entityTypeId = 2`;
- nested `result.categories` parsing;
- pagination;
- approved category fields only: ID, name, optional sort;
- category `0` stage request using `DEAL_STAGE`;
- non-zero category stage request using `DEAL_STAGE_<category_id>`;
- nested `EXTRA.SEMANTICS` and supported top-level semantic aliases;
- identical `stage_id` text in different categories with different semantics;
- exact `(stage_id, category_id)` resolution without cross-category fallback;
- unknown category or stage failing refresh safely before activation;
- previous active dataset remaining intact after handled refresh failure;
- categories loading transactionally and appearing in approved snapshots.

### 2. Fix Deals table structure

Make the header and row cell order exactly:

1. ID
2. Deal name
3. Status
4. KEV
5. Funnel
6. Cycle, days
7. Contact type
8. Budget
9. Estimated profit
10. Created date
11. Closed date
12. Average check

For an individual deal row, average check is not applicable and displays `—`.

Open deals, missing close dates, and negative cycles display `—` in the cycle column.

### 3. Fix Deals bottom summary

Add one authoritative footer row labeled:

```text
Итого по выборке
```

It must align with the exact table columns and use backend values calculated before pagination:

- won/open/lost counts in a clear non-shifting representation;
- funnel and non-aggregatable text/date fields: `—`;
- cycle column: weighted filtered average cycle;
- budget: filtered budget sum;
- profit: filtered estimated profit sum;
- average-check column: weighted filtered average check.

Do not calculate totals from visible browser rows. Remove duplicate/conflicting Deals totals if present.

### 4. Complete Contacts summary and sorting

Contacts must retain visible columns:

- average check;
- average cycle.

Implement end-to-end stable sorting for both:

```text
average_check_usd
average_cycle_days
```

Update:

- backend sort allowlist;
- backend sort implementation with null handling and contact-ID tie-breaker;
- API query typing;
- frontend `ContactSort` allowlist;
- sortable headers;
- tests.

Contacts footer must remain aligned and represent the full filtered selection before pagination.

### 5. Complete active filter counts

The active-filter badge must include:

Contacts:
- category ID.

Deals:
- category ID.

ABC:
- category ID;
- deal creation from;
- deal creation to.

KEV:
- category ID;
- deal creation from;
- deal creation to.

### 6. Implement ABC and KEV deal-creation draft/apply behavior

The deal creation range in ABC and KEV must use the existing safe date pattern:

- separate draft state;
- valid complete ISO dates;
- inclusive range;
- reverse-range validation;
- explicit apply button;
- applied values only in browser storage;
- reset clears draft and applied values;
- invalid applied range prevents query execution;
- existing validation UI is shown instead of calling the API.

Keep creation-date ranges independent from existing close-date ranges.

### 7. Preserve filters when opening Deals from Contacts

When a Contacts count opens Deals, preserve:

- exact analytical contact ID;
- optional status;
- active category ID;
- active deal creation from;
- active deal creation to.

The resulting Deals list must explain the clicked Contacts metric.

### 8. Complete funnel metadata and browser-state validation

Ensure:

- cached filter metadata validates `categories` safely;
- category IDs are non-negative integers;
- category names are non-empty strings;
- funnel options remain sorted by local sort order then category ID;
- each report persists category state only under its own existing storage key;
- reset behavior is independent for Contacts, Deals, ABC, and KEV;
- refresh invalidates filter metadata and all four report queries.

### 9. Backend analytics tests

Add or update tests proving:

- exact funnel filters in Contacts, Deals, ABC, and KEV;
- inclusive creation-date filters in ABC and KEV;
- Contacts category filtering returns only contacts with matching deals;
- weighted average check uses underlying won deals, not average-of-averages;
- weighted average cycle uses valid closed won/lost deals;
- open and negative-cycle deals are excluded;
- empty denominators return `null`;
- filter-wide totals are calculated before pagination;
- one deal is counted once through the analytical contact rule;
- contact `661` analytical assignment regression remains correct.

### 10. Frontend quality

- Fix all table/header/footer alignment defects.
- Replace compressed one-line JSX introduced in the partial implementation with existing repository formatting style.
- Preserve loading, error, empty, retry, authentication, session-expiry, sorting, pagination, reset, and local-storage behavior.
- Do not add unrelated visual redesign or new screens.

### 11. Documentation

Update all relevant documentation to the final behavior:

- `SPEC.md`;
- `backend/README.md`;
- `frontend/README.md`;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/deployment.md`;
- `docs/project-status.md`;
- `.ai/report.md`.

Replace stale previous-task content in `.ai/report.md` with a clean report for this task.

## Out Of Scope

- Live Bitrix calls.
- Any Bitrix write operation.
- Stage-history or time-in-stage analytics.
- New reports or charts.
- Responsible-manager analytics.
- Automatic or scheduled refresh.
- Background queues.
- Unrelated refactoring.
- Production deployment itself.

## Constraints

- Read and follow `AGENTS.md`, `WORKFLOW.md`, and current repository documentation.
- Keep Bitrix strictly read-only.
- The only new funnel read method remains:

```text
crm.category.list
```

- Never add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Never use `select: ["*"]`.
- Do not make live Bitrix calls.
- Do not expose or commit `.env`, webhook URLs, credentials, DuckDB, Parquet, CSV, raw rows, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits` changes.
- Docker startup must continue to start services only and never refresh Bitrix automatically.
- Do not modify `.ai/task.md` during implementation.
- Do not use `git add .`.

## Acceptance Criteria

### Funnel boundary

- Existing and new fake clients match the category-aware ingestion interface.
- Category-list pagination and nested payload parsing are tested.
- Category-specific stage requests and semantics are tested.
- Cross-category stage fallback is impossible and covered by regression tests.
- Unknown category/stage fails safely without replacing the active dataset.

### Filters

- Contacts, Deals, ABC, and KEV filter exactly by `category_id`.
- ABC and KEV use inclusive deal creation ranges independently from close-date ranges.
- ABC and KEV creation dates use draft/apply/validation/reset behavior.
- Active-filter badges count all new filters.
- Contacts-to-Deals navigation propagates category and creation dates.

### Metrics and summaries

- Contacts average check and average cycle are correct and sortable.
- Deals row order matches its headers.
- Deals displays funnel, cycle, and an explicit average-check column.
- Contacts and Deals footers align with table columns.
- Footer sums and weighted averages use all filtered rows before pagination.
- Unavailable averages display `—`.

### Regression and safety

- Existing analytical contact assignment remains unchanged.
- Revenue remains won-only and estimated profit remains 50%.
- No Bitrix write methods or wildcard selects are added.
- No live Bitrix calls occur.
- No secrets or generated/private data are committed.
- Docker startup still does not refresh data.

## Checks

Before implementation:

```bash
git log --oneline -5
git status --short
```

Backend complete suite:

```bash
cd backend
python -m pytest
```

If dependencies are unavailable, use the existing Docker/dev environment and install:

```bash
pip install -e ".[dev]"
python -m pytest
```

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

When Docker runtime is available:

```bash
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
docker compose down -v
```

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src docs
```

Diff validation:

```bash
git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'
```

## Hard Workflow Gate

Before commit:

- complete backend suite passes;
- frontend build passes;
- Compose config checks pass;
- `.ai/report.md` contains only the current task report and exact check results;
- only task-related files and `.ai/report.md` are staged;
- no secrets, databases, snapshots, generated files, caches, `node_modules`, `frontend/dist`, or `ui-kits` changes are staged;
- no live Bitrix call was made;
- no Bitrix write method was added;
- Docker startup behavior remains unchanged.

Set `.ai/report.md` status to `done` only when all required acceptance criteria and checks pass.

Commit message:

```text
codex: TASK-2026-07-20-03 Complete and verify funnel analytics
```
