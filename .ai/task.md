# Task: TASK-2026-07-20-03

Status: planned
Created from: `6886b334484dff5cd6222a66c3de3e5efeca1a0d`

## Title

Complete and verify funnel analytics, creation-date filters, average metrics, and filter-wide table summaries

## Goal

Fix the remaining review blockers in the partial implementation of funnel-aware analytics and make the current task acceptable.

Preserve the correct parts already implemented. Make surgical corrections only. Do not introduce new reports, redesign the application, or expand product scope.

## Review Status

The Codex commit `6886b334484dff5cd6222a66c3de3e5efeca1a0d` is not accepted.

The implementation still has blocking backend/frontend contract defects and does not satisfy the documentation and verification requirements.

## Facts

- Bitrix remains strictly read-only.
- Funnel/category ingestion and exact `(stage_id, category_id)` resolution already exist and must be preserved.
- Contacts-to-Deals navigation now propagates category and creation-date filters and must remain working.
- Full backend tests were reported as passing, but required acceptance behavior is still missing from the implementation.
- Revenue remains won-only.
- Estimated profit remains `revenue_usd * 0.50`.
- Average check is won revenue divided by won deal count.
- Average cycle uses valid closed `won` and `lost` deals, excluding open deals, missing close dates, and negative durations.
- Filter-wide summaries must be calculated before pagination from the entire filtered selection.

## Scope

### 1. Fix Contacts average metric sorting

The API and frontend expose:

```text
average_check_usd
average_cycle_days
```

but the actual backend `CONTACT_ANALYTICS_SORT_FIELDS` allowlist does not include them.

Requirements:

- Add both fields to the actual backend allowlist used by `list_contact_analytics()`.
- Preserve stable sorting, null handling, and contact-ID tie-breaking.
- Keep FastAPI query typing and frontend `ContactSort` aligned with the backend.
- Add focused backend tests for ascending and descending sorting of both fields.
- Include rows with `null` averages in sorting tests.
- Verify the endpoint no longer returns `Unsupported contact analytics sort field` for these two fields.

### 2. Fix Deals header and row alignment

The exact visible Deals column order must be:

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

Requirements:

- Render row cells in exactly the same order as headers.
- KEV must appear under the KEV header.
- Funnel name must appear under the Funnel header.
- Cycle must appear under the Cycle header.
- Row-level average check is not applicable and displays `—`.
- Open deals, missing close dates, and negative cycles display `—`.
- Add a frontend-oriented regression test if the current test stack supports it; otherwise document and perform an explicit browser/operator check.

### 3. Fix Deals filter-wide footer

Keep one authoritative footer labeled:

```text
Итого по выборке
```

Requirements:

- Footer cell count and order must exactly match the 12 visible columns.
- Display filtered won/open/lost counts clearly without shifting the table.
- A compact combined status-count cell is acceptable, for example:

```text
Успешные: N / Открытые: N / Проигранные: N
```

- Funnel and non-aggregatable text/date columns display `—`.
- Cycle column displays `filtered_average_cycle_days`.
- Budget displays `filtered_budget_usd`.
- Profit displays `filtered_estimated_profit_usd`.
- Average-check column displays `filtered_average_check_usd`.
- Use backend response values calculated before pagination.
- Do not calculate footer metrics from current-page rows.

### 4. Implement deal-creation draft/apply behavior for ABC

The ABC creation-date fields currently write directly to applied filters.

Add separate draft state for:

```text
dealCreatedFrom
dealCreatedTo
```

Requirements:

- Initialize drafts from applied ABC filters.
- Draft edits must not trigger report requests or browser-storage changes.
- Validate complete ISO dates.
- Validate that start is not later than end.
- Add an explicit `Применить даты создания` action.
- Applying valid drafts updates both applied values and resets offset to zero.
- Reset clears both draft and applied creation dates.
- Invalid applied creation ranges disable the ABC query and show validation UI.
- Keep creation dates independent from `Было` and `Стало` close-date periods.

### 5. Implement deal-creation draft/apply behavior for KEV

The KEV creation-date fields currently write directly to applied filters.

Add separate draft state for:

```text
dealCreatedFrom
dealCreatedTo
```

Requirements:

- Initialize drafts from applied KEV filters.
- Draft edits must not trigger report requests or browser-storage changes.
- Validate complete ISO dates and reverse ranges.
- Add an explicit `Применить даты создания` action.
- Applying valid drafts updates applied values.
- Reset clears both draft and applied creation dates.
- Invalid applied creation ranges disable the KEV query and show validation UI.
- Keep creation dates independent from existing close-date filters.

### 6. Complete active-filter badge counts

Include all currently omitted filters.

Contacts:

- `categoryId`.

Deals:

- `categoryId`.

ABC:

- `categoryId`;
- `dealCreatedFrom`;
- `dealCreatedTo`.

KEV:

- `categoryId`;
- `dealCreatedFrom`;
- `dealCreatedTo`.

Add focused pure frontend helper tests when practical, or document an explicit operator verification.

### 7. Validate cached funnel metadata

Update cached filter metadata validation.

Requirements:

- `categories` must be an array.
- Every category must contain a non-negative integer `category_id`.
- Every category must contain a non-empty trimmed `category_name`.
- Invalid category entries must not make cached metadata appear valid.
- Preserve safe fallback to fresh metadata or no metadata.
- Funnel select values remain numeric category IDs encoded as strings in the frontend.
- Funnel labels remain category names.

### 8. Clean up frontend formatting

The current implementation still contains compressed one-line JSX and malformed comma placement.

Requirements:

- Reformat the newly touched funnel/date/footer sections to match existing repository style.
- Do not globally reformat unrelated code.
- Keep behavior unchanged outside this task.

### 9. Add missing tests

Add or update tests proving the remaining acceptance behavior:

- Contacts sorts by average check ascending and descending.
- Contacts sorts by average cycle ascending and descending.
- Null average values are deterministic and do not crash sorting.
- Funnel filters work in Contacts, Deals, ABC, and KEV.
- ABC deal-creation filtering remains inclusive.
- KEV deal-creation filtering remains inclusive and composes with close dates.
- Contacts and Deals summaries are calculated before pagination.
- Weighted average check uses underlying won deals, not average-of-averages.
- Weighted average cycle uses underlying valid closed deals.
- Open and negative-cycle deals are excluded.
- Empty denominators return `null`.
- Funnel metadata response remains sorted and typed.
- Category-list pagination and exact category-aware stage behavior remain covered.
- Unknown category/stage continues to fail safely without replacing the active dataset.
- Contact `661` analytical assignment regression remains correct.

Do not reduce existing test coverage to make the suite pass.

### 10. Update documentation

Update all required documentation to match the final implementation:

- `SPEC.md`;
- `backend/README.md`;
- `frontend/README.md`;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/deployment.md`;
- `docs/project-status.md`;
- `.ai/report.md`.

Document at minimum:

- funnel directory and exact category filtering;
- category-aware stage resolution;
- creation-date filters in all four reports;
- ABC/KEV draft/apply behavior;
- average check and cycle semantics;
- filter-wide footer semantics;
- required manual `Обновить из Bitrix` after deployment;
- Docker startup still does not refresh data automatically.

`.ai/report.md` must contain only the current task report and exact executed checks. Do not claim functionality that is not present in code.

## Out Of Scope

- Live Bitrix calls.
- Any Bitrix write operation.
- New reports or charts.
- Stage-history or time-in-stage analytics.
- Responsible-manager analytics.
- Automatic or scheduled refresh.
- Background queues.
- Production deployment itself.
- Unrelated refactoring or visual redesign.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, `SPEC.md`, and current documentation.
- Keep Bitrix strictly read-only.
- The allowed funnel read method remains:

```text
crm.category.list
```

- Never add or call:

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

### Backend

- Average check and average cycle sort fields work end to end.
- Funnel and creation-date filters remain correct and inclusive.
- Filter-wide totals and weighted averages remain calculated before pagination.
- Complete backend suite passes.

### Frontend

- Deals headers, body cells, and footer align exactly.
- Deals footer shows status counts, average cycle, budget, profit, and average check.
- ABC creation dates use draft/apply/validation/reset behavior.
- KEV creation dates use draft/apply/validation/reset behavior.
- Active-filter badges count every new funnel and creation-date filter.
- Cached categories are validated safely.
- Contacts-to-Deals filter propagation remains working.
- Frontend build passes.

### Documentation and safety

- All required documentation is updated.
- `.ai/report.md` is accurate and contains only this task.
- No Bitrix write methods or wildcard selects are added.
- No live Bitrix calls occur.
- No secrets or generated/private data are committed.
- Docker startup behavior remains unchanged.

## Checks

Before implementation:

```bash
git log --oneline -5
git status --short
```

Complete backend suite:

```bash
cd backend
python -m pytest
```

If dependencies are unavailable, use the existing Docker/dev environment:

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
- browser/operator verification confirms Deals alignment and ABC/KEV draft/apply behavior;
- `.ai/report.md` contains accurate exact results;
- all required documentation is updated;
- only task-related files and `.ai/report.md` are staged;
- no secrets, databases, snapshots, generated files, caches, `node_modules`, `frontend/dist`, or `ui-kits` changes are staged;
- no live Bitrix call was made;
- no Bitrix write method was added;
- Docker startup behavior remains unchanged.

Set `.ai/report.md` status to `done` only after all criteria and checks pass.

Commit message:

```text
codex: TASK-2026-07-20-03 Fix remaining funnel analytics blockers
```
