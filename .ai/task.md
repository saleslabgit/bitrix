# Task: TASK-2026-06-22-16

Status: planned
Created from: current `main` after `TASK-2026-06-22-15`

## Title

Fix Contacts filter stability bugs

## Goal

Fix three user-reported bugs in the existing Contacts screen and its local backend filter metadata endpoint:

1. Dropdown filters sometimes become empty over time.
2. Deal creation date inputs refetch/update the table while the user is typing; the table should update only when a date is actually selected/applied.
3. Browser console periodically shows `GET /api/meta/filters` returning `500 Internal Server Error`.

This is one bug-fix milestone for the existing Contacts screen only.

## Facts

- The user reproduced these bugs after TASK-15 was deployed locally.
- Current Contacts screen uses `filterQuery.data?.contact_types ?? []`, `filterQuery.data?.regions ?? []`, and `filterQuery.data?.statuses ?? []` directly for select options.
- If `filterQuery` errors and has no current data, the dropdown options become empty arrays.
- Current Contacts screen disables dropdowns when `filterQuery.isPending || filterQuery.isError`.
- Current date inputs write directly into `filters.dealCreatedFrom` and `filters.dealCreatedTo` on every `onChange`, which changes the contacts query key and can trigger table fetches while the user is still typing/editing the date.
- Current `GET /api/meta/filters` calls `get_filter_metadata(get_connection())` and returns `FilterMetadataResponse`.
- Current `backend/app/reports/local.py::get_filter_metadata()` queries `normalized_contacts` and `normalized_deals` directly.
- Report APIs must read local DuckDB-backed data only and must not call Bitrix or NBRB.
- Bitrix remains read-only. This task must not change extraction, normalization, manual refresh, contact selection, currency conversion, or Bitrix calls.

## Assumptions

- Empty dropdowns are at least partly a frontend resilience bug: metadata fetch failures should not erase the last known good options.
- The `500` must still be diagnosed and fixed or defensively handled on the backend. Do not only hide the error in the UI.
- Date filter UX can stay native and compact; no new date-picker dependency is needed.
- A date should be considered selected/applied only when it is a complete valid ISO date `YYYY-MM-DD` selected by the native date control or explicitly committed from the input. Partial typing must not change the active backend query.
- Clearing an already applied date should clear that filter deliberately, but avoid refetching repeatedly for transient partial input states.

## Unknowns

- The exact backend exception behind `/api/meta/filters` 500 is not known from the user report. Codex must inspect/reproduce locally where possible, add tests around the discovered failure mode, and document the root cause in `.ai/report.md`.
- Browser-level behavior of native `type="date"` differs slightly by browser. The implementation should be robust enough that partial typing does not update active filters/query keys.

## Scope

### 1. Diagnose and fix `/api/meta/filters` 500

Investigate `GET /api/meta/filters` failures using current backend code.

Expected backend outcome:

- `/api/meta/filters` should not return 500 for normal local states:
  - no prepared dataset / empty initialized schema;
  - active dataset with normalized contacts/deals;
  - dataset with no contacts or no deals;
  - all `closed_at` values NULL;
  - while filter metadata has no distinct values yet.
- If a true unexpected storage error happens, the API should still return a safe user-facing error without secrets, raw rows, local paths, or stack traces.
- Prefer fixing the root cause over swallowing all errors.
- Keep response shape unchanged: `contact_types`, `regions`, `statuses`, `min_created_at`, `max_created_at`, `min_closed_at`, `max_closed_at`.
- Do not add Bitrix/NBRB calls.

Implementation guidance:

- Ensure `get_filter_metadata()` is safe when called directly as well as through `get_connection()` if appropriate.
- Consider `initialize_schema(connection)` inside report helper if current local report helpers rely on callers too much.
- Add focused backend tests for the root cause and for empty/local unprepared states.

### 2. Keep dropdown options stable on frontend metadata errors

Update Contacts UI so transient metadata errors do not wipe dropdown options.

Requirements:

- Keep the last successful filter metadata in component state or use an equivalent TanStack Query v5 pattern.
- Select option lists should use last successful metadata when the current metadata request is pending or failed.
- Do not replace options with empty arrays after a metadata 500 if previous metadata exists.
- Do not clear selected `contactType`, `region`, or `status` merely because metadata refetch failed.
- The UI should still show a clear alert when metadata cannot be refreshed.
- Retry should still work.
- If there has never been successful metadata, the dropdowns may be disabled/empty with an error alert.

### 3. Fix deal creation date input behavior

Update date input UX so the table query changes only when a date is actually selected/applied.

Requirements:

- Maintain separate draft values for `dealCreatedFrom` and `dealCreatedTo` if needed.
- Do not update active `filters.dealCreatedFrom` / `filters.dealCreatedTo` for partial/in-progress typed values.
- Commit an active date filter only for complete valid `YYYY-MM-DD` values.
- Native date-picker selection should still update the table without requiring an extra page reload.
- Clearing a date should clear the active date filter in a controlled way.
- Date filters should still persist across reload after they are applied.
- Reset must clear drafts, active filters, persisted state, and table query state.
- Invalid range (`from > to`) should still show clear validation and avoid backend request.

Possible acceptable UX patterns:

- Commit on native `change` only when `event.currentTarget.validity.valid` and value is complete; ignore partial input; or
- Use date drafts plus `onBlur`/Enter/apply behavior; or
- Add a compact `Применить даты` button if needed for reliable browser behavior.

Choose the smallest reliable implementation consistent with the current UI.

### 4. Preserve existing Contacts behavior

Keep all existing working behavior:

- search by contact name;
- exact contact ID filter;
- type/region/status filters;
- deal creation date range filtering through `deal_created_from` / `deal_created_to`;
- sorting, pagination, reset;
- budget columns and labels;
- Bitrix `Посмотреть` links;
- manual `Обновить из Bitrix` flow;
- persisted Contacts state;
- no disruptive auto-refetch.

### 5. Documentation and report

Update docs only if behavior/operator guidance changes. At minimum update `.ai/report.md` with:

- root cause of empty dropdowns;
- root cause or best available diagnosis of `/api/meta/filters` 500;
- date input behavior implemented;
- tests/checks run;
- confirmation that no Bitrix calls or write methods were added.

## Out Of Scope

- New screens.
- New router/query-string state layer.
- Contact creation date.
- Reworking all filters or table architecture.
- Changing Bitrix extraction, manual refresh, normal sync, diagnostics, reconciliation, normalization, contact priority rules, currency loading, ABC/RFM/concentration formulas, or data model storage columns.
- Calling Bitrix from frontend.
- Any Bitrix write operation.
- Showing phones, emails, addresses, messengers, comments, files, requisites, activities, arbitrary custom fields, webhook values, raw payloads, or raw private rows.
- Changing `ui-kits/`.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- Frontend must call only local backend endpoints.
- Report and metadata APIs must filter/read local DuckDB-backed data only.
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

- Dropdown filters do not become empty after a transient `/api/meta/filters` failure if metadata was loaded successfully before.
- Selected type/region/status filters are not cleared by metadata refresh errors.
- `/api/meta/filters` no longer returns 500 for empty initialized local DB, prepared synthetic/local dataset, no-deals/no-contacts edge cases, or the reproduced root cause.
- If metadata cannot be loaded, the UI shows a clear error and retry without destroying last known good options.
- Deal creation date inputs do not refetch/update the table for partial typing.
- Deal creation date filters still update the table when a complete valid date is selected/applied.
- Clearing date filters works deliberately and resets table offset.
- Invalid date range still avoids backend Contacts request and shows validation.
- Existing Contacts filters, sorting, pagination, reset, persisted state, refresh UX, budget columns, and Bitrix links remain working.
- No frontend Bitrix calls are added.
- No Bitrix write methods are added or called.
- Backend tests pass.
- Frontend build passes.
- `.ai/report.md` is updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-16 Fix Contacts filter stability bugs
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
- `/api/meta/filters` 500 root cause is fixed or safely handled with tests;
- frontend keeps last successful metadata instead of clearing dropdowns on metadata errors;
- date input partial typing no longer changes active Contacts query filters;
- required backend tests and frontend build are run, or any inability is explicitly documented with reason;
- `.ai/report.md` states root causes/diagnosis and confirms no Bitrix calls or write methods were added;
- frontend still calls only local backend endpoints, not Bitrix;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
