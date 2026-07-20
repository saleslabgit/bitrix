# Task: TASK-2026-07-20-05

Status: planned
Created from: `c8ba99597077c7e93c7e45e11064263ec9615de5`

## Title

Pin report summary rows to the bottom and align totals with their table columns

## Goal

Improve the Contacts and Deals report tables so the filter-wide summary row remains visible at the bottom of the table scrolling viewport while the user scrolls through rows.

Every summary value must use the same horizontal alignment and numeric styling as the body cells and header of its corresponding column.

This is a frontend-only presentation task. Preserve all existing report formulas, API contracts, filtering, sorting, pagination, authentication, refresh behavior, and backend-derived summary values.

## Facts

- The current frontend uses `.table-scroll` as the vertically and horizontally scrollable table viewport.
- Table headers are already sticky at the top of that viewport.
- Contacts and Deals render backend-derived filter-wide values in `<tfoot>`.
- Summary values describe the complete filtered selection before pagination.
- Contacts and Deals footer values must not be recalculated from visible browser rows.
- Numeric body cells use the existing `number-cell` class.
- Financial body cells use the existing `number-cell money-cell` classes.
- The current global `th` rule uses `position: sticky; top: 0`; footer cells must not accidentally inherit top-sticky header behavior.
- ABC uses separate summary bars and KEV uses a comparison table. They do not have the sum/average footer row targeted by this task.
- Bitrix remains strictly read-only.
- Docker startup must not refresh Bitrix automatically.

## Assumptions

- “Закрепить внизу” means sticky at the bottom of the table’s own `.table-scroll` viewport, not fixed to the browser window.
- The change applies to both Contacts and Deals because both tables show filter-wide sums and average values.
- The summary row should move horizontally together with the table columns when the user scrolls horizontally.
- Existing summary labels and values remain unchanged unless minor markup changes are required for correct semantics and alignment.

## Unknowns

- None that block implementation.

## Scope

### 1. Inspect the current implementation before editing

Read and follow:

- `AGENTS.md`;
- `WORKFLOW.md`;
- `SPEC.md`;
- `.ai/task.md`;
- `.ai/report.md`;
- `frontend/README.md`;
- `docs/project-status.md`;
- `docs/development.md`.

Inspect at minimum:

- `ContactsTable` in `frontend/src/App.tsx`;
- `DealsTable` in `frontend/src/App.tsx`;
- `.table-scroll`, table header, numeric cell, money cell, and table footer styles in `frontend/src/styles.css`.

Before editing run:

```bash
git log --oneline -8
git status --short
```

Do not overwrite unknown local changes.

### 2. Add a dedicated summary-footer presentation contract

Add a clear reusable class to the Contacts and Deals table footers, for example:

```text
table-summary-footer
```

The exact name may follow existing repository conventions, but both footers must use one consistent contract.

Requirements:

- Keep valid semantic table markup with `<tfoot>`.
- Prefer a row-header cell with `scope="row"` for `Итого по выборке` where practical.
- Do not use `position: fixed`.
- Do not move the summary outside the table into a separate grid that could drift from column widths.
- Do not duplicate summary values above and below the table.

### 3. Make the summary row sticky at the bottom

Within `.table-scroll`, the summary footer must remain visible while body rows scroll vertically.

Requirements:

- Footer cells use sticky positioning with `bottom: 0`.
- Footer cells explicitly override inherited header positioning, including `top: auto` when required.
- The footer has an opaque design-system background so body text does not show through.
- Add a clear top border and, if useful, a subtle design-system shadow to distinguish the fixed summary from scrolling rows.
- Use an appropriate z-index so body rows pass behind the footer.
- Preserve the existing sticky header at the top.
- The sticky footer must not cover or replace the pagination controls below `.table-scroll`.
- The footer remains part of the horizontally scrollable table and stays aligned during horizontal scrolling.
- The final data row remains reachable; scrolling to the bottom must not hide content permanently behind the sticky footer.
- Do not introduce a second independent vertical scrollbar.

### 4. Align the Contacts summary with Contacts columns

Reformat the current compact one-line Contacts `<tfoot>` into readable JSX.

Preserve the existing logical Contacts columns and backend fields.

Apply the same classes used by body cells:

- deal counts: `number-cell`;
- budget, budget in work, lost budget, revenue, profit, and average check: `number-cell money-cell`;
- average cycle: `number-cell`;
- non-aggregatable date/text placeholders: the same left alignment as their columns.

Requirements:

- The summary row must have the same logical column count as the Contacts header and body.
- A `colSpan` over the initial text columns is allowed only when all subsequent summary cells still map exactly to their columns.
- `Итого по выборке` remains clearly visible.
- Zero values must remain visible and correctly formatted; do not replace numeric zero with `—` through a truthiness check.
- Nullable averages continue to display `—`.
- Add right alignment to numeric average headers if needed so header, body, and footer alignment are consistent across the full column.

### 5. Align the Deals summary with Deals columns

Preserve the exact 12-column Deals order:

1. ID;
2. deal name;
3. status;
4. KEV;
5. funnel;
6. cycle, days;
7. contact type;
8. budget;
9. estimated profit;
10. created date;
11. closed date;
12. average check.

Footer requirements:

- exactly 12 logical column positions;
- `Итого по выборке` in the first position;
- status counts remain in the status position;
- KEV, funnel, contact type, and date placeholders remain in their own positions;
- average cycle uses `number-cell`;
- budget and estimated profit use `number-cell money-cell`;
- average check uses `number-cell money-cell`;
- numeric body/header/footer values align consistently to the right;
- status and text values retain the same left alignment as their columns;
- zero average check remains a formatted zero when the backend returns zero, while `null` remains `—`.

If necessary, add the existing numeric alignment class to the Deals cycle and average-check headers so the whole columns align consistently.

### 6. Preserve scrolling and report behavior

Do not change:

- report API calls;
- query keys;
- filters;
- sorting behavior;
- pagination calculations;
- active-filter counts;
- Contacts-to-Deals navigation;
- summary formulas or backend response models;
- loading, error, empty, authentication, refresh, and session-expiry states;
- local-storage behavior;
- ABC and KEV report behavior.

The table should still support both vertical and horizontal scrolling.

### 7. Frontend quality

Use existing design tokens and repository style.

Requirements:

- no hard-coded color values when an existing design token fits;
- no unrelated visual redesign;
- no `ui-kits/` changes;
- no new frontend dependency;
- no compressed one-line footer JSX;
- no duplicated CSS rules when one reusable footer class is sufficient;
- sticky footer styling must work in both local Vite and production nginx builds.

### 8. Browser/operator verification

Use a local synthetic dataset only. Do not make live Bitrix calls.

Verify Contacts and Deals with enough rows to require vertical scrolling.

At minimum verify:

- the table header remains pinned at the top;
- the summary footer remains pinned at the bottom at the top, middle, and end of vertical scrolling;
- header, body, and footer have matching logical cell counts;
- the footer moves horizontally with the table;
- the footer does not cover pagination;
- the last body row can be reached;
- count and numeric columns are right-aligned consistently;
- money columns are right-aligned consistently;
- text/status columns remain left-aligned;
- both a wide desktop viewport and a narrower viewport with horizontal scrolling work;
- Contacts and Deals loading, empty, and normal data states remain usable.

Prefer an automated headless browser check using temporary tooling that is not committed. If browser automation is unavailable, perform a concrete manual operator check and record exact steps and results in `.ai/report.md`.

### 9. Documentation

Update concise frontend behavior documentation where relevant:

- `frontend/README.md`;
- `docs/project-status.md`.

Document that Contacts and Deals use sticky filter-wide summary rows inside the table viewport and that summary values align with their corresponding columns.

Do not update backend or data-model documentation unless implementation unexpectedly changes those contracts, which is outside scope.

### 10. Implementation report

Replace `.ai/report.md` with a clean report for this task only.

Include:

- exact changed files;
- frontend build result;
- Compose configuration results;
- exact browser/operator verification method and result;
- confirmation that Contacts and Deals footers remain sticky and aligned;
- confirmation that no backend formulas or APIs changed;
- confirmation that no live Bitrix calls were made;
- remaining risks, if any.

## Out Of Scope

- Backend analytics changes.
- API response changes.
- Database/schema changes.
- Metric formula changes.
- New reports or screens.
- Changes to ABC summary bars.
- Changes to the KEV comparison table.
- Export, printing, or mobile redesign.
- Automatic Bitrix refresh.
- Live Bitrix calls.
- Changes to authentication.
- Production deployment itself.
- New frontend dependencies or a permanent new test framework.
- Unrelated refactoring.

## Constraints

- Keep Bitrix strictly read-only.
- Never add or call Bitrix write methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not make live Bitrix calls.
- Do not modify `.ai/task.md` during implementation.
- Do not use `git add .`.
- Do not commit `.env`, secrets, webhook URLs, DuckDB, Parquet, CSV, raw data, logs, caches, `node_modules`, `frontend/dist`, browser screenshots, Playwright artifacts, or temporary test tooling.
- Docker startup must continue to start services only and must not refresh Bitrix automatically.

## Acceptance Criteria

### Sticky behavior

- Contacts summary row remains visible at the bottom of `.table-scroll` during vertical scrolling.
- Deals summary row remains visible at the bottom of `.table-scroll` during vertical scrolling.
- Both footers scroll horizontally with their tables.
- Existing sticky headers continue to work.
- Pagination remains visible and usable below the table viewport.
- The final body row remains reachable.

### Alignment

- Contacts footer cells align with their corresponding Contacts columns.
- Deals footer cells align with their corresponding Deals columns.
- Counts and numeric values are right-aligned consistently.
- Money values are right-aligned and use existing financial emphasis.
- Text and status values retain the established left alignment.
- Header, body, and footer cell geometry remains consistent.
- Zero values display as zero; only unavailable nullable values display `—`.

### Regression safety

- Filter-wide values still come directly from backend response fields calculated before pagination.
- No report formulas or API contracts change.
- Filters, sorting, pagination, local storage, navigation, authentication, and manual refresh behavior remain unchanged.
- ABC and KEV remain unchanged.
- Frontend build passes.
- Local and production Compose configurations pass.
- Browser/operator verification passes on Contacts and Deals.
- No live Bitrix call occurs.
- No secrets or generated files are committed.

## Checks

Before implementation:

```bash
git log --oneline -8
git status --short
```

Frontend build:

```bash
cd frontend
npm run build
```

Compose configuration:

```bash
docker compose config
docker compose -f docker-compose.prod.yml config
```

Local operator flow with synthetic data and live Bitrix disabled:

```bash
BITRIX_WEBHOOK_URL="" docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
```

After browser verification:

```bash
docker compose down -v
```

Diff validation:

```bash
git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'
```

Safety review:

```bash
git status --short --branch
git diff --name-only --cached
```

Confirm no forbidden or generated files are staged.

## Hard Workflow Gate

Before commit:

- Contacts sticky footer is verified in a real browser or headless browser;
- Deals sticky footer is verified in a real browser or headless browser;
- vertical and horizontal scrolling are verified;
- footer alignment is verified against corresponding body columns;
- zero and nullable summary rendering are reviewed;
- pagination and last-row reachability are verified;
- frontend build passes;
- both Compose configuration checks pass;
- `.ai/report.md` contains exact current-task results only;
- only task-related frontend/docs files and `.ai/report.md` are staged;
- no backend/API/data changes are staged;
- no secrets, databases, snapshots, generated files, caches, `node_modules`, `frontend/dist`, browser artifacts, or temporary tooling are staged;
- no live Bitrix call was made;
- Docker startup behavior remains unchanged.

Set `.ai/report.md` status to `done` only when all acceptance criteria and checks pass.

Commit message:

```text
codex: TASK-2026-07-20-05 Pin table summary rows
```
