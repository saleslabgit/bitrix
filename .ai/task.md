# Task: TASK-2026-06-22-13

Status: planned
Created from: current `main` after `.ai/report.md` for `TASK-2026-06-22-12` reports `done`

## Title

Improve Contacts verification UI

## Goal

Improve the existing Contacts screen so the product owner can verify refreshed local Bitrix data faster from the UI.

Add sortable Contacts analytics rows, contact ID search, a reliable filter reset, a closed-date column, a USD budget column, and a Bitrix contact-card link next to the contact ID.

Keep this as a focused improvement to the current Contacts screen and its local backend analytics API. Do not add a new Deals screen in this task.

## Facts

- The user confirmed the manual refresh completed and the data mostly matches.
- The user requested UI features to verify data:
  - sorting;
  - search by ID in filters;
  - fix `Сбросить фильтр` not updating the table;
  - add `дата закрытия` column;
  - add `бюджет` column showing the deal amount in USD;
  - show a `Посмотреть` link next to the ID using:

```text
https://dialar.bitrix24.by/crm/contact/details/{{id}}/
```

- Current frontend is a single `Contacts` screen in `frontend/src/App.tsx`.
- Current frontend uses local backend endpoints only:
  - `GET /api/reports/contacts/analytics`;
  - `GET /api/meta/filters`;
  - `GET /api/datasets/status`;
  - `POST /api/local/refresh-data`.
- `frontend/src/api.ts` `ContactFilters` currently has `search`, `contactType`, `region`, `status`, `limit`, and `offset`; it has no contact ID filter and no sort/order params.
- Backend endpoint `GET /api/reports/contacts/analytics` currently accepts `limit`, `offset`, `date_from`, `date_to`, `search`, `contact_type`, `region`, and `status`; it has no contact ID filter and no sort/order params.
- `ContactAnalyticsRow` / `ContactAnalyticsResponse` already include:
  - `contact_id`;
  - `contact_name`;
  - `total_deals_count`, `won_deals_count`, `open_deals_count`, `lost_deals_count`;
  - `revenue_usd`;
  - `estimated_profit_usd`;
  - `first_won_date`;
  - `last_won_date`;
  - `latest_deal_date`.
- Current Contacts table displays `revenue_usd`, `estimated_profit_usd`, and `latest_deal_date`, but does not show `last_won_date` as a closed-date column.
- This screen is contact-analytics aggregate data, not a per-deal table.
- The provided Bitrix URL is a contact details URL, so the `Посмотреть` link must use `contact_id` unless current implementation discovers a stronger repository-backed reason to do otherwise.
- Bitrix remains read-only. Report API and frontend table interactions must use local backend data only and must not call Bitrix.

## Assumptions

- In the current Contacts aggregate table, `дата закрытия` means the latest closed won deal date for the contact, represented by existing `last_won_date`. Show `—` when there is no closed won deal.
- In the current Contacts aggregate table, `бюджет` should use the existing USD financial value for the contact, `revenue_usd`, because the screen aggregates a contact's won deals. Label it clearly as USD, for example `Бюджет USD`, so it is not confused with original-currency totals.
- Sorting should be consistent across pagination, so it should be applied before slicing/pagination in the backend, not only to the current frontend page.
- Exact contact ID filtering is enough for verification. If the user enters `661`, the table should return contact `661` when it exists and matches the other active filters.

## Unknowns

- Whether the current reset bug is caused only by debounced search state, by object identity/query key behavior, or by a combination of search, offset, and query invalidation.
- Whether all desired columns will fit comfortably at current desktop density without minor CSS table-width adjustments.

## Scope

### 1. Backend contact analytics filtering and sorting

Extend the local `GET /api/reports/contacts/analytics` path to support:

- optional `contact_id` query param for exact contact ID filtering;
- optional `sort` query param;
- optional `order` query param with `asc` / `desc`.

Apply filtering and sorting in the report function before pagination.

Use an explicit allowlist of sortable fields. Suggested sortable fields:

```text
contact_id
contact_name
contact_type_normalized
region_normalized
total_deals_count
won_deals_count
open_deals_count
lost_deals_count
revenue_usd
estimated_profit_usd
last_won_date
latest_deal_date
```

Choose a stable default sort that preserves current useful behavior. If the current effective order is contact ID ascending, keep that unless a stronger repository-backed reason exists.

Tie-break with `contact_id` for deterministic output.

Do not build SQL strings from untrusted sort input. This report currently loads local facts into Python and can sort Python rows directly; if SQL is introduced, use an allowlist mapping only.

If an invalid sort/order value is supplied, return a safe FastAPI validation/client error or fall back deterministically. Prefer explicit validation for clarity.

### 2. Frontend filters

Update `frontend/src/api.ts` and `frontend/src/App.tsx` filters to include:

- `contactId` / `contact_id` exact ID search;
- `sort`;
- `order`.

Add a compact `ID контакта` filter input near the text search. Keep it numeric/user-friendly, but do not make the UI fragile: empty value should remove the filter.

When any filter changes, reset `offset` to `0`.

Fix `Сбросить` / empty-state reset so it reliably:

- clears text search draft;
- clears contact ID draft/filter;
- clears type/region/status filters;
- resets pagination offset to `0`;
- triggers the contacts table to refetch/update.

### 3. Frontend sortable table

Make table headers sortable for the useful columns above.

Requirements:

- clicking a sortable header changes `sort` / `order` and resets `offset` to `0`;
- current sort state is visible in the header with a simple text/icon indicator;
- keyboard/button semantics are accessible enough for a data table;
- sorting works with active filters and pagination;
- no local Bitrix calls are added.

Prefer existing dependencies and patterns. Do not add TanStack Table or another dependency unless it is clearly justified by repository style and scope.

### 4. New/renamed visible table fields

Update the current Contacts table columns:

- Show contact ID with a nearby `Посмотреть` link:

```text
https://dialar.bitrix24.by/crm/contact/details/{contact_id}/
```

  Open it in a new tab/window and use safe rel attributes. This is a contact details link, not a deal details link.

- Add `Дата закрытия` using `last_won_date` from the analytics response.
- Add `Бюджет USD` using `revenue_usd` from the analytics response.
- Keep or rename the existing financial column as needed to avoid duplicate/confusing labels. It is acceptable for `Бюджет USD` to replace the current `Выручка USD` label if it still displays `revenue_usd`.
- Keep `Расчетная прибыль USD` and existing deal counts.
- Keep `Последняя сделка` if it remains useful and the table still fits; otherwise document the chosen compact layout in `.ai/report.md`.

### 5. Documentation

Update relevant docs if API params or frontend verification flow changed. At minimum consider:

- `frontend/README.md`;
- `docs/development.md`.

Do not update `ui-kits/`.

### 6. Tests

Add focused backend coverage for:

- contact ID filtering on `/api/reports/contacts/analytics` report logic or API path;
- sorting by at least `revenue_usd` and a date field before pagination;
- invalid/unsupported sort handling, if explicit validation is implemented;
- deterministic tie-break by `contact_id`.

Frontend has no current test framework beyond TypeScript build. Keep changes type-safe and run the build.

### 7. Report

Update `.ai/report.md` with:

- exact behavior implemented;
- changed backend params;
- visible UI changes;
- how reset filters was fixed;
- tests/checks run;
- confirmation that no Bitrix write methods were added and frontend still calls only local backend endpoints.

## Out Of Scope

- New frontend screens.
- A per-deal table or Deals screen.
- Changing contact/deal matching, Bitrix extraction, normalization, priorities, currency conversion, revenue/profit formulas, ABC/RFM logic, or manual refresh pipeline.
- Calling Bitrix from the frontend.
- Adding mass `crm.deal.contact.items.get` scans.
- Any Bitrix write operation.
- Exporting CSV/raw data.
- Showing phones, email, addresses, messengers, comments, files, requisites, activities, arbitrary custom fields, webhook values, or raw payloads.
- Changing `ui-kits/`.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- The Contacts screen must continue to use `/api/reports/contacts/analytics` for financial metrics.
- All sorting/filtering/reporting must use local backend data only.
- Do not add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit `.env`, DuckDB files, Parquet snapshots, raw exports, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Keep the UI compact and operational; no marketing/landing page changes.

## Acceptance Criteria

- Contacts table can be sorted by useful visible columns, and sorting is stable across pagination.
- Filter area includes exact search by contact ID.
- Reset filters clears all filters/searches and visibly refreshes/updates the table.
- Table shows `Дата закрытия` from the latest closed won deal date (`last_won_date`) for the contact.
- Table shows `Бюджет USD` from `revenue_usd`; original-currency totals are not used as the primary financial metric.
- Contact ID area includes a `Посмотреть` link to `https://dialar.bitrix24.by/crm/contact/details/{contact_id}/`.
- Existing refresh UX remains intact.
- Existing Contacts empty/loading/error states remain intact.
- No frontend Bitrix calls are added.
- No Bitrix write methods are added or called.
- Backend tests pass.
- Frontend build passes.
- `.ai/report.md` is updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-13 Improve Contacts verification UI
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
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests
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
- backend contact analytics supports the new filter/sort contract safely;
- frontend sends the new params and renders the requested verification UI;
- reset filters has been fixed and verified;
- required backend tests and frontend build are run, or any inability is explicitly documented with reason;
- `.ai/report.md` states that no Bitrix write methods were added or called;
- frontend still calls only local backend endpoints, not Bitrix;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
