# Task: TASK-2026-06-22-07

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-06`

## Title

Add manual data refresh flow

## Goal

Make the project usable like a real local app after `docker compose up --build` without requiring the user to know backend internals or run hidden helper scripts.

Docker must only start services. It must not automatically call Bitrix or refresh data. The user should control data refresh explicitly from the UI.

Required user flow:

1. User runs:

```bash
docker compose up --build
```

2. User opens:

```text
http://localhost:5173
```

3. If local `data/analytics.duckdb` has an active dataset, Contacts table loads normally.
4. If local database is empty/not prepared, frontend shows a clear empty-state panel:

```text
Локальная база не подготовлена.
Нажмите «Обновить из Bitrix», чтобы загрузить данные.
```

5. User clicks `Обновить из Bitrix`.
6. Backend runs the existing read-only Bitrix manual sync, then applies approved contact type rules, reruns local normalization, and loads NBRB rates.
7. Frontend shows progress/status and then refreshes dataset status, filters, and Contacts table.
8. If sync/preparation fails, frontend shows a clear error from the safe backend status/message.

## Important Product Rules

- Bitrix remains read-only.
- No Bitrix write methods are allowed.
- Docker startup must not automatically call Bitrix.
- User must explicitly start refresh from UI.
- Existing local database must be reused if present.
- Generated local data, DuckDB, Parquet, `.env`, logs, caches, and secrets must not be staged or committed.

## Backend Scope

### 1. Add one safe operator endpoint

Add a backend endpoint for the full manual refresh flow, for example:

```text
POST /api/local/refresh-data
```

The endpoint should:

- build the existing Bitrix client from env settings;
- call existing manual read-only Bitrix sync;
- if sync succeeds, apply approved contact type rules and rerun normalization from the new raw tables;
- if sync succeeds, load NBRB currency rates for raw deals;
- return a typed safe response with status, counts, and safe messages;
- never return secrets, webhook URL, raw rows, contact/deal row samples, local absolute paths, or generated file contents.

If naming should be different to match existing conventions, choose the cleanest local/operator naming and document it.

### 2. Keep existing endpoints

Do not remove existing endpoints:

- `POST /api/bitrix/sync/run`;
- `GET /api/bitrix/sync/status`;
- `GET /api/datasets/status`;
- `GET /api/reports/contacts`.

If possible, reuse existing code instead of duplicating sync logic.

### 3. Error handling

Handle these cases safely:

- missing `BITRIX_WEBHOOK_URL`;
- invalid webhook or Bitrix request error;
- sync succeeds but local preparation fails;
- NBRB rate loading fails or unsupported currency appears.

A failed refresh must not leave the UI pretending the dataset is ready. Return enough safe status for the frontend to display a useful message.

### 4. No async job system unless necessary

This can be a synchronous MVP endpoint even if the request takes several minutes. Frontend should show a blocking loading state with clear text.

Do not add Celery/RQ/background workers/scheduler in this task.

## Frontend Scope

Update the existing Contacts screen only.

### 1. Dataset-not-ready state

When `/api/datasets/status` says there is no active successful dataset, show a prominent empty-state panel instead of just an empty Contacts table.

Panel content should explain:

- local database is not prepared;
- user can start a manual read-only refresh from Bitrix;
- refresh can take several minutes.

### 2. Refresh action

Add a button:

```text
Обновить из Bitrix
```

On click:

- call the new backend refresh endpoint;
- show loading/progress text such as `Загрузка данных из Bitrix... Это может занять несколько минут.`;
- disable duplicate refresh clicks while request is running;
- after success, refetch dataset status, filter metadata, and Contacts table;
- after failure, show a clear error message and keep the refresh button available.

### 3. Existing Contacts behavior

If dataset is ready, keep existing Contacts behavior:

- search;
- filters;
- pagination;
- loading/error/empty states.

Do not add new report screens in this task.

## Documentation And Report

Update:

- `.ai/report.md` — changed files, endpoint added, UI behavior, checks, limitations;
- `docs/development.md` — simple user flow: run Docker, open frontend, click refresh if data is not ready;
- `frontend/README.md` — same short flow;
- `docs/project-status.md` — app now has manual data refresh flow for local testing.

Mention explicitly that local databases are intentionally not committed and Docker does not auto-refresh data.

## Out Of Scope

- Automatic refresh on Docker startup.
- Scheduled refresh.
- Background job queue.
- New report screens.
- Dashboard.
- Auth/roles.
- Production deployment/Nginx/HTTPS.
- CI.
- Changing contact type business mapping.
- Changing currency conversion formulas.
- CSV export.
- Any Bitrix write method.

## Acceptance Criteria

- `docker compose up --build` starts the app without auto-calling Bitrix.
- With no active dataset, frontend shows a clear “database not prepared” state and `Обновить из Bitrix` button.
- Clicking refresh calls a backend endpoint that runs the full manual data preparation sequence:
  - read-only Bitrix sync;
  - approved contact type rules;
  - local renormalization;
  - NBRB currency rates.
- After successful refresh, Contacts table loads without manual curl/helper commands.
- Existing local active dataset still loads without forcing refresh.
- No secrets, raw rows, forbidden personal fields, local absolute paths, generated data, or Bitrix webhook values are exposed.
- No Bitrix write methods are added or called.
- Tests cover backend refresh orchestration with mocks and frontend/API behavior where practical.
- `npm run build` passes from `frontend/`.
- Backend tests run if backend code changes.
- Docs describe the simple user flow.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-07 Add manual data refresh flow
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run after implementation as applicable:

```bash
cd backend
python -m pytest
```

If system Python lacks pytest, use the existing backend dev environment and document the command.

Run frontend checks:

```bash
cd frontend
npm run build
```

Run Compose checks if Docker is available:

```bash
docker compose config
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
docker compose down -v
```

Do not run live Bitrix refresh in tests unless the user explicitly asks. Use mocked backend tests for refresh orchestration. If a live/manual refresh is run for verification, document it clearly and never print secrets or row-level data.

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
- staged files are only files intentionally changed for `TASK-2026-06-22-07` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
