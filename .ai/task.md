# Task: TASK-2026-06-22-08

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-07`

## Title

Improve contacts USD and refresh UX

## Goal

Improve the first real Contacts screen after user testing:

- avoid misleading original-currency totals as the main financial metric;
- show USD revenue/profit metrics already calculated by the backend;
- make manual data refresh progress and completion states clear for the user.

Keep scope narrow: this is still the Contacts screen only. Do not add dashboard, ABC, RFM, deal-cycle, stale-deal, concentration, or type/region screens.

## Current Problem

The Contacts screen currently displays `total_amount_original` from:

```text
GET /api/reports/contacts
```

That field is a sum of original deal amounts and is not converted to USD. Because contacts can have deals in different currencies, this is not a reliable financial metric.

The backend already has converted metrics in:

```text
GET /api/reports/contacts/analytics
```

Relevant fields include:

- `revenue_usd`;
- `estimated_profit_usd`;
- `first_won_date`;
- `last_won_date`;
- `latest_deal_date`;
- `has_sales`.

Also, the current refresh UI can temporarily show confusing text such as `Manual Bitrix refresh completed.` while the panel still says the local database is not prepared. The user needs clearer loading/progress/result indicators.

## Product Scope

### 1. Contacts table financial columns

Update the Contacts screen to use USD analytics as the primary financial data.

Expected table columns after the change:

- contact name;
- raw type, if still useful;
- normalized type;
- region;
- total deals count;
- won/open/lost deals count;
- `Выручка USD` from `revenue_usd`;
- `Расчетная прибыль USD` from `estimated_profit_usd`;
- optional sales/date fields if they fit cleanly, e.g. latest deal date.

Do not present `total_amount_original` as the main financial metric. If kept, label it clearly as diagnostic/original and do not imply it is converted.

### 2. API usage

Prefer using existing backend endpoints:

- `GET /api/reports/contacts/analytics` for table data;
- `GET /api/meta/filters`;
- `GET /api/datasets/status`;
- `POST /api/local/refresh-data`.

Do not create a new report endpoint unless there is a strong reason. If a tiny backend fix is required for parity of filters/pagination, keep it scoped and covered by tests.

The existing analytics endpoint supports `limit`, `offset`, `search`, `contact_type`, `region`, and date filters. If status filtering is not available there, either:

- remove/disable the status filter on this screen with a clear reason in `.ai/report.md`; or
- add status support to the analytics endpoint if it is small, consistent with the existing contacts endpoint, and tested.

Do not silently keep a status filter that no longer affects results.

### 3. Refresh UX

Improve manual refresh UX on the Contacts screen:

- while refresh is running, show a clear blocking/progress state:

```text
Загрузка данных из Bitrix...
Это может занять несколько минут.
```

- disable duplicate refresh clicks;
- after successful refresh, show a concise success state/counts before or while refetching table data, for example:

```text
Обновление завершено: 14216 контактов, 9142 сделок, курсы загружены.
```

- avoid displaying backend technical text like `Manual Bitrix refresh completed.` as the main user message;
- after success, refetch dataset status, filters, and Contacts table;
- after failure, show a clear error and keep the refresh button available.

### 4. Preserve existing behavior

Keep:

- Docker starts services only, no auto-refresh;
- user explicitly triggers refresh;
- existing local active dataset loads immediately;
- no Bitrix calls except when user clicks `Обновить из Bitrix`;
- no Bitrix write methods;
- no forbidden personal fields displayed.

## Backend Scope

Backend changes are allowed only if needed to support the improved Contacts table cleanly.

Possible acceptable backend changes:

- add status filter support to `GET /api/reports/contacts/analytics`, matching existing `GET /api/reports/contacts` behavior;
- add/adjust tests for analytics pagination/filter behavior;
- keep response safe and typed.

Forbidden backend changes:

- new report family;
- new Bitrix methods;
- Bitrix write methods;
- changed currency conversion formula;
- changed contact type mapping/priority rules.

## Frontend Scope

Update only the existing frontend Contacts screen and API client types.

Requirements:

- use `ContactAnalyticsPageResponse` shape if switching to `/api/reports/contacts/analytics`;
- format USD money clearly, e.g. `$12,345.67` or `12 345,67 USD` consistently;
- keep loading/error/empty states;
- keep pagination;
- keep search/type/region filters;
- handle status filter correctly as described above;
- keep design-system styling.

## Documentation And Report

Update:

- `.ai/report.md` — what changed, endpoint used, financial metric behavior, refresh UX, checks;
- `frontend/README.md` and/or `docs/development.md` only if user flow changed materially;
- `docs/project-status.md` — Contacts screen now uses USD analytics metrics.

## Out Of Scope

- Dashboard.
- ABC/RFM screens.
- Deal reconciliation screen.
- Stale deals/cycle/concentration/type-region screens.
- Automatic refresh.
- Background queue.
- Auth.
- Production deployment.
- UI redesign.
- Design-system restructuring.
- CSV export.

## Acceptance Criteria

- Contacts screen no longer uses original-currency sum as the primary financial metric.
- Contacts screen displays USD revenue and estimated profit from backend analytics.
- Search/type/region filters and pagination still work.
- Status filter is either supported correctly or removed/disabled with explicit report note.
- Manual refresh running state is clear and blocks duplicate clicks.
- Manual refresh success state shows useful user-facing counts/status, not only backend technical text.
- No forbidden personal fields are displayed.
- No Bitrix calls happen unless the user triggers refresh.
- No Bitrix write methods are added or called.
- `npm run build` passes from `frontend/`.
- Backend tests run if backend code changes.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-08 Improve contacts USD and refresh UX
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run frontend checks:

```bash
cd frontend
npm run build
```

Run backend tests if backend code changes:

```bash
cd backend
python -m pytest
```

Use the existing backend dev environment if system Python lacks pytest and document the exact command.

Run Compose smoke checks if Docker is available:

```bash
docker compose config
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
docker compose down -v
```

Do not run live Bitrix refresh unless the user explicitly asks. Use mocked tests for refresh UX/API changes where practical.

Before committing:

```bash
git status --short --branch
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

If any required check cannot be run, document the exact reason in `.ai/report.md`.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- the latest relevant commit is this planner commit;
- `.ai/report.md` is updated;
- every required check is either run and reported, or explicitly documented as not run with reason;
- `.ai/report.md` explicitly states whether any live Bitrix refresh was or was not run;
- `.ai/report.md` explicitly states that no Bitrix write methods were added or called;
- staged files are only files intentionally changed for `TASK-2026-06-22-08` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
