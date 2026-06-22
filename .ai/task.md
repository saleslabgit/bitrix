# Task: TASK-2026-06-22-18

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-17`

## Title

Add Deals report

## Goal

Add a second frontend report for deals, similar in behavior and density to the current Contacts report, backed by a local backend deals analytics endpoint.

The report must let the user verify deal-level data from the local database with filters and columns requested by the product owner.

## User Request

Add a deals report with filters:

- deal ID;
- deal status;
- type, for example `Дизайнер`;
- region;
- dates like in Contacts.

Add columns:

- ID + link;
- deal name;
- deal status;
- type;
- region;
- budget;
- profit;
- created date;
- closed date.

## Facts

- Current frontend has only the Contacts screen in `frontend/src/App.tsx`.
- Current Contacts screen reads only local backend endpoints:
  - `GET /api/reports/contacts/analytics`;
  - `GET /api/meta/filters`;
  - `GET /api/datasets/status`;
  - `POST /api/local/refresh-data`.
- Current Contacts filters include exact contact ID, type, region, status, and deal creation date drafts applied by `Применить даты`.
- Current metadata endpoint exposes `contact_types`, `regions`, `statuses`, `min_created_at`, `max_created_at`, `min_closed_at`, and `max_closed_at`.
- Current backend analytics code already loads normalized deal facts with:
  - `deal_id`;
  - `deal_name`;
  - `amount_usd`;
  - `status_group`;
  - `created_at`;
  - `closed_at`;
  - `contact_type_normalized`;
  - `region_normalized`;
  - analytical contact assignment.
- Current contact analytics budget semantics:
  - budgets use all assigned local deals in USD;
  - revenue and estimated profit are won-only;
  - estimated profit is always `revenue_usd * 0.50`.
- For a single deal row, `Бюджет` should display that deal's `amount_usd`.
- For a single deal row, `Прибыль` must be won-only: `amount_usd * 0.50` when `status_group == "won"`, otherwise `0.00`.
- Bitrix is read-only and must not be called from frontend reports.
- Report APIs must read local DuckDB-backed data only.

## Assumptions

- `Даты, как в Контактах` means a deal creation date range filter using `normalized_deals.created_at`, with draft inputs and an explicit `Применить даты` action before table refetch.
- The deal link target should be the Bitrix deal details page:

```text
https://dialar.bitrix24.by/crm/deal/details/{{deal_id}}/
```

- Deal status can be stored/transferred as `won`, `open`, `lost`, and displayed in Russian labels in the frontend.
- A lightweight in-app screen switch or sidebar selection is acceptable; do not add a full router unless the existing frontend structure already makes that clearly simpler.
- Deal report UI state may be persisted separately from Contacts state, using a safe browser storage key such as `bitrix-sales.deals.v1`.

## Unknowns

- Browser-level visual verification depends on the execution environment. If Codex cannot run Docker/browser checks, document the limitation in `.ai/report.md`.
- The product owner did not request search by deal name. Do not add it unless it falls out naturally from existing table helpers with no extra scope; exact deal ID is required.

## Scope

### 1. Backend deal analytics endpoint

Add a local backend endpoint for deal-level analytics, recommended:

```text
GET /api/reports/deals/analytics
```

Required query parameters:

- `limit`, `offset` with the same safe bounds as Contacts;
- `deal_id` exact positive integer filter;
- `status` filter over `won`, `open`, `lost`;
- `contact_type` filter over normalized analytical contact type;
- `region` filter over normalized analytical region;
- `deal_created_from` / `deal_created_to` inclusive filters over `normalized_deals.created_at`;
- `sort` and `order` with an allowlist.

Required response shape:

- page metadata: `total`, `limit`, `offset`;
- rows with:
  - `deal_id`;
  - `deal_name`;
  - `status_group`;
  - `contact_type_normalized`;
  - `region_normalized`;
  - `budget_usd`;
  - `estimated_profit_usd`;
  - `created_date`;
  - `closed_date`.

Sort allowlist should cover all displayed columns:

- `deal_id`;
- `deal_name`;
- `status_group`;
- `contact_type_normalized`;
- `region_normalized`;
- `budget_usd`;
- `estimated_profit_usd`;
- `created_date`;
- `closed_date`.

Sorting must be stable and deterministic. Use `deal_id` as the final tie-breaker. Null closed dates must not crash sorting.

Implementation guidance:

- Prefer extending `backend/app/reports/analytics.py` with deal row/page dataclasses and `list_deal_analytics()` because `_load_deal_facts()` already centralizes local currency conversion and normalized deal facts.
- Add Pydantic response models in `backend/app/api/models.py`.
- Add endpoint and sort literal in `backend/app/main.py`.
- Do not add new storage tables or migrations for this task.
- Do not call Bitrix, NBRB, or external services from the report endpoint.

### 2. Backend tests

Add focused backend tests covering:

- endpoint returns local deal rows from the synthetic dataset;
- exact `deal_id` filter returns one matching deal;
- `status`, `contact_type`, and `region` filters work;
- deal creation date range filters rows by `created_at` inclusively;
- sorting by budget/profit/date works and is deterministic;
- won deal profit equals `budget_usd * 0.50`;
- open/lost deal profit is `0.00`;
- response does not expose forbidden personal fields;
- no Bitrix write methods were added.

### 3. Frontend API types and fetcher

Update `frontend/src/api.ts` with:

- `DealAnalytics` row type;
- `DealAnalyticsPage` type;
- `DealSort` type;
- `DealFilters` type;
- `fetchDealAnalytics()` calling only `/api/reports/deals/analytics`.

Frontend must still call only local backend endpoints. No direct Bitrix calls.

### 4. Frontend Deals report screen

Add a Deals report view to the existing frontend.

Required UI behavior:

- The sidebar must allow switching between `Contacts` and `Deals`.
- Keep Contacts behavior intact.
- Deals must reuse the existing dataset status/manual refresh flow where practical.
- Deals must use the existing metadata for type/region/status/date filter options.
- Deals filters:
  - exact deal ID numeric input;
  - deal status select;
  - type select;
  - region select;
  - created date range inputs with draft state and explicit `Применить даты` behavior, matching Contacts.
- Deals table columns:
  - `ID` with `Посмотреть` link to `https://dialar.bitrix24.by/crm/deal/details/{{deal_id}}/`;
  - `Название сделки`;
  - `Статус сделки` with Russian labels;
  - `Тип`;
  - `Регион`;
  - `Бюджет` formatted as USD;
  - `Прибыль` formatted as USD;
  - `Дата создания`;
  - `Дата закрытия`.
- Add sorting for displayed columns. Like Contacts, first click on a new sort column should sort descending.
- Add pagination, loading, error, empty, reset, and selected-filter-count states comparable to Contacts.
- Persist Deals table state safely in browser storage, separate from Contacts, for example `bitrix-sales.deals.v1`.
- Reset Deals filters must reset only Deals state and must not delete cached metadata options.
- Preserve TASK-17 metadata-cache protection so type/status/region dropdowns do not get wiped by failed or invalid metadata refreshes.

Implementation guidance:

- Keep the screen dense and operational.
- Reuse existing helpers/components where it keeps the file understandable; avoid a broad frontend rewrite.
- Do not modify `ui-kits/`.
- Do not add other screens beyond Contacts and Deals.

### 5. Documentation and report

Update relevant docs when behavior changes, at minimum consider:

- `frontend/README.md` for the new Deals screen and endpoint;
- `docs/development.md` for the new frontend/backend endpoint and operator verification;
- `docs/data-model.md` for the deal analytics output;
- `docs/project-status.md` if the current project status needs to mention the new report.

Update `.ai/report.md` with:

- backend endpoint added;
- frontend Deals screen behavior;
- profit semantics for deal rows;
- checks run;
- confirmation that no Bitrix calls/write methods were added;
- any browser/Docker verification that could not be run.

## Out Of Scope

- Changing Bitrix ingestion, extraction, link completeness, reconciliation, or normal refresh behavior.
- New Bitrix API calls.
- Any Bitrix write operation.
- New storage tables or persisted analytics tables.
- Company, lead, product, activity, phone, email, address, messenger, comment, file, requisite, or arbitrary custom-field display.
- CSV/export.
- Authentication.
- Adding a full router/query-string state layer unless it is clearly needed and remains small.
- Changing Contacts metrics, contact priority rules, type normalization, currency loading, ABC/RFM/concentration formulas, or manual refresh semantics.
- Changing `ui-kits/`.

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
- Deal row `Прибыль` must follow project semantics: won-only estimated profit.

## Acceptance Criteria

- A Deals report is available from the frontend sidebar without breaking Contacts.
- Deals screen loads from local backend data when an active dataset exists.
- Deals screen has filters for deal ID, status, type, region, and deal creation date range.
- Deal creation date range does not refetch on partial date typing; it applies only through `Применить даты` when values are complete/valid.
- Deals table displays the requested columns with correct Russian labels and USD formatting.
- Deal ID includes a `Посмотреть` link to the Bitrix deal details URL.
- `Бюджет` equals the deal amount in USD.
- `Прибыль` equals `budget_usd * 0.50` only for won deals and `0.00` for open/lost deals.
- Sorting works for displayed columns, with first click on a new column sorting descending.
- Pagination, loading, error, empty, and reset states work.
- Deals state is persisted separately from Contacts state.
- Metadata dropdown cache protection from TASK-17 remains intact.
- Backend tests cover the new endpoint and profit/filter/sort semantics.
- Frontend build passes.
- No frontend Bitrix calls are added.
- No Bitrix write methods are added or called.
- `.ai/report.md` is updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-18 Add Deals report
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
- backend exposes a local deal analytics endpoint with the required filters, sorting, pagination, and fields;
- deal profit semantics are won-only and tested;
- frontend has a Deals report reachable from sidebar;
- Contacts behavior is preserved;
- Deals filters and date apply behavior match the requested behavior;
- Deals table uses USD budget/profit fields and safe Bitrix deal links;
- no Bitrix calls are added to frontend;
- no Bitrix write methods are added anywhere;
- required backend tests and frontend build are run, or any inability is explicitly documented with reason;
- `.ai/report.md` describes implementation, checks, facts, unknowns, and risks;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
