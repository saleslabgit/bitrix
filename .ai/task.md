# Task: TASK-2026-06-22-26

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-25`

## Title

Stabilize filter metadata endpoint

## Goal

Stop the periodic browser console error:

```text
GET /api/meta/filters 503 (Service Unavailable)
```

The UI currently keeps working because the frontend uses cached filter metadata, but the backend should not produce expected intermittent `503` responses for normal report usage.

## User Request

The user confirmed the ABC layout works, but periodically sees this console error:

```text
GET http://localhost:5173/api/meta/filters 503 (Service Unavailable)
```

## Facts

- The frontend calls `GET /api/meta/filters` through React Query when a dataset is ready.
- The frontend already keeps the last valid filter metadata in browser storage under `bitrix-sales.filter-metadata.v1`.
- Current frontend logic validates fresh metadata and falls back to cached metadata when fresh metadata is empty/invalid.
- Current backend route `meta_filters()` intentionally raises `HTTPException(503)` when:
  - an active successful dataset exists;
  - `normalized_contacts_count > 0`;
  - `get_filter_metadata()` returns an empty `contact_types` list.
- That `503` guard was useful before the frontend cache/fallback behavior, but now it creates a noisy expected network error in the browser console.
- Contacts, Deals, and ABC reports must continue to read only local backend endpoints.
- Bitrix must remain read-only and must not be called by report page loads.

## Assumptions

- The periodic `503` is caused by the explicit guard in `backend/app/main.py`, not by Bitrix or Vite.
- For normal report usage, `/api/meta/filters` should be a stable local metadata endpoint and return a typed metadata payload whenever the local schema can be read.
- Unexpected storage/database exceptions can still surface as real backend errors; this task is not meant to hide real crashes.

## Unknowns

- The exact runtime moment when the empty `contact_types` snapshot appears is not known from GitHub alone.
- Browser visual/runtime verification may or may not be available to Codex.

## Scope

### 1. Backend endpoint behavior

Update `GET /api/meta/filters` so it does not return `503` merely because `contact_types` is empty while an active dataset exists.

Required behavior:

- If local schema can be read, return `200` with `FilterMetadataResponse`.
- Empty `contact_types`, `statuses`, or date ranges are allowed payload states.
- Do not use `503` as the normal signal for transient or empty filter metadata.
- Do not call Bitrix from this endpoint.
- Do not expose secrets, raw rows, or forbidden personal fields.

Recommended approach:

- Remove the explicit `HTTPException(503)` guard from `meta_filters()`.
- Let the frontend's existing metadata validation and cache fallback handle empty metadata snapshots.
- Keep real exceptions unhidden unless there is an existing project pattern for safe storage error mapping.

### 2. Frontend behavior

Review `frontend/src/App.tsx` and `frontend/src/api.ts` to ensure the current fallback behavior remains correct after backend no longer returns expected `503`.

Required behavior:

- If fresh metadata is empty/invalid and cached metadata is valid for the current active dataset, keep using cached metadata.
- Dropdowns must not be cleared by a transient empty metadata response.
- Do not show a user-facing error merely because fresh metadata is empty while valid cached metadata exists.
- Avoid periodic failed `/api/meta/filters` requests in normal active dataset usage.

Only change frontend code if needed to satisfy the above behavior.

### 3. Tests

Update backend tests that currently expect `503` for empty contact types.

Required coverage:

- `meta_filters()` returns `200`/response model with empty metadata before dataset is prepared.
- `meta_filters()` returns metadata normally after synthetic dataset is prepared.
- `meta_filters()` no longer raises `HTTPException(503)` when an active dataset exists but contact types are empty.
- Existing filter metadata extraction tests remain valid.

If frontend code changes, run the frontend build.

### 4. Documentation and report

Update relevant docs only if behavior documentation is materially affected.

Update `.ai/report.md` with:

- root cause;
- changed files;
- checks run;
- whether frontend build was needed/run;
- any remaining risk.

## Out Of Scope

- New filters or columns.
- ABC calculation changes.
- Contacts/Deals/ABC report data semantics.
- Re-enabling region filters/columns.
- Changing manual Bitrix refresh behavior.
- Calling Bitrix from report pages.
- Editing `ui-kits/`.

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

- Normal report usage no longer produces periodic `GET /api/meta/filters 503` browser console errors caused by empty metadata snapshots.
- `/api/meta/filters` returns a valid typed metadata response when local schema is readable, even if lists are empty.
- Dropdown options are not cleared when fresh metadata is empty and cached metadata is valid.
- No Bitrix calls are added to report page load paths.
- No CRM write methods are added.
- Relevant backend tests are updated and passing.
- `.ai/report.md` is updated.

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

If broader impact is found, run full backend tests:

```bash
cd backend && python -m pytest
```

Frontend checks, if frontend code changes:

```bash
cd frontend && npm run build
```

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src
```

## Hard Workflow Gate

Before committing, verify:

- only files related to this task are staged;
- no forbidden artifacts are staged;
- `ui-kits/` is not staged;
- `.ai/report.md` is updated;
- relevant tests/checks are recorded in `.ai/report.md`;
- no Bitrix write methods were added.

Commit message:

```text
codex: TASK-2026-06-22-26 Stabilize filter metadata endpoint
```