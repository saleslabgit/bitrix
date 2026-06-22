# Task: TASK-2026-06-22-22

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-21`

## Title

Add Deals revenue total

## Goal

Add `Выручка` to the Deals report totals bar, next to the existing budget and profit totals.

Also simplify the totals labels by removing `по фильтру` from the visible UI labels.

## User Request

On the Deals page, in the totals bar currently showing:

```text
Бюджет по фильтру
Прибыль по фильтру
```

add one more metric:

```text
Выручка
```

And remove `по фильтру` from the visible labels.

The visible labels should become:

```text
Бюджет
Выручка
Прибыль
```

## Facts

- Current Deals report is implemented in `frontend/src/App.tsx`.
- Current Deals totals are displayed by `DealTotalsBar` above and below the Deals table.
- Current Deals backend page response includes:
  - `filtered_budget_usd`;
  - `filtered_estimated_profit_usd`.
- Current Deals budget total sums all filtered deals before pagination.
- Current Deals profit total is won-only: `budget_usd * 0.50` for won deals, otherwise `0.00`.
- Current Deal row `estimated_profit_usd` already follows won-only semantics.
- Revenue in this project means won-only USD revenue.
- Frontend must call only local backend endpoints.
- Report APIs must read local DuckDB-backed data only.
- Bitrix is read-only and must not be called from report page loads.

## Assumptions

- Deals `Выручка` total should be calculated across all currently filtered Deals rows before pagination.
- Deals `Выручка` total should sum `budget_usd` only for filtered rows where `status_group == "won"`.
- If the active filter is `status=open` or `status=lost`, `Выручка` should be `0.00`.
- If the active filter is `status=won`, `Выручка` should equal `Бюджет` for the filtered set.
- The backend field can be named clearly, recommended:

```text
filtered_revenue_usd
```

- Even though visible labels should not say `по фильтру`, the values are still filtered totals based on the current Deals filters.

## Unknowns

- Browser-level visual verification depends on the execution environment. If unavailable, document the limitation in `.ai/report.md`.

## Scope

### 1. Backend Deals revenue total

Extend the Deals analytics page response with a filtered revenue total.

Requirements:

- Add a backend page field, recommended `filtered_revenue_usd`.
- Compute it across all filtered Deals rows before pagination.
- Include all current Deals filters:
  - `deal_id`;
  - `client_id`;
  - `client_search`;
  - `status`;
  - `contact_type`;
  - backend-supported `region`;
  - created-date range.
- Revenue must be won-only: sum `budget_usd` / `amount_usd` only for rows where `status_group == "won"`.
- Empty result should return `0.00`.
- Do not change existing `filtered_budget_usd` or `filtered_estimated_profit_usd` semantics.
- Do not add persisted analytics tables or migrations.
- Do not call Bitrix, NBRB, or external services from the report endpoint.

Update response models and API types accordingly.

### 2. Frontend totals bar labels and layout

Update the Deals totals bar in `frontend/src/App.tsx`.

Requirements:

- Display three totals both above and below the Deals table:
  - `Бюджет`;
  - `Выручка`;
  - `Прибыль`.
- Remove `по фильтру` from visible labels.
- Keep USD formatting consistent with existing totals.
- Keep loading, error, invalid date, and empty states from showing misleading stale totals.
- Keep the layout compact and stable with three total chips.

### 3. Tests

Add focused backend tests covering:

- revenue total includes won deals only;
- revenue total is computed across all filtered rows before pagination;
- revenue total respects `client_id` and `status` filters;
- `status=open` or `status=lost` revenue total is `0.00`;
- existing budget/profit totals remain unchanged.

Frontend tests are not currently established; run the frontend build.

### 4. Documentation and report

Update relevant docs when behavior changes, at minimum consider:

- `frontend/README.md` for the three Deals totals;
- `docs/development.md` for Deals response fields;
- `docs/data-model.md` for Deals page revenue total semantics;
- `docs/project-status.md` if useful.

Update `.ai/report.md` with:

- backend field added;
- revenue semantics;
- frontend label changes;
- checks run;
- confirmation that no Bitrix calls/write methods were added.

## Out Of Scope

- Changing row-level Deals table columns.
- Changing Contacts report metrics.
- Changing budget/profit semantics.
- Implementing/correcting region normalization logic.
- New report screens.
- URL routing/query-string routing.
- Changing Bitrix ingestion, extraction, contact-deal link logic, reconciliation, or manual refresh behavior.
- Any live Bitrix diagnostic call.
- Any Bitrix write operation.
- Displaying forbidden personal fields or raw Bitrix rows.
- Adding CSV/export, authentication, scheduler, or automatic refresh.
- Modifying `ui-kits/`.

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

## Acceptance Criteria

- Deals backend response includes `filtered_revenue_usd` or an equivalently clear field name.
- Deals revenue total is won-only and computed before pagination.
- Deals revenue total respects current filters, including `client_id` and `status`.
- Existing Deals budget and profit totals keep their current semantics.
- Deals totals bar shows three labels: `Бюджет`, `Выручка`, `Прибыль`.
- Visible labels no longer include `по фильтру`.
- Totals are shown both above and below the Deals table as before.
- Loading/error/empty/invalid-date states remain clear and do not show stale totals.
- Frontend still calls only local backend endpoints.
- Backend report endpoints do not call Bitrix, NBRB, or external services.
- No Bitrix write methods are added.
- Relevant backend tests and frontend build pass, or any inability is explicitly documented with reason.
- Documentation and `.ai/report.md` are updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-22 Add Deals revenue total
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
- Deals revenue total is implemented, tested, and documented;
- visible Deals totals labels are exactly `Бюджет`, `Выручка`, `Прибыль`;
- no existing budget/profit semantics regress;
- no frontend Bitrix calls are added;
- no Bitrix write methods are added anywhere;
- required backend tests and frontend build are run, or inability is explicitly documented;
- `.ai/report.md` describes implementation, checks, facts, unknowns, and risks;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
