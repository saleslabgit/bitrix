# Task: TASK-2026-07-20-04

Status: planned
Created from: `2dc1775246155064171ab43549b149f3cc894632`

## Title

Repair and independently verify the rejected funnel analytics implementation

## Goal

Repair the current rejected implementation of funnel-aware reports and make the Contacts, Deals, ABC, and KEV behavior internally consistent, user-visible, tested, and safe.

This is a new task for an independent implementation model. Do not trust prior `.ai/report.md` claims as proof. Inspect the current code and verify every acceptance criterion directly.

Preserve working funnel ingestion, local category storage, exact `(stage_id, category_id)` status resolution, read-only Bitrix access, existing authentication, and existing report behavior outside the defects listed below.

## Review Status

The following Codex commits were reviewed and rejected:

```text
6886b334484dff5cd6222a66c3de3e5efeca1a0d
2dc1775246155064171ab43549b149f3cc894632
```

The current repository contains partial changes from those commits. Repair the implementation rather than reverting all funnel work.

## Verified Current Defects

### Backend sort contract

- `ContactAnalyticsSortField` contains duplicate declarations of:
  - `average_check_usd`;
  - `average_cycle_days`.
- The actual runtime `CONTACT_ANALYTICS_SORT_FIELDS` tuple still does not include those fields.
- FastAPI and frontend expose the fields, so clicking the sortable headers can raise:

```text
Unsupported contact analytics sort field
```

### Deals table alignment

The current Deals headers are ordered as:

```text
ID
Deal name
Status
KEV
Funnel
Cycle
Contact type
Budget
Estimated profit
Created date
Closed date
Average check
```

The current body renders funnel and cycle before KEV. Values therefore appear under the wrong headers.

### Deals footer

- The footer does not display filtered won/open/lost counts.
- The footer cell meanings do not match the 12 visible columns.
- Filter-wide average cycle, budget, profit, and average check must remain backend-derived before pagination.

### ABC and KEV date validation UI

- Separate creation-date drafts were added.
- Queries are disabled for invalid applied creation ranges.
- However, the global `activeRangeInvalid` and `activeDraftsInvalid` logic does not include the ABC/KEV creation-date ranges.
- Therefore the user may see an empty or stale table without the required validation message.

### Cached funnel metadata validation

- `validCategoryOptions()` can turn invalid category input into an empty list.
- `isFilterMetadataValidForDataset()` does not validate `categories`.
- Invalid cached categories can therefore still be treated as valid filter metadata.

### Tests and verification

- The reported `144 passed` suite does not contain focused tests for average-check and average-cycle sorting in both directions with null values.
- No frontend regression test exists for Deals header/body/footer alignment.
- The required browser/operator verification was not completed.

### Frontend quality

The touched sections still contain compressed one-line JSX, long one-line conditions, and malformed comma placement. Clean only the relevant sections.

### Documentation

`docs/data-model.md` was required by the previous task but was not updated in the latest implementation commit.

## Facts

- Bitrix is strictly read-only.
- The only funnel directory method allowed is `crm.category.list`.
- Deals already store `category_id` locally.
- A local category directory stores category ID, name, and optional sort order.
- Deal stages must resolve only by exact `(stage_id, category_id)`.
- Revenue is won-only.
- Estimated profit is `revenue_usd * 0.50`.
- Average check is won revenue divided by won deal count.
- Average cycle uses valid closed `won` and `lost` deals.
- Open deals, missing close dates, and negative cycles do not participate in average cycle.
- Missing denominators return `null`; UI displays `—`.
- Table summaries represent the complete filtered selection before pagination.
- Docker startup starts services only and must never refresh Bitrix automatically.

## Scope

### 1. Inspect the current repository before editing

Read:

- `AGENTS.md`;
- `WORKFLOW.md`;
- `SPEC.md`;
- `.ai/task.md`;
- `.ai/report.md`;
- `backend/README.md`;
- `frontend/README.md`;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/deployment.md`;
- `docs/project-status.md`.

Run:

```bash
git log --oneline -8
git status --short
```

Do not overwrite unknown local changes.

### 2. Fix the Contacts average sort contract

Make these fields work end to end:

```text
average_check_usd
average_cycle_days
```

Requirements:

- Remove duplicate values from `ContactAnalyticsSortField`.
- Add both fields exactly once to the actual `CONTACT_ANALYTICS_SORT_FIELDS` runtime allowlist.
- Keep FastAPI `ContactAnalyticsSortQuery` aligned.
- Keep frontend `ContactSort` and `CONTACT_SORT_FIELDS` aligned.
- Preserve the existing generic sort implementation, null handling, and contact-ID tie-breaker.
- Do not add unsupported sort values.

Add focused tests proving:

- average check ascending;
- average check descending;
- average cycle ascending;
- average cycle descending;
- rows with `null` average values do not crash sorting;
- null placement is deterministic;
- equal values use contact ID as the deterministic tie-breaker;
- the FastAPI endpoint accepts both fields.

### 3. Fix the Deals table column order

The exact header and body order must be:

1. ID;
2. deal name;
3. status;
4. KEV;
5. funnel;
6. cycle, days;
7. contact type;
8. budget;
9. estimated profit;
10. created date;
11. closed date;
12. average check.

Requirements:

- Render KEV immediately after status.
- Render funnel immediately after KEV.
- Render cycle immediately after funnel.
- Row-level average check is not applicable and displays `—`.
- Open deals, missing close dates, and negative cycles display `—`.
- The number of `<td>` cells must exactly match the number of headers.

### 4. Fix the Deals filter-wide footer

Keep one footer labeled:

```text
Итого по выборке
```

The footer must contain exactly 12 column positions matching the table.

Required mapping:

1. ID column: label `Итого по выборке`, using an appropriate `colSpan` only if the resulting total column count remains exactly correct;
2. deal-name/non-aggregatable position: `—` when not covered by the label;
3. status position: compact filtered status counts;
4. KEV position: `—`;
5. funnel position: `—`;
6. cycle position: `filtered_average_cycle_days` or `—`;
7. contact-type position: `—`;
8. budget position: `filtered_budget_usd`;
9. profit position: `filtered_estimated_profit_usd`;
10. created-date position: `—`;
11. closed-date position: `—`;
12. average-check position: `filtered_average_check_usd` or `—`.

The status position must clearly show all three backend counts, for example:

```text
Успешные: N / Открытые: N / Проигранные: N
```

Use:

- `filtered_won_deals_count`;
- `filtered_open_deals_count`;
- `filtered_lost_deals_count`.

Do not derive footer values from visible page rows.

### 5. Complete ABC creation-date draft/apply validation

Preserve the separate ABC creation-date draft state.

Requirements:

- Draft inputs use `abcDealCreatedDrafts`.
- Editing a draft must not update applied filters, query keys, or local storage.
- Applying valid dates updates `abcFilters.dealCreatedFrom` and `abcFilters.dealCreatedTo` and resets offset to zero.
- Reset clears both draft and applied creation dates.
- Reverse applied ranges disable the ABC query.
- Reverse applied ranges must also set `activeRangeInvalid` for ABC so the existing validation state is visible.
- Reverse draft ranges must set `activeDraftsInvalid` for ABC.
- `rangeValidationMessage()` and `draftRangeValidationMessage()` must clearly mention creation dates when that is the invalid range.
- Keep creation dates independent from `Было` and `Стало` close-date periods.

### 6. Complete KEV creation-date draft/apply validation

Preserve the separate KEV creation-date draft state.

Requirements:

- Draft inputs use `kevDealCreatedDrafts`.
- Editing a draft must not update applied filters or local storage.
- Applying valid dates updates the applied KEV creation range.
- Reset clears both draft and applied creation dates.
- Reverse applied ranges disable the KEV query and set `activeRangeInvalid`.
- Reverse draft ranges set `activeDraftsInvalid`.
- Validation messages distinguish creation-date errors from close-date errors.
- Keep creation dates independent from close-date filters.

### 7. Validate cached category metadata correctly

Do not silently turn invalid category metadata into valid empty category metadata.

Implement a clear validation contract, for example one of these approaches:

- parser returns `null`/failure when any category item is invalid; or
- parser returns both parsed values and an explicit validity flag.

Requirements:

- `categories` must be an array.
- Every item must be an object.
- `category_id` must be a non-negative integer.
- `category_name` must be a non-empty trimmed string.
- Invalid category input makes the whole cached metadata invalid.
- `isFilterMetadataValidForDataset()` explicitly validates categories.
- Valid empty categories are allowed only when the active dataset genuinely has no category directory; do not confuse this with malformed cached input.
- Fresh valid metadata may replace invalid cached metadata.
- Invalid cached metadata must not be used for funnel selectors.

Add focused tests for valid, empty, and malformed category metadata. If no frontend unit-test framework exists, extract pure parsing/validation helpers into a small testable TypeScript module and add the smallest practical test setup without introducing a large framework. If adding frontend tests is disproportionate, perform and document a concrete browser/operator test and keep the helper logic simple and reviewable.

### 8. Preserve and verify active filter badge counts

Confirm the badges count:

Contacts:

- category ID.

Deals:

- category ID.

ABC:

- category ID;
- applied deal creation from;
- applied deal creation to.

KEV:

- category ID;
- applied deal creation from;
- applied deal creation to.

Reformat the arrays normally. Remove malformed leading-comma formatting.

### 9. Clean relevant frontend code

Reformat only the touched areas:

- `initialKevFilters`;
- ABC/KEV creation-date state and validation expressions;
- active-filter arrays;
- category select component;
- ABC/KEV creation-date controls;
- Contacts and Deals table footers;
- Deals row cells.

Requirements:

- no compressed one-line JSX in these sections;
- no comma placed at the beginning of a line or expression;
- use existing project style;
- no unrelated frontend redesign.

### 10. Add regression tests for the actual defects

Backend tests must include:

- average sort fields in the runtime allowlist;
- API acceptance of both average sort fields;
- asc/desc/null/tie sorting cases;
- filter-wide summary values before pagination;
- funnel filters in Contacts, Deals, ABC, and KEV;
- inclusive ABC creation-date filtering;
- inclusive KEV creation-date filtering combined with close dates;
- weighted average check and cycle;
- open and negative cycles excluded;
- empty denominators return `null`;
- exact category-aware stage behavior and safe refresh failure remain covered;
- contact `661` analytical assignment regression remains covered.

Frontend verification must cover:

- Deals header/body/footer alignment;
- status counts visible in the footer;
- ABC creation drafts do not apply until the button is clicked;
- KEV creation drafts do not apply until the button is clicked;
- invalid applied and draft ranges show validation UI;
- active-filter badge counts include funnel and creation ranges;
- malformed cached categories are rejected.

Prefer automated tests. Where the repository lacks the required frontend test infrastructure, perform a browser/operator check and document exact steps and outcomes in `.ai/report.md`.

### 11. Update documentation

Update, when necessary to match final behavior:

- `SPEC.md`;
- `backend/README.md`;
- `frontend/README.md`;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/deployment.md`;
- `docs/project-status.md`.

`docs/data-model.md` must explicitly document:

- local funnel/category directory;
- exact category-aware stage resolution;
- average check and cycle semantics;
- filter-wide summary semantics.

Do not append contradictory text to outdated sections. Correct existing documentation where necessary.

### 12. Replace the implementation report

Replace `.ai/report.md` with a clean report for `TASK-2026-07-20-04` only.

The report must include:

- exact changed files;
- exact test commands and results;
- frontend build result;
- Compose config results;
- browser/operator verification steps and results;
- safety search result;
- confirmation that no live Bitrix call occurred;
- known remaining risks.

Set:

```text
Статус: done
```

only when every acceptance criterion is satisfied.

## Out Of Scope

- Live Bitrix calls.
- Any Bitrix write operation.
- New reports or charts.
- Stage history or time-in-stage analytics.
- Responsible-manager analytics.
- Automatic or scheduled refresh.
- Background jobs.
- Production deployment itself.
- General frontend redesign.
- Unrelated refactoring.

## Constraints

- Work from the current repository state.
- Keep Bitrix strictly read-only.
- Preserve `crm.category.list` as the only added funnel-directory method.
- Never add or call:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Never use:

```text
select: ["*"]
```

- Do not make live Bitrix calls.
- Do not expose or commit `.env`, webhook URLs, credentials, DuckDB files, Parquet, CSV, raw Bitrix rows, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits` changes.
- Docker startup must continue to start services only and never refresh Bitrix automatically.
- Do not modify `.ai/task.md` during implementation.
- Do not use `git add .`.
- Do not weaken or delete tests merely to obtain a passing suite.

## Acceptance Criteria

### Backend

- `average_check_usd` and `average_cycle_days` appear exactly once in the type contract and runtime allowlist.
- Both average sort fields work through the FastAPI endpoint.
- Ascending, descending, null, and tie behavior are tested.
- Funnel and date filters remain correct.
- Weighted summaries remain calculated before pagination.
- Complete backend suite passes.

### Deals UI

- Header and body order match exactly.
- Footer aligns with all 12 visible columns.
- Footer displays won/open/lost counts.
- Footer displays average cycle, budget, profit, and average check from backend page totals.
- Row-level average check and unavailable cycle values display `—`.

### ABC and KEV UI

- Creation dates use draft/apply behavior.
- Draft edits do not trigger applied queries.
- Invalid drafts show validation UI.
- Invalid applied ranges show validation UI and disable queries.
- Reset clears draft and applied values.
- Creation dates remain independent from close-date periods.

### Metadata and state

- Malformed cached categories are rejected.
- Valid category IDs and names remain available to all report selectors.
- Active-filter badges include all funnel and creation-date filters.
- Contacts-to-Deals filter propagation remains working.

### Documentation and safety

- Required documentation is current and non-contradictory.
- `.ai/report.md` is accurate and task-specific.
- No Bitrix write methods or wildcard selects are added.
- No live Bitrix calls occur.
- No secrets or generated/private data are committed.
- Docker startup behavior remains unchanged.

## Checks

Before editing:

```bash
git log --oneline -8
git status --short
```

Backend complete suite:

```bash
cd backend
python -m pytest
```

If dependencies are unavailable, use an isolated Python 3.12 Docker/dev environment and install:

```bash
pip install -e ".[dev]"
python -m pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

Run any added frontend tests and record the exact command.

Compose:

```bash
docker compose config
docker compose -f docker-compose.prod.yml config
```

Runtime/operator flow when Docker is available:

```bash
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
docker compose down -v
```

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src docs
rg 'select\s*[:=]\s*\[\s*["'"']\*["'"']\s*\]' backend/app backend/tests
```

Diff validation:

```bash
git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'
```

## Hard Workflow Gate

Before committing:

- complete backend suite passes;
- frontend build passes;
- any added frontend tests pass;
- Compose config checks pass;
- browser/operator verification confirms Deals alignment, footer status counts, ABC/KEV draft/apply, validation states, and filter badges;
- `.ai/report.md` contains exact results for this task only;
- required documentation is updated;
- only task-related files and `.ai/report.md` are staged;
- no secrets, databases, snapshots, generated data, caches, `node_modules`, `frontend/dist`, or `ui-kits` changes are staged;
- no live Bitrix call was made;
- no Bitrix write method or wildcard select was added;
- Docker startup behavior remains unchanged.

Commit message:

```text
codex: TASK-2026-07-20-04 Repair rejected funnel analytics implementation
```
