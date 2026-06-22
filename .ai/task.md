# Task: TASK-2026-06-22-28

Status: planned
Created from: current `main` after `TASK-2026-06-22-27`

## Title

Add sticky tables and contact revenue chart

## Goal

Improve report table usability and add a customer-level revenue chart from the Contacts table.

User-facing goals:

- report tables should use only the available viewport height;
- table top and bottom controls should stay visible while scrolling table rows;
- clicking a customer name in the Contacts table should open a modal with a chart of closed won deals for that customer.

## User Request

The user confirmed the previous `/api/meta/filters` issue no longer happens and asked for the next task:

- In tables, pin the top and bottom and make tables only as tall as the screen.
- In the clients table, clicking a client name should open a popup with a chart of closed deals for the selected filter period.
- X axis: deal close dates.
- Y axis: revenue.

## Facts

- Frontend currently has Contacts, Deals, and ABC report screens in `frontend/src/App.tsx`.
- Tables currently live inside `.table-card` with `.table-scroll` using horizontal scroll only.
- Pagination lives below the table inside the same card.
- Deals and ABC reports also show totals bars above and below their tables.
- Contacts rows currently show contact name as plain text inside `.contact-cell`.
- Contacts filters currently include:
  - search;
  - exact contact ID;
  - contact type;
  - deal status;
  - deal creation date range labeled `Создана с` / `Создана по`.
- Backend contact analytics already supports `date_from` / `date_to` over reporting dates and `deal_created_from` / `deal_created_to` over deal creation dates, but the current Contacts UI exposes only deal creation dates.
- Revenue is always won-only USD.
- The frontend package currently has no charting library dependency.
- Project requirements allow charts through Recharts or ECharts.
- Bitrix is read-only and report page interactions must read only local backend endpoints.
- Region filters/columns remain hidden in frontend.

## Product Semantics

### Sticky table workspace

Apply the table workspace behavior consistently to Contacts, Deals, and ABC reports.

Definitions:

- `Top` means the table column header row must remain visible while scrolling table rows.
- `Bottom` means pagination and bottom totals, when present, must remain visible while scrolling table rows.
- The table body area should scroll inside the card instead of making the whole page grow indefinitely.

Expected report behavior:

- The visible report card should fit within the current viewport as much as practical after the page header and filters.
- Table rows scroll vertically inside the table area.
- Table rows still scroll horizontally when the table is wider than the viewport.
- Contacts, Deals, and ABC table headers remain visible while vertical scrolling rows.
- Pagination remains visible at the bottom of the card.
- For Deals and ABC, totals bars must remain readable; the bottom totals bar should stay with the bottom controls or remain visible in the fixed bottom area.
- Do not break existing sorting, pagination, empty/error/loading states, or horizontal scroll.

### Contact revenue chart popup

Clicking the customer/contact name in the Contacts table opens a modal popup.

The chart must show closed won deals assigned to the selected analytical contact.

Chart rules:

- Only local data is used.
- Only deals where `status_group == "won"` are included.
- X axis is `closed_at` date.
- Y axis is won revenue in USD.
- If multiple won deals have the same close date, aggregate/sum them for that date.
- Points must be sorted by close date ascending.
- The modal should show customer name and ID.
- Show total revenue and deal count for the charted period.
- Show loading, error, and empty states.
- Closing the modal must not reset table filters, sorting, or pagination.

Period semantics for this task:

- The chart period should follow the current Contacts screen date filters as the user's selected period.
- Because the current Contacts UI exposes `Создана с` / `Создана по`, pass those values from the Contacts state to the chart request as the selected period context.
- The backend endpoint should support explicit closed-date filtering parameters (`date_from` / `date_to`) because the chart itself is by close date.
- Frontend should map the current Contacts date filter to the chart period for now and clearly label the modal period so the behavior is understandable.
- If no date filter is selected, show all closed won deals for that contact.

If implementation finds that current date semantics are too misleading, document the concern in `.ai/report.md` and choose the smallest safe behavior that still lets the user inspect closed won deal revenue by close date.

## Scope

### 1. Backend contact revenue series endpoint

Add a local-only backend endpoint for the chart.

Recommended endpoint:

```text
GET /api/reports/contacts/{contact_id}/won-revenue-series
```

Recommended query parameters:

```text
date_from?: YYYY-MM-DD
date_to?: YYYY-MM-DD
```

Required response fields:

- `contact_id`;
- `contact_name`;
- `date_from`;
- `date_to`;
- `total_revenue_usd`;
- `won_deals_count`;
- `points`.

Each point should contain:

- `closed_date`;
- `revenue_usd`;
- `won_deals_count`.

Data source and constraints:

- Use `normalized_deals` and existing local currency conversion logic / `_load_deal_facts()` patterns.
- Include only deals with `analytical_contact_id == contact_id`.
- Include only `status_group == "won"`.
- Include only deals with non-null `closed_at`.
- Filter by `closed_at.date()` using `date_from` / `date_to` inclusively.
- Aggregate by close date.
- Return empty `points` and zero totals if the contact exists but has no matching won deals.
- Return a safe 404 if the contact does not exist.
- Do not expose deal names, raw rows, private fields, local paths, or secrets.
- Do not call Bitrix.

Add backend dataclasses/models/tests consistently with current patterns in:

- `backend/app/reports/analytics.py`;
- `backend/app/api/models.py`;
- `backend/app/main.py`;
- backend tests.

### 2. Frontend modal and chart

Add a Contacts table interaction:

- Contact name becomes a button/link-style control.
- Clicking it opens a modal.
- The modal fetches the new backend endpoint for that contact and current Contacts selected period.
- Modal must not navigate away and must not modify report filters.
- Modal must be keyboard accessible enough for current UI standards:
  - visible close button;
  - click backdrop or close button closes;
  - `Escape` closes if practical;
  - use dialog semantics (`role="dialog"`, `aria-modal="true"`).

Chart implementation:

- Prefer adding Recharts as the charting dependency.
- Update `frontend/package.json` and lockfile if dependency changes.
- Use a compact line or bar chart suitable for revenue over dates.
- Format Y values as USD using existing money formatting conventions.
- Format X values as close dates.
- Render a useful empty state when there are no won closed deals in the period.
- Keep the chart readable in a modal on desktop and usable on narrower screens.

### 3. Sticky table workspace

Update `frontend/src/App.tsx` and `frontend/src/styles.css` so Contacts, Deals, and ABC tables use a viewport-bounded card layout.

Required behavior:

- The table card has a bounded height based on the viewport.
- `.table-scroll` supports vertical and horizontal scrolling.
- `thead th` are sticky at the top of the scroll area.
- Pagination is visible at the bottom without scrolling to the last row.
- Bottom totals, where present, remain visible with the bottom area or otherwise do not disappear while scrolling rows.
- Long tables should not make the whole page vertically huge.
- Existing empty/loading/error states still look acceptable.
- No overlap, clipping, or unreadable controls at common desktop widths.

### 4. Documentation and report

Update relevant docs:

- `docs/development.md` for new endpoint and frontend behavior;
- `docs/data-model.md` for the contact won revenue series output if needed;
- `frontend/README.md` for the modal/chart and sticky table behavior.

Update `.ai/report.md` with:

- changed files;
- backend endpoint semantics;
- frontend chart/modal behavior;
- sticky table implementation notes;
- checks run;
- whether browser visual verification was run;
- risks/unknowns.

## Out Of Scope

- Re-enabling region filters or columns.
- Changing Contacts, Deals, or ABC analytics metric semantics outside the new chart endpoint.
- Adding a new full report screen.
- Exporting data.
- Showing phone, email, address, messengers, comments, files, requisites, or raw Bitrix fields.
- Calling Bitrix from the chart/modal or report page load.
- Editing `ui-kits/`.
- Reworking the whole app navigation.

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
- If adding Recharts, commit only package metadata/lockfile changes, not installed dependency folders.
- Do not use `git add .`.

## Acceptance Criteria

### Table UX

- Contacts, Deals, and ABC report cards are viewport-bounded.
- Table rows scroll inside the table area.
- Table headers stay visible while scrolling rows.
- Pagination stays visible at the bottom of the card.
- Deals and ABC totals remain readable and usable with the bounded table layout.
- Existing sorting and pagination continue to work.

### Contact chart

- Clicking a contact/customer name in the Contacts table opens a modal.
- Modal displays the selected contact name and ID.
- Modal shows a chart of won revenue by close date for that contact.
- X axis uses close dates.
- Y axis uses USD revenue.
- Multiple won deals on the same close date are aggregated.
- Modal shows total revenue and won deal count for the charted period.
- Empty/error/loading states are handled.
- Closing the modal preserves Contacts filters, sorting, and pagination.

### Data and safety

- Chart uses only local backend data.
- Chart endpoint does not call Bitrix.
- Chart endpoint does not expose forbidden personal fields or raw rows.
- No CRM write methods are added.
- Docs and `.ai/report.md` are updated.

## Checks

Required before implementation:

```bash
git log --oneline -5
git status --short
```

Backend checks:

```bash
cd backend && python -m pytest tests/test_api_local.py tests/test_analytics.py
```

If shared analytics helpers are touched broadly, run full backend tests:

```bash
cd backend && python -m pytest
```

Frontend checks:

```bash
cd frontend && npm run build
```

If a new frontend dependency is added, run package install/update in the standard frontend workflow and verify the lockfile is updated without committing `node_modules` or `frontend/dist`.

Runtime/browser verification if practical:

```bash
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:8000/api/meta/filters
curl -f http://localhost:5173/
```

Then verify in browser:

- Contacts/Deals/ABC table header and bottom controls stay visible while rows scroll;
- Contacts name click opens modal;
- chart loads and closes correctly.

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src
```

## Hard Workflow Gate

Before committing, verify:

- only task-related files are staged;
- no forbidden artifacts are staged;
- `ui-kits/` is not staged;
- `node_modules` and `frontend/dist` are not staged;
- `.ai/report.md` is updated;
- backend tests are recorded;
- frontend build is recorded;
- browser/runtime verification result is recorded or explicitly marked unavailable;
- no Bitrix write methods were added.

Commit message:

```text
codex: TASK-2026-06-22-28 Add sticky tables and contact revenue chart
```