# Task: TASK-2026-06-22-17

Status: planned
Created from: current `main` after `TASK-2026-06-22-16`

## Title

Harden Contacts filter metadata against empty snapshots

## Goal

Fix the remaining Contacts filter bug reported by the user:

- the `Тип` dropdown still becomes empty after some time;
- browser reload restores it;
- this must not happen.

TASK-16 protected the UI from failed `/api/meta/filters` requests. This task must also protect the UI and backend from a successful but invalid/empty metadata response while a non-empty active dataset exists.

## Facts

- The user tested TASK-16 and reported that not all fixes passed.
- The remaining reproduced symptom is specifically: dropdown `Тип` breaks/empties after time, and reload fixes it.
- Current frontend code uses:

```ts
const filterMetadata = filterQuery.data ?? lastFilterMetadata;
```

- Current frontend stores `lastFilterMetadata` only in React component state.
- Current frontend updates `lastFilterMetadata` for any truthy `filterQuery.data`, even if `contact_types` is an empty array.
- Therefore, if `/api/meta/filters` returns HTTP 200 with empty `contact_types`, the UI treats it as valid and the `Тип` dropdown becomes empty.
- Current backend `get_filter_metadata()` returns empty tuples for empty `normalized_contacts` / `normalized_deals` states.
- Empty metadata is valid only when there is no prepared/active dataset or when the active dataset truly has no contacts. It is suspicious/invalid when `GET /api/datasets/status` reports an active successful dataset with `normalized_contacts_count > 0`.
- Current `GET /api/datasets/status` exposes active dataset counts, including `normalized_contacts_count` and `normalized_deals_count`.
- Frontend and report APIs must call only local backend endpoints. Bitrix remains read-only and is not involved in metadata loading.

## Assumptions

- The remaining bug is caused by a transient successful empty metadata snapshot, not by a rejected request. This matches the observed behavior and current code path.
- For a non-empty active dataset, `contact_types` should never be empty because normalized contacts must have a normalized type such as `Не определено` or a real configured type.
- Persisting the last valid metadata in browser storage is acceptable because it stores only safe aggregate filter option labels, not backend rows, secrets, raw payloads, or personal fields.
- A successful metadata response should be considered valid for Contacts filters only if it is consistent with the active dataset state.

## Unknowns

- The exact timing source of the empty metadata snapshot is not proven. It may be a transient read during dataset replacement, a backend connection/storage edge case, or a frontend remount/cache edge case. Codex must document the observed/reproduced condition or the best-supported diagnosis in `.ai/report.md`.
- There is no frontend test framework beyond TypeScript build. Implement focused pure helper functions if useful, but do not add a full test framework just for this fix.

## Scope

### 1. Backend: reject inconsistent empty filter metadata for active datasets

Update the backend metadata endpoint so it does not return a successful empty `contact_types` response when the active dataset says contacts exist.

Expected behavior:

- If there is no active dataset, empty metadata is allowed.
- If the active dataset exists but has `normalized_contacts_count == 0`, empty `contact_types` is allowed.
- If the active dataset is successful/active and has `normalized_contacts_count > 0`, then `contact_types` must be non-empty.
- If this consistency check fails, return a safe non-200 error, preferably `503 Service Unavailable`, with a short user-facing message like `Filter metadata is temporarily unavailable. Keep previous options and retry.`
- Do not include stack traces, local paths, row samples, contact/deal names, webhook values, or secrets.
- Keep normal valid response shape unchanged.
- Do not call Bitrix, NBRB, or external services.

Implementation guidance:

- The consistency check can live in `backend/app/main.py::meta_filters()` or a small helper near local report metadata.
- Use `get_dataset_storage_status(connection)` / active dataset metadata or current safe row counts already available in storage helpers.
- Add backend tests for:
  - active dataset reports `normalized_contacts_count > 0` while metadata `contact_types` is empty => endpoint returns a safe error, not HTTP 200 with empty options;
  - no active dataset / empty schema still returns empty metadata safely;
  - valid active dataset still returns non-empty contact types.

### 2. Frontend: validate metadata before replacing options

Update frontend metadata handling so an invalid successful payload cannot wipe dropdowns.

Requirements:

- Add a validation/sanity function for Contacts filter metadata.
- If active dataset has `normalized_contacts_count > 0`, metadata with empty `contact_types` must be treated as invalid for dropdown replacement.
- Do not set `lastFilterMetadata` from invalid metadata.
- Do not use invalid `filterQuery.data` over cached metadata.
- Preserve the last valid metadata when current metadata is invalid, pending, or failed.
- If there is no valid cached metadata yet, show a clear alert and keep dropdowns disabled/empty.
- If cached metadata exists and current metadata is invalid, keep dropdowns populated and show a clear warning/alert that filters could not be refreshed.
- Do not clear selected `contactType`, `region`, or `status` due to invalid metadata.

### 3. Frontend: persist last valid metadata cache

Store last valid filter metadata in browser storage so a component remount or transient invalid metadata does not leave the UI with empty options.

Preferred storage key:

```text
bitrix-sales.filter-metadata.v1
```

Requirements:

- Store only safe metadata option labels and date range values from `/api/meta/filters`.
- Validate/coerce stored metadata before using it.
- Use persisted metadata only as a fallback; a valid fresh response should replace it.
- Clear or replace the cache only when a valid fresh metadata response is received or when the user explicitly resets all local UI state if that reset is intended to clear metadata too. Prefer not to delete metadata cache on normal Contacts filter reset, because filter reset should not make dropdown options disappear.
- Do not store contacts rows, deal rows, secrets, raw payloads, webhook values, or personal fields.

### 4. Improve user-visible metadata diagnostics

Make the UI state understandable:

- If fresh metadata request fails but cached metadata is used, show a non-blocking alert/warning while keeping selects usable.
- If fresh metadata response is invalid/empty for an active non-empty dataset, show a similar alert/warning and keep cached selects usable.
- If no cached metadata exists, show the current hard error state and disabled dropdowns.
- Keep wording short and operator-focused.

### 5. Preserve existing behavior

Do not regress:

- search by contact name;
- exact contact ID filter;
- type/region/status filters;
- deal creation date drafts and `Применить даты` behavior;
- deal creation date range filtering through `deal_created_from` / `deal_created_to`;
- sorting, pagination, reset;
- budget columns and labels;
- Bitrix `Посмотреть` links;
- manual `Обновить из Bitrix` flow;
- persisted Contacts state;
- no disruptive auto-refetch.

### 6. Report and docs

Update `.ai/report.md` with:

- why TASK-16 was insufficient;
- exact invalid metadata condition now handled;
- backend consistency behavior;
- frontend cache key and validation behavior;
- checks run;
- confirmation that no Bitrix calls or write methods were added.

Update docs only if operator/developer behavior changes enough to mention the metadata cache.

## Out Of Scope

- New screens.
- New router/query-string state layer.
- Contact creation date.
- Reworking all filters or table architecture.
- Adding a frontend test framework.
- Changing Bitrix extraction, manual refresh, normal sync, diagnostics, reconciliation, normalization, contact priority rules, currency loading, ABC/RFM/concentration formulas, or data model storage columns.
- Calling Bitrix from frontend.
- Any Bitrix write operation.
- Showing phones, emails, addresses, messengers, comments, files, requisites, activities, arbitrary custom fields, webhook values, raw payloads, or raw private rows.
- Changing `ui-kits/`.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- Frontend must call only local backend endpoints.
- Report and metadata APIs must read local DuckDB-backed data only.
- Do not add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit `.env`, DuckDB files, Parquet snapshots, raw exports, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Keep the Contacts UI dense and operational.

## Acceptance Criteria

- The `Тип` dropdown does not become empty when a transient metadata response is empty/invalid and a previous valid metadata cache exists.
- The frontend never replaces non-empty cached `contact_types` with an empty `contact_types` payload while active dataset `normalized_contacts_count > 0`.
- Last valid filter metadata survives component remount/browser reload through safe browser storage.
- `/api/meta/filters` does not return HTTP 200 with empty `contact_types` when an active successful dataset reports `normalized_contacts_count > 0`.
- Safe backend error is returned for inconsistent active metadata, without secrets or raw data.
- A fresh valid metadata response still replaces the cache.
- Normal empty metadata before any active dataset remains supported.
- Existing date apply behavior, filters, sorting, pagination, reset, refresh UX, budget columns, and Bitrix links remain working.
- No frontend Bitrix calls are added.
- No Bitrix write methods are added or called.
- Backend tests pass.
- Frontend build passes.
- `.ai/report.md` is updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-17 Harden Contacts filter metadata against empty snapshots
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

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- latest relevant commit is this planner commit;
- backend rejects inconsistent empty metadata for active non-empty datasets;
- frontend validates metadata before using it;
- frontend persists and uses last valid metadata cache;
- the `Тип` dropdown cannot be wiped by a successful empty metadata response while cached valid metadata exists;
- required backend tests and frontend build are run, or any inability is explicitly documented with reason;
- `.ai/report.md` explains why TASK-16 was insufficient and what condition is now covered;
- `.ai/report.md` confirms no Bitrix calls or write methods were added;
- frontend still calls only local backend endpoints, not Bitrix;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
