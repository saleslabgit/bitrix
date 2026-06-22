# Task: TASK-2026-06-22-27

Status: planned
Created from: current `main` after `TASK-2026-06-22-26`

## Title

Fix filter metadata 500 root cause

## Goal

Eliminate the intermittent browser console error:

```text
GET /api/meta/filters 500 (Internal Server Error)
```

This must be fixed at the backend/root-cause level, not hidden in the frontend.

## User Request

The user still sees periodic console errors on the frontend:

```text
GET http://localhost:5173/api/meta/filters 500 (Internal Server Error)
```

The previous task removed the expected `503`, but the endpoint now sometimes returns a real `500`.

## Facts

- `TASK-2026-06-22-26` removed the explicit `HTTPException(503)` guard from `meta_filters()`.
- Current `meta_filters()` now does only:

```python
filters = get_filter_metadata(get_connection())
return FilterMetadataResponse.model_validate(filters)
```

- `get_connection()` in `backend/app/local_database.py` keeps one global DuckDB connection in `_connection`.
- FastAPI sync endpoints run in a worker threadpool.
- The frontend can trigger concurrent backend requests, for example:
  - `GET /api/datasets/status`;
  - `GET /api/meta/filters`;
  - `GET /api/reports/contacts/analytics`;
  - `GET /api/reports/deals/analytics`;
  - `GET /api/reports/abc/analytics`.
- A single shared DuckDB connection used concurrently from multiple FastAPI worker threads is a likely root cause of intermittent `500` responses.
- `get_connection()` also calls `initialize_schema()` on each access, so schema initialization/DDL may happen on hot read paths and under concurrent requests.
- Report page loads must remain local-only and must not call Bitrix.

## Assumptions

- The `500` is caused by backend storage/concurrency behavior, not by Vite or Bitrix.
- The durable local DuckDB file is the normal runtime storage for Docker/local app usage.
- In-memory DuckDB is mostly for tests and must not be broken silently.

## Unknowns

- The exact runtime traceback is not known from GitHub alone.
- The bug may be caused by shared connection concurrency, repeated schema initialization, a DuckDB lock/conflict, or response validation after an unexpected row type.

## Required Investigation Before Fix

Before implementing the fix, Codex must inspect the actual failure path.

Required actions:

- Run the app/backend enough to call `GET /api/meta/filters` through HTTP if practical.
- Inspect backend logs/traceback for the `500`.
- If the exact user timing is hard to reproduce manually, add a focused concurrent test that stresses local metadata/status/report reads against the same prepared DuckDB database.
- Do not conclude “frontend cache issue” unless backend HTTP status is proven stable.

Record the observed traceback or the reason it could not be reproduced in `.ai/report.md`.

## Scope

### 1. Fix backend local DB access stability

Fix the backend so normal concurrent report page requests do not make `/api/meta/filters` return `500`.

Recommended direction:

- Review `backend/app/local_database.py` and `backend/app/storage/connection.py`.
- Avoid unsafe concurrent use of one global DuckDB connection from multiple FastAPI worker threads.
- Avoid repeated schema initialization on every hot read request if it contributes to contention.
- Prefer a small, explicit local database access pattern that matches the current codebase:
  - either thread-local/read-safe DuckDB connections for file-backed runtime storage;
  - or a clearly scoped lock/connection helper if that is the least risky option;
  - or another verified DuckDB-safe pattern.

Important requirements:

- Preserve transaction safety of manual refresh and activation.
- Preserve tests that rely on temporary DuckDB paths.
- Preserve `reset_connection()` behavior for tests.
- Do not introduce a broad background job or queue.
- Do not make report page loads call Bitrix.
- Do not swallow real unexpected storage exceptions silently; the goal is to remove the normal intermittent failure, not hide all failures.

### 2. Stabilize `/api/meta/filters`

Required behavior:

- In normal active dataset usage, repeated and concurrent `GET /api/meta/filters` returns `200` with `FilterMetadataResponse`.
- Empty option lists remain allowed typed payloads.
- The endpoint must not return `500` because another report/status request happens at the same time.
- The endpoint must not return `500` because schema initialization runs concurrently on a prepared database.

### 3. Frontend

Frontend changes are not the primary fix.

Only change frontend if needed after backend is stable. If changed:

- keep cached filter metadata fallback;
- do not clear dropdowns on transient empty metadata;
- do not hide real active report errors that affect table data.

### 4. Tests

Add or update tests to cover the real failure mode.

Required backend coverage:

- existing `tests/test_api_local.py` metadata tests still pass;
- a concurrent read test against a prepared local dataset repeatedly calls metadata/status/report read functions or HTTP endpoints and asserts no exception/500;
- `meta_filters()` still returns typed empty metadata before dataset preparation;
- `meta_filters()` still returns typed metadata after synthetic dataset preparation.

If the fix touches shared local DB connection management, run the full backend test suite.

### 5. Documentation and report

Update relevant docs if local DB access behavior changes.

Update `.ai/report.md` with:

- actual or reproduced root cause;
- what changed in DB access or endpoint behavior;
- changed files;
- checks run;
- whether HTTP/browser/runtime smoke was run;
- remaining risks.

## Out Of Scope

- New filters or columns.
- ABC calculation changes.
- Contacts/Deals report semantics.
- Manual Bitrix refresh feature changes beyond preserving safety.
- Calling Bitrix from report pages.
- Editing `ui-kits/`.
- Hiding the console error only by muting frontend logging while backend still returns `500`.

## Constraints

- Work only from current GitHub repository files.
- Keep Bitrix read-only.
- Do not add CRM write methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit `.env`, DuckDB, Parquet, CSV, raw data, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Do not use `git add .`.

## Acceptance Criteria

- `/api/meta/filters` no longer intermittently returns `500` during normal frontend usage.
- Concurrent local reads involving `/api/meta/filters` and other report/status reads are covered by a test or documented runtime smoke and do not fail.
- The fix addresses backend root cause, not only frontend display.
- Metadata endpoint still returns typed `200` responses for empty metadata states.
- Manual refresh/activation behavior remains transaction-safe.
- No Bitrix calls are added to report page load paths.
- No CRM write methods are added.
- Relevant tests pass and `.ai/report.md` is updated.

## Checks

Required before implementation:

```bash
git log --oneline -5
git status --short
```

Backend checks:

```bash
cd backend && python -m pytest tests/test_api_local.py
```

If shared DB connection/storage code changes, run full backend tests:

```bash
cd backend && python -m pytest
```

Frontend checks, only if frontend code changes:

```bash
cd frontend && npm run build
```

Runtime smoke if practical:

```bash
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:8000/api/meta/filters
curl -f http://localhost:8000/api/datasets/status
```

If using Docker runtime smoke, inspect backend logs for `/api/meta/filters` tracebacks and document the result.

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src
```

## Hard Workflow Gate

Before committing, verify:

- only task-related files are staged;
- no forbidden artifacts are staged;
- `ui-kits/` is not staged;
- `.ai/report.md` includes traceback/reproduction findings;
- backend tests are recorded;
- full backend tests are recorded if shared DB connection code changed;
- runtime smoke result is recorded if run;
- no Bitrix write methods were added.

Commit message:

```text
codex: TASK-2026-06-22-27 Fix filter metadata 500 root cause
```