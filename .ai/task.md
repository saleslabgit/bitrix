# Task: TASK-2026-06-22-29

Status: planned
Created from: current `main` after `TASK-2026-06-22-28`

## Title

Fix report workspace width

## Goal

Fix the frontend layout regression after `TASK-2026-06-22-28`:

- during loading, the table card collapses into a narrow centered card;
- after loading, the table card does not use the full available workspace width.

The report workspace must use the full width and height available to the main content area.

## User Request

The user reported two visual issues with screenshots:

1. Loading state renders as a narrow centered table card instead of a full-width workspace table.
2. After data loads, the table is still not full-width.

## Facts

- `TASK-2026-06-22-28` introduced the dense report workspace, right filter drawer, and full-height table card.
- Current `frontend/src/styles.css` still has shared styles:

```css
.toolbar,
.table-card {
  margin: 0 auto;
  ...
}
```

- `.table-card` is a flex item inside `.main-panel`.
- In a column flex layout, `margin: 0 auto` on the cross axis can prevent the card from stretching to full available width.
- Current `.table-card` has flex/height behavior but does not explicitly force `width: 100%`.
- Loading state uses `ContactsSkeleton` inside the same `.table-card`, so the card width can collapse around skeleton content.
- Current screenshots show:
  - loading: narrow centered card;
  - loaded: table card centered and not using the available main panel width.
- Backend/data behavior is not part of this bug.
- Bitrix must remain read-only and report page loads must stay local-only.

## Scope

### 1. Fix table card width in all report states

Update `frontend/src/styles.css` and `frontend/src/App.tsx` only if needed.

Required behavior:

- `.table-card` must fill the available width of `.main-panel` in Contacts, Deals, and ABC.
- Loading, refreshing, empty, error, and loaded states must use the same full-width table card shell.
- The table card must not center itself by content width.
- The table card must preserve current viewport-bounded height behavior.
- The table card must keep horizontal table scrolling for wide tables.
- The table card must not overflow under the sidebar.
- The table card should respect the main panel padding, but should otherwise span from left to right inside that panel.

Expected CSS direction:

- Remove or override `margin: 0 auto` for `.table-card`.
- Add explicit `width: 100%` and `max-width: none` where needed.
- Keep `.toolbar` behavior unaffected if no inline toolbars remain visible, but avoid broad changes that could break drawer controls.
- Ensure `.table-scroll`, `table`, skeleton, and state panels do not force shrink-to-content width.

### 2. Fix loading state presentation

Required behavior:

- When table data is pending, the loading/skeleton state appears inside a full-width, full-height table card.
- Loading state should not show a narrow standalone card in the center of the page.
- Pagination should not show misleading `Страница 1 из 1` if there is no loaded table data yet, unless existing behavior intentionally keeps pagination visible; prefer hiding pagination while active table query is pending.

### 3. Preserve TASK-28 behavior

Do not regress:

- compact top action row;
- right-side filter drawer;
- full-height workspace;
- sticky table headers;
- visible bottom pagination when data is loaded;
- contact revenue chart modal;
- Contacts/Deals/ABC sorting and pagination;
- region filters/columns remain hidden.

### 4. Documentation and report

Update docs only if the layout behavior documentation materially changes.

Update `.ai/report.md` with:

- root cause;
- changed files;
- checks run;
- browser/visual verification result;
- any remaining risk.

## Out Of Scope

- Backend changes.
- Data calculation changes.
- New filters or columns.
- Changing chart endpoint/modal behavior unless it is required by layout fix.
- Re-enabling region filters/columns.
- Editing `ui-kits/`.
- Calling Bitrix from report pages.

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

- In loading state, Contacts table card is full-width inside the main workspace, not a narrow centered card.
- After loading, Contacts table card is full-width inside the main workspace.
- Deals and ABC table cards also remain full-width.
- Table card still extends to the bottom of the viewport.
- Table rows still scroll inside the card.
- Table headers remain sticky while scrolling rows.
- Pagination remains visible at the bottom when data is loaded.
- There is no large unused horizontal space caused by the card being centered/narrow.
- Existing drawer filters and contact revenue modal still work.
- No Bitrix calls or CRM write methods are added.
- `.ai/report.md` is updated.

## Checks

Required before implementation:

```bash
git log --oneline -5
git status --short
```

Frontend checks:

```bash
cd frontend && npm run build
```

Runtime/browser verification if practical:

```bash
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
```

Browser verification must include:

- a loading or simulated pending state screenshot/measurement, if practical;
- loaded Contacts screen at a wide desktop viewport similar to the user screenshot;
- verify `.table-card` width is approximately the `.main-panel` content width, not shrink-to-content;
- verify the card reaches the bottom of the viewport.

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
- frontend build is recorded;
- browser/runtime verification is recorded or explicitly marked unavailable;
- no Bitrix write methods were added.

Commit message:

```text
codex: TASK-2026-06-22-29 Fix report workspace width
```