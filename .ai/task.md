# Task: TASK-2026-06-22-21

Status: planned
Created from: current `main` after `TASK-2026-06-22-20` was cancelled by the user before Codex implementation

## Title

Link contact deal counts and hide regions

## Goal

Improve the Contacts-to-Deals verification workflow and temporarily hide region UI until region logic is ready.

The user wants to click deal counters in the Contacts table and jump directly to the Deals report with matching client and status filters applied.

The user also wants all region filters and region columns hidden from the frontend for now because region detection is not finished.

## User Request

From the Contacts table:

- clicking `Всего сделок` should open Deals filtered by that contact/client;
- clicking `Успешные` should open Deals filtered by that contact/client and `won` status;
- clicking `Открытые` should open Deals filtered by that contact/client and `open` status;
- clicking `Проигранные` should open Deals filtered by that contact/client and `lost` status.

Additionally:

- hide region filters and region columns everywhere in the frontend for now.

The previously planned `TASK-2026-06-22-20 Stabilize filter metadata endpoint` is cancelled by the user as not currently needed. Do not implement it in this task.

## Facts

- Current frontend has Contacts and Deals reports in `frontend/src/App.tsx`.
- Current Contacts rows contain:
  - `contact_id`;
  - `contact_name`;
  - `total_deals_count`;
  - `won_deals_count`;
  - `open_deals_count`;
  - `lost_deals_count`.
- Current Deals report already has a client text search filter `clientSearch` backed by `client_search` over local analytical contact/client name.
- Current normalized deals contain `analytical_contact_id` and `analytical_contact_name` according to `docs/data-model.md`.
- Current Deals backend endpoint supports deal ID, client search, status, type, region, date, sorting, pagination, and filtered totals.
- Current frontend Contacts and Deals filters still include region UI and region state.
- Backend reports must read local DuckDB-backed data only.
- Frontend must call only local backend endpoints.
- Bitrix is read-only and must not be called from report page loads.

## Assumptions

- For the Contacts-to-Deals jump, exact `contact_id` filtering is safer than name-only filtering because two clients can share the same display name.
- The Deals UI may still show the selected client name in the `Клиент` filter input, but the actual jump filter should be exact by local analytical contact ID when available.
- When the user manually edits the Deals `Клиент` search input, it should behave as normal fuzzy text search and clear any hidden exact contact ID filter.
- Clicking a non-zero counter should reset unrelated Deals filters so the result is easy to understand: only client, status, default dates, default pagination, and default sort should remain unless there is a strong existing pattern to preserve more.
- Clicking a zero counter should either do nothing or render as a disabled/non-link value; it should not navigate to a confusing empty filtered view.
- `Hide region filters and columns everywhere in frontend` means hide/remove region controls and columns from Contacts and Deals UI, and stop sending frontend `region` query params from these reports. Backend region fields and backend API support may remain for later use.

## Unknowns

- Browser click-through verification depends on the execution environment. If unavailable, document the limitation in `.ai/report.md`.

## Scope

### 1. Backend exact client filter for Deals

Add exact client/contact filtering to the Deals analytics backend.

Recommended query parameter:

```text
client_id
```

Requirements:

- `GET /api/reports/deals/analytics` should accept `client_id` as a positive integer query parameter.
- It should filter local deals by `normalized_deals.analytical_contact_id` through the existing deal facts path.
- It must remain local-only: no Bitrix, NBRB, or external calls from the report endpoint.
- It must not expose forbidden personal fields.
- It must compose correctly with status, type, created-date, sorting, pagination, and filtered totals.
- If both `client_id` and `client_search` are supplied, prefer exact `client_id` for filtering. `client_search` can remain a frontend display/search value, but it must not accidentally exclude exact-client rows when `client_id` is present.

Add backend tests covering:

- exact `client_id` returns only that analytical client's deals;
- exact `client_id` plus `status` returns only matching status deals;
- filtered budget/profit totals respect exact `client_id` and status before pagination;
- `client_id` does not use Bitrix or external calls.

### 2. Contacts table counter links

Make the Contacts deal-count cells clickable where useful.

Required behavior:

- `Всего сделок` click opens/switches to the Deals report with exact client filter and no status filter.
- `Успешные` click opens/switches to Deals with exact client filter and `status = won`.
- `Открытые` click opens/switches to Deals with exact client filter and `status = open`.
- `Проигранные` click opens/switches to Deals with exact client filter and `status = lost`.
- The Deals client input should visibly show the clicked contact/client name.
- The actual Deals fetch should use exact `client_id` when the navigation came from a Contacts row.
- The Deals page should reset to first page (`offset = 0`) after navigation.
- Unrelated old Deals filters should be cleared on navigation unless keeping one is clearly necessary and documented.
- Counters with `0` should not behave like active links.
- Links/buttons must be keyboard-accessible and not break table sorting.
- Existing contact ID Bitrix link behavior must remain unchanged.

Implementation guidance:

- Add a small helper such as `openDealsForContact(contact, status?)` in `App.tsx` rather than introducing a full router.
- Reuse existing report state and storage patterns.
- Keep the UI dense. A number-styled button/link is enough; avoid large new controls.

### 3. Hide region UI in frontend

Temporarily hide region filters and columns from the frontend.

Requirements:

- Remove/hide Region filter from Contacts toolbar.
- Remove/hide Region filter from Deals toolbar.
- Remove/hide Region column from Contacts table.
- Remove/hide Region column from Deals table.
- Remove region from frontend selected-filter counts.
- Stop sending `region` query params from frontend report fetches.
- Make persisted frontend state safe: old `region` values in localStorage must not continue to affect current frontend queries.
- Make persisted sort state safe: old `region_normalized` sort values in localStorage should fall back to a valid visible default sort.
- Do not remove backend region fields, backend region query support, storage columns, or docs about data model unless a small doc note is useful. This is a frontend hiding task, not a data-model rewrite.

### 4. Frontend docs/report

Update relevant docs if behavior changes, at minimum consider:

- `frontend/README.md` for Contacts counter navigation and temporarily hidden region UI;
- `docs/development.md` if operator verification steps change;
- `docs/project-status.md` if useful.

Update `.ai/report.md` with:

- note that `TASK-2026-06-22-20` was cancelled and not implemented;
- backend/client filter changes;
- frontend Contacts-to-Deals navigation behavior;
- hidden region UI details;
- checks run;
- confirmation that no Bitrix calls/write methods were added.

## Out Of Scope

- Implementing/correcting region normalization logic.
- Removing region data from backend, storage, reports, or database schema.
- New report screens.
- URL routing/query-string routing.
- Changing Bitrix ingestion, extraction, contact-deal link logic, reconciliation, or manual refresh behavior.
- Any live Bitrix diagnostic call.
- Any Bitrix write operation.
- Displaying forbidden personal fields or raw Bitrix rows.
- Changing contact priority rules, type normalization semantics, currency loading, report metric formulas, or manual refresh semantics.
- Implementing the cancelled `TASK-2026-06-22-20` metadata stabilization.
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
- Do not change backend financial semantics: deal profit remains won-only; contact profit remains revenue-based.

## Acceptance Criteria

- Latest relevant task is this planner commit, not cancelled `TASK-2026-06-22-20`.
- Deals backend supports exact local `client_id` filtering by analytical contact ID.
- Deals exact client filter composes with status and totals before pagination.
- In Contacts table, non-zero deal count cells are clickable/keyboard-accessible.
- Clicking `Всего сделок` opens Deals filtered by the clicked contact/client, with no status filter.
- Clicking `Успешные` opens Deals filtered by clicked contact/client and `won`.
- Clicking `Открытые` opens Deals filtered by clicked contact/client and `open`.
- Clicking `Проигранные` opens Deals filtered by clicked contact/client and `lost`.
- Deals client input shows the clicked contact name, while backend filtering uses exact `client_id`.
- Manual editing of Deals client search clears hidden exact `client_id` and uses fuzzy `client_search` behavior.
- Old unrelated Deals filters do not accidentally remain after clicking a Contacts counter.
- Zero counters are not misleading clickable actions.
- Region filters and columns are hidden from Contacts and Deals frontend.
- Frontend no longer sends region query params for Contacts or Deals.
- Old persisted region filters/sorts do not affect current frontend reports.
- Contacts/Deals existing sorting, pagination, reset, loading, empty, and error states remain usable.
- Frontend still calls only local backend endpoints.
- Backend report endpoints do not call Bitrix, NBRB, or external services.
- No Bitrix write methods are added.
- Relevant backend tests and frontend build pass, or any inability is explicitly documented with reason.
- Documentation and `.ai/report.md` are updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-21 Link contact deal counts and hide regions
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

- cancelled `TASK-2026-06-22-20` was not implemented;
- exact Deals `client_id` filtering is implemented and tested;
- Contacts counter click-to-Deals behavior works for all four count columns;
- region UI is hidden from frontend filters and tables;
- old persisted region state no longer affects frontend queries;
- no frontend Bitrix calls are added;
- no Bitrix write methods are added anywhere;
- required backend tests and frontend build are run, or inability is explicitly documented;
- `.ai/report.md` describes implementation, checks, facts, unknowns, and risks;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
