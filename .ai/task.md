# Task: TASK-2026-06-22-15

Status: planned
Created from: current `main` after `TASK-2026-06-22-14` report

## Title

Persist Contacts UI state and add deal creation date filter

## Goal

Improve the existing Contacts screen so it behaves like a stable verification workspace:

- the page must not refresh/refetch by itself in a way that disrupts the current table state;
- filters, sorting, pagination, and related table state must survive a browser reload;
- the user must be able to filter Contacts analytics by deal creation date.

This task is about the existing Contacts screen only. Do not add new screens.

## Facts

- The user confirmed the current data model is workable and wants to focus on UI improvements now.
- The user explicitly decided not to add contact creation date for now.
- Current Contacts screen state is kept only in React state in `frontend/src/App.tsx`.
- Current `initialFilters` includes search, exact contact ID, contact type, region, deal status, sort, order, limit, and offset.
- Current frontend uses TanStack Query with global query `staleTime: 30_000` and default refetch behavior in `frontend/src/main.tsx`.
- Current Contacts query key is `['contacts', filters]` and fetches `/api/reports/contacts/analytics`.
- Current backend endpoint `/api/reports/contacts/analytics` already accepts `date_from` and `date_to`, but `list_contact_analytics()` applies them through `_reporting_date(deal)`.
- `_reporting_date(deal)` is not the same as deal creation date: open deals use `created_at`, while closed deals use `closed_at` when available.
- The user asked specifically for filtering by deal creation date, so this must not reuse the current report-date semantics.
- `normalized_deals.created_at` already exists and is loaded from Bitrix deal `DATE_CREATE` / item created time.
- `GET /api/meta/filters` already returns `min_created_at` and `max_created_at`, which can be used as UI hints for available deal creation date range.
- Bitrix remains read-only. This task must not change extraction, normalization, manual refresh, contact selection, currency conversion, or Bitrix calls.

## Assumptions

- Persisted UI state should use browser-local storage with a versioned key, because the app currently has one Contacts screen and no router/query-string state layer.
- Persisted state includes: search text, exact contact ID, contact type, region, status, deal creation date range, sort field, sort order, limit, and offset.
- Search draft and persisted `filters.search` should stay in sync after reload; same for contact ID draft.
- When persisted state is invalid, incompatible, or contains unknown values, the app should safely fall back to defaults instead of breaking the screen.
- `Сбросить` must clear persisted state and immediately refetch/render the default table state.
- Filtering by deal creation date means selecting contacts whose assigned analytical deals have `created_at::date` within the inclusive range.
- If a deal creation date range is active, contacts with zero matching assigned deals should not be shown, unless implementation finds an existing product pattern that clearly requires zero rows to remain visible; if so, document the exact behavior in `.ai/report.md`.
- Existing `date_from` / `date_to` query parameters should keep their current report-date behavior for existing/future report callers. Add separate parameters for deal creation date filtering.

## Unknowns

- Whether the observed self-refresh is caused by TanStack Query refetch-on-focus/reconnect, browser reload, Vite dev refresh, or another trigger. Implement the robust fix: disable disruptive background refetch for the Contacts workspace and persist state so reloads do not lose operator context.
- There is no current frontend test framework beyond TypeScript/Vite build. Use type safety and, where practical, simple focused helper tests only if a frontend test setup already exists.

## Scope

### 1. Stop disruptive background refetch

Adjust TanStack Query behavior for the current app so the Contacts workspace does not periodically refetch on its own or refetch on window focus/reconnect after becoming stale.

Expected behavior:

- no timer-based Contacts refetch;
- no automatic refetch on window focus/reconnect that changes the visible table while the user is verifying data;
- manual refresh through `Обновить из Bitrix` still invalidates/refetches dataset status, filters, and contacts after success;
- explicit retry buttons and pagination/filter/sort changes still fetch normally.

Prefer the smallest project-consistent change, for example default query options in `frontend/src/main.tsx` plus per-query options only where needed.

### 2. Persist Contacts table state

Persist and restore the Contacts screen state in browser storage.

State to persist:

```text
search
contactId
contactType
region
status
dealCreatedFrom
dealCreatedTo
sort
order
limit
offset
```

Requirements:

- use a versioned storage key, for example `bitrix-sales.contacts.v1`;
- validate/coerce persisted values before using them;
- keep search/contact ID input drafts synchronized with restored filters;
- update persisted state whenever filters/sort/pagination/date range changes;
- reset clears both in-memory state and persisted state;
- reset must update the table immediately, not leave old query state visible;
- do not persist backend data, rows, secrets, raw payloads, or personal fields.

### 3. Backend filter by deal creation date

Add explicit deal creation date filter support to Contacts analytics.

Preferred API query parameters:

```text
deal_created_from=YYYY-MM-DD
deal_created_to=YYYY-MM-DD
```

Backend behavior:

- parse as `date | None` in FastAPI;
- pass to `list_contact_analytics()`;
- filter `_DealFact` rows by `deal.created_at.date()` inclusively;
- combine with existing filters predictably:
  - contact type/region/search/contact ID filter contacts;
  - status filter applies to the already creation-date-filtered deal set;
  - metrics/counts/budgets/revenue/profit reflect the creation-date-filtered deal set;
- do not change existing `date_from` / `date_to` report-date behavior;
- do not change ABC, RFM, concentration, type-region, stale deals, deal cycle, currency conversion, normalization, or Bitrix sync.

### 4. Frontend deal creation date filter

Add a compact date range control to the existing Contacts toolbar.

Suggested labels:

```text
Создана с
Создана по
```

Requirements:

- use native date inputs (`type="date"`) unless the existing codebase already has a better local control;
- values are ISO dates `YYYY-MM-DD` sent as `deal_created_from` and `deal_created_to`;
- each date change resets `offset` to `0`;
- range is inclusive;
- if both dates are set and `from > to`, show a clear local validation state or prevent the invalid request in a simple way;
- use `filterQuery.data.min_created_at` / `max_created_at` as placeholders/min/max only if it stays simple and reliable;
- date filters persist across browser reload and clear on reset;
- keep the toolbar usable on desktop and avoid layout overlap on narrower widths.

### 5. Frontend API types

Update `frontend/src/api.ts`:

- extend `ContactFilters` with `dealCreatedFrom` and `dealCreatedTo`;
- send them as `deal_created_from` and `deal_created_to` only when non-empty;
- keep frontend calls limited to local backend endpoints.

### 6. Documentation

Update relevant docs so the operator/developer behavior is clear. At minimum consider:

- `frontend/README.md`;
- `docs/development.md`.

Mention that Contacts screen state is persisted locally and that deal creation date filtering is local backend filtering over `normalized_deals.created_at`.

### 7. Tests

Add focused backend tests for:

- `deal_created_from` / `deal_created_to` filters use deal `created_at`, not closed/reporting date;
- filtered Contacts analytics counts/budgets/revenue reflect only deals created in the selected range;
- status filter composes correctly with deal creation date filtering;
- API endpoint accepts the new query parameters;
- existing `date_from` / `date_to` behavior is not broken if there is existing coverage or easy focused coverage can be added.

Frontend verification:

- TypeScript build must pass;
- add lightweight pure helper coverage only if a frontend test setup already exists;
- otherwise document manual/browser verification limitations in `.ai/report.md`.

### 8. Report

Update `.ai/report.md` with:

- exact state persistence key and fields;
- exact background refetch behavior changed;
- exact backend query parameters added;
- exact date semantics implemented;
- checks run;
- confirmation that no Bitrix calls or write methods were added;
- any manual/browser verification limitations.

## Out Of Scope

- Contact creation date.
- New screens.
- New router/navigation system.
- CSV/export.
- Authentication.
- Changing Bitrix extraction, manual refresh, normal sync, diagnostic endpoints, normalization, contact priority rules, currency loading, ABC/RFM/concentration formulas, or data model storage columns.
- Calling Bitrix from frontend.
- Any Bitrix write operation.
- Showing phones, emails, addresses, messengers, comments, files, requisites, activities, arbitrary custom fields, webhook values, raw payloads, or raw private rows.
- Changing `ui-kits/`.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- Frontend must call only local backend endpoints.
- Report APIs must filter local DuckDB-backed data only; report API calls must not call Bitrix or NBRB.
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

- Contacts screen no longer auto-refetches on a timer/window focus/reconnect in a way that disrupts the current verification state.
- Manual `Обновить из Bitrix`, explicit retries, filter changes, sort changes, and pagination still fetch data correctly.
- Contacts screen restores filters, sort/order, pagination, search draft, contact ID draft, and deal creation date range after browser reload.
- `Сбросить` clears persisted UI state and immediately shows the default unfiltered table state.
- Contacts toolbar includes deal creation date range controls.
- Contacts analytics API accepts `deal_created_from` and `deal_created_to`.
- Deal creation date filtering uses `normalized_deals.created_at` / `_DealFact.created_at.date()`, not closed date and not `_reporting_date()`.
- Metrics/counts/budgets/revenue/profit in the Contacts table reflect the selected deal creation date range.
- Status filter and deal creation date filter work together.
- Existing Contacts sort, exact ID search, search by name, type/region/status filters, reset, pagination, refresh UX, budget columns, dates, and Bitrix `Посмотреть` links remain working.
- No frontend Bitrix calls are added.
- No Bitrix write methods are added or called.
- Backend tests pass.
- Frontend build passes.
- `.ai/report.md` is updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-15 Persist Contacts UI state and add deal creation date filter
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
- disruptive background Contacts refetch behavior is disabled without breaking explicit user-triggered fetches;
- Contacts UI state persists safely and reset clears it;
- deal creation date backend filter is implemented with focused tests;
- frontend sends and persists the new date filters;
- required backend tests and frontend build are run, or any inability is explicitly documented with reason;
- `.ai/report.md` states that no Bitrix calls or write methods were added;
- frontend still calls only local backend endpoints, not Bitrix;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
