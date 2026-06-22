# Task: TASK-2026-06-22-19

Status: planned
Created from: current `main` after `TASK-2026-06-22-18`

## Title

Fix report errors and add Deals client search totals

## Goal

Fix the user-reported report/runtime issues and extend the Deals report so it is more useful for data verification:

- diagnose and fix the `500` from Contacts analytics with the reported query;
- remove the missing favicon request noise;
- add client search to Deals filters;
- show filtered Deals budget/profit totals above and below the table, calculated across all filtered rows, not only the current pagination page.

## User Request

The user reported console output:

```text
Download the React DevTools for a better development experience
favicon.ico:1 GET http://localhost:5173/favicon.ico 404 (Not Found)
api.ts:233 GET http://localhost:5173/api/reports/contacts/analytics?limit=25&offset=0&sort=contact_id&order=desc 500 (Internal Server Error)
```

Additional requested changes:

- add client search to the Deals report filter;
- add budget and profit sums at the top and bottom of the table for all filtered deals, not only deals visible on the current pagination page.

## Facts

- Current frontend has Contacts and Deals reports.
- Contacts reads `GET /api/reports/contacts/analytics`.
- Deals reads `GET /api/reports/deals/analytics`.
- Deals rows currently include deal ID/name, status, normalized analytical type/region, USD budget, won-only USD estimated profit, created date, and closed date.
- Deals filters currently include exact deal ID, status, type, region, and deal creation date range.
- Normalized deals contain `analytical_contact_id` and `analytical_contact_name` according to current documentation.
- Contact and deal report APIs must read local DuckDB-backed data only.
- Frontend must call only local backend endpoints.
- Bitrix is read-only and must not be called from report page loads.
- The React DevTools console message is a normal Vite/React development-mode informational message. It is not an application bug unless production build behavior is changed unexpectedly.
- `favicon.ico` 404 is browser/dev-server noise and can be fixed by adding a small frontend favicon asset/config.

## Assumptions

- `поиск по клиентам` in the Deals report means searching by the selected analytical contact/client name stored locally as `normalized_deals.analytical_contact_name`.
- The client search should be case-insensitive, trimmed, local-only, and should not expose or search forbidden personal fields such as phone, email, address, messengers, comments, files, requisites, or arbitrary raw fields.
- The Deals totals should respect all current Deals filters, including the new client search, but must be computed before `limit`/`offset` pagination.
- The requested budget/profit sums are for the Deals report only.
- Existing Contacts totals/metrics semantics are unchanged by this task.

## Unknowns

- The exact root cause of the Contacts `500` is unknown. Codex must reproduce or inspect it and document the root cause in `.ai/report.md` before claiming it is fixed.
- Browser-level verification depends on the execution environment. If it cannot be run, document the limitation in `.ai/report.md`.

## Scope

### 1. Diagnose and fix Contacts analytics `500`

Investigate the failing request:

```text
GET /api/reports/contacts/analytics?limit=25&offset=0&sort=contact_id&order=desc
```

Requirements:

- reproduce the failure with the current code or add a failing regression test first;
- identify the real backend exception/root cause;
- fix the backend path so this valid query does not return `500`;
- keep sorting allowlisted and deterministic;
- do not expose stack traces, local paths, secrets, raw rows, webhook values, or forbidden personal data in API responses;
- add regression coverage for the failure path;
- document the root cause and fix in `.ai/report.md`.

If the failure only appears with a local live dataset shape that is hard to reproduce exactly, create the smallest synthetic/test fixture that represents the same missing/null/edge condition.

### 2. Favicon and console noise

- Add a small frontend favicon asset/config so `GET /favicon.ico` no longer returns `404` in local Vite usage.
- Do not try to suppress the React DevTools development-mode informational message unless there is a real build/config bug. Mention in `.ai/report.md` that this line is expected in dev mode.

### 3. Deals client search filter

Add a Deals filter for client search.

Backend requirements:

- add a query parameter such as `client_search` to `GET /api/reports/deals/analytics`;
- filter by local analytical contact/client name, recommended source: `normalized_deals.analytical_contact_name` through the existing deal facts loader;
- matching should be case-insensitive substring search after trimming whitespace;
- empty/blank search should behave as no filter;
- no Bitrix or external calls from this endpoint;
- no forbidden personal fields in response.

Frontend requirements:

- add an input to the Deals filter area labeled clearly, for example `Клиент` or `Поиск по клиенту`;
- wire it to the new backend parameter;
- persist it in the existing Deals state storage key;
- reset Deals filters must clear it;
- keep Contacts behavior unchanged;
- keep metadata dropdown cache behavior from earlier tasks intact.

### 4. Deals filtered totals above and below table

Extend Deals analytics response with totals for all rows matching filters before pagination.

Recommended response fields:

```text
filtered_budget_usd
filtered_estimated_profit_usd
```

Requirements:

- totals must include every deal matching current filters before `limit`/`offset`;
- totals must respect deal ID, status, type, region, created-date range, and new client search filters;
- totals must not be limited to the current page;
- when no rows match, both totals should be `0.00`;
- budget total sums `budget_usd`;
- profit total sums existing deal-row profit semantics: won-only `estimated_profit_usd`;
- frontend must display the totals above and below the Deals table;
- labels should be clear, for example `Бюджет по фильтру` and `Прибыль по фильтру`;
- formatting must match existing USD formatting;
- loading, error, and empty states must not show misleading totals.

Implementation guidance:

- Prefer calculating totals in the same backend list function that already filters Deals rows, before pagination.
- Avoid adding persisted analytics tables or migrations for this task.
- Avoid broad frontend refactors; keep changes focused in existing report code.

### 5. Documentation and report

Update relevant documentation when behavior changes, at minimum consider:

- `frontend/README.md` for Deals client search and filtered totals;
- `docs/development.md` for the Deals endpoint parameters/response and favicon note if useful;
- `docs/data-model.md` for deal analytics totals and client-search source;
- `docs/project-status.md` if current status should mention the refinement.

Update `.ai/report.md` with:

- root cause of the Contacts `500`;
- files changed;
- backend/frontend behavior added;
- checks run;
- explicit note that React DevTools console line is expected in dev mode;
- confirmation that report endpoints remain local-only and no Bitrix write methods were added.

## Out Of Scope

- New report screens beyond Contacts and Deals.
- Changing Bitrix ingestion, extraction, contact-deal link logic, reconciliation, or manual refresh behavior.
- Any new Bitrix calls from report endpoints or frontend.
- Any Bitrix write operation.
- Displaying phone, email, address, messengers, comments, files, requisites, arbitrary raw Bitrix fields, webhook values, secrets, raw rows, or local paths.
- Changing contact priority rules, type normalization, currency loading, ABC/RFM/concentration formulas, or manual refresh semantics.
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
- Keep financial values in USD.
- Deal row and total `Прибыль` must stay won-only according to current deal report semantics.

## Acceptance Criteria

- The reported Contacts request no longer returns `500` and has regression coverage:

```text
GET /api/reports/contacts/analytics?limit=25&offset=0&sort=contact_id&order=desc
```

- `.ai/report.md` explains the actual root cause of the Contacts `500`.
- `favicon.ico` no longer returns `404` in local frontend usage.
- `.ai/report.md` notes that the React DevTools line is expected in development mode.
- Deals report has a client search filter backed by local analytical contact/client name.
- Deals client search is persisted and reset correctly with Deals state.
- Deals response includes filtered budget/profit totals computed across all filtered rows before pagination.
- Deals totals respect all filters, including client search, and are not limited to the current page.
- Deals UI displays the totals both above and below the table with clear Russian labels and USD formatting.
- Loading/error/empty states remain clear and do not show misleading totals.
- Contacts behavior remains intact.
- Frontend still calls only local backend endpoints.
- Backend report endpoints do not call Bitrix, NBRB, or external services.
- No Bitrix write methods are added.
- Relevant backend tests and frontend build pass, or any inability is explicitly documented with reason.
- Documentation and `.ai/report.md` are updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-19 Fix report errors and add Deals client search totals
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
- Contacts analytics `500` root cause is understood, fixed, and covered by a regression test;
- Deals client search works locally without Bitrix calls;
- Deals filtered totals are calculated before pagination and shown above and below the table;
- Contacts behavior and existing Deals filters/sorting/pagination remain intact;
- no frontend Bitrix calls are added;
- no Bitrix write methods are added anywhere;
- required backend tests and frontend build are run, or any inability is explicitly documented with reason;
- `.ai/report.md` describes implementation, checks, facts, unknowns, and risks;
- staged files are only task files plus `.ai/report.md` and relevant docs/assets;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
