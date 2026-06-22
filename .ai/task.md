# Task: TASK-2026-06-22-14

Status: planned
Created from: current `main` after `3708a6b codex: TASK-2026-06-22-13 Improve Contacts verification UI`

## Title

Add contact budget breakdown columns

## Goal

Refine the existing Contacts analytics table so financial columns match the product owner's verification logic:

- `Бюджет` — sum of all deals assigned to the contact;
- `Бюджет в работе` — sum of open deals assigned to the contact;
- `Бюджет проигранных` — sum of lost deals assigned to the contact;
- `Выручка` — sum of won deals assigned to the contact;
- `Прибыль` — the current estimated profit field, renamed in the UI.

Also rename deal-count columns, make first sort click descending, and expand the working area to use the available screen width with small side padding.

## Facts

- The user tested TASK-13 and said everything works.
- The user clarified that the current `Бюджет USD` logic is not correct for their verification needs because it currently displays `revenue_usd`, i.e. won-only revenue.
- Current Contacts analytics response includes `revenue_usd` and `estimated_profit_usd`, but does not include separate all/open/lost deal budget sums.
- Current `revenue_usd` must remain won-only revenue.
- Current estimated profit rule remains unchanged: `estimated_profit_usd = revenue_usd * 0.50`.
- All financial analytics must be in USD.
- The Contacts screen remains an aggregate contact-level table, not a per-deal table.
- Current visible count columns are labeled `Won`, `Open`, `Lost`.
- Current sorting toggles to ascending on the first click for a new column because `updateSort()` sets `asc` when the clicked field is not already active.
- Current layout uses `max-width: var(--grid-desktop-max)` for the page header, toolbar, alerts, and table card. The user wants large tables to use the full available screen width with only small side padding.
- Bitrix remains read-only. This task must not change extraction, refresh, normalization, contact selection, or Bitrix calls.

## Assumptions

- `Бюджет` means `sum(amount_usd)` for all deals whose `analytical_contact_id` is the contact, across statuses `won`, `open`, and `lost` within the active local report period.
- `Бюджет в работе` means `sum(amount_usd)` for open deals assigned to the contact.
- `Бюджет проигранных` means `sum(amount_usd)` for lost deals assigned to the contact.
- `Выручка` means the existing won-only `revenue_usd`.
- `Прибыль` means the existing `estimated_profit_usd`, no formula change.
- UI column labels should be the exact Russian business labels above. The values should still be formatted as USD currency; do not display original-currency totals.
- For a first click on any sortable column, `order` should become `desc`. Subsequent clicks on the same column should toggle `desc` / `asc`.
- Expanding the working area means the content area inside the existing app shell/sidebar should use full available width; do not add or remove screens/navigation.

## Unknowns

- Whether the user wants these new budget sums to be affected by the existing `status` filter. Keep the current report behavior consistent: filters apply first, then the displayed aggregates reflect the filtered local report rows. If implementation discovers existing semantics differ, document the exact behavior in `.ai/report.md`.
- Whether every date-period edge case is already covered by existing tests. Add focused tests for the new financial aggregates using the current period/reporting-date semantics.

## Scope

### 1. Backend contact analytics budget aggregates

Extend `ContactAnalyticsRow` and `ContactAnalyticsResponse` with explicit USD fields for the new budget breakdown.

Preferred field names:

```text
budget_usd                 # all deal statuses
budget_in_work_usd          # open deals
lost_budget_usd             # lost deals
```

Keep existing fields:

```text
revenue_usd                 # won only
estimated_profit_usd        # revenue_usd * 0.50
```

Calculation rules:

- Use `_DealFact.amount_usd`, already converted locally to USD.
- Include only deals assigned to the contact via `analytical_contact_id`.
- Preserve the existing period filtering behavior of `list_contact_analytics()`.
- Do not change ABC/RFM/concentration formulas; they remain won-revenue based.
- Do not use original currency totals as primary financial columns.

### 2. Backend sorting allowlist

Add the new budget fields to the contact analytics sort allowlist and FastAPI sort literal:

```text
budget_usd
budget_in_work_usd
lost_budget_usd
```

Keep sorting deterministic with `contact_id` tie-break.

### 3. Frontend API types

Update `frontend/src/api.ts`:

- add the new response fields to `ContactAnalytics`;
- add the new sort fields to `ContactSort`;
- keep existing local backend endpoints only.

### 4. Frontend table columns and labels

Update the Contacts table columns to show the requested financial columns:

| Label | Source |
|---|---|
| `Бюджет` | `budget_usd` |
| `Бюджет в работе` | `budget_in_work_usd` |
| `Бюджет проигранных` | `lost_budget_usd` |
| `Выручка` | `revenue_usd` |
| `Прибыль` | `estimated_profit_usd` |

Rename count labels:

| Current | New |
|---|---|
| `Won` | `Успешные` |
| `Open` | `Открытые` |
| `Lost` | `Проигранные` |

Keep existing useful columns unless layout requires minor reordering. Do not remove contact ID, contact name, type, region, deal counts, dates, or the `Посмотреть` link unless impossible; if a compact ordering is chosen, document it in `.ai/report.md`.

### 5. Sort interaction

Update `updateSort()` behavior:

- if the user clicks a different column, set `sort` to that column and `order` to `desc`;
- if the user clicks the currently active column, toggle `desc` / `asc`;
- reset `offset` to `0` after sort changes.

Make sure the visual sort indicator still matches the actual query params.

### 6. Full-width working area

Adjust frontend layout CSS so large tables use the available screen width:

- remove or override `max-width: var(--grid-desktop-max)` from the working area elements that constrain the Contacts screen (`page-header`, `toolbar`, `table-card`, alerts as needed);
- keep small, consistent side padding on `.main-panel`;
- keep horizontal table scroll for narrow screens;
- avoid overlap/clipping/layout shift;
- do not modify `ui-kits/`.

### 7. Documentation

Update relevant documentation to describe the new Contacts financial fields and layout behavior if needed. At minimum consider:

- `frontend/README.md`;
- `docs/development.md`;
- `docs/data-model.md` if API/output semantics change enough to document.

### 8. Tests

Add focused backend tests for:

- `budget_usd` equals all assigned deal amounts in USD;
- `budget_in_work_usd` equals open assigned deal amounts in USD;
- `lost_budget_usd` equals lost assigned deal amounts in USD;
- `revenue_usd` remains won-only;
- `estimated_profit_usd` remains `revenue_usd * 0.50`;
- sorting by at least one new budget field works before pagination;
- API response includes the new fields.

Frontend has no current test framework beyond TypeScript build. Keep changes type-safe and run the build.

### 9. Report

Update `.ai/report.md` with:

- exact field names added;
- exact formulas implemented;
- UI labels changed;
- sort first-click behavior changed;
- layout change summary;
- tests/checks run;
- confirmation that no Bitrix write methods were added/called and frontend still calls only local backend endpoints.

## Out Of Scope

- New screens.
- Per-deal table.
- Changing Bitrix extraction, refresh, relation completeness, normalization, contact priority rules, currency loading, ABC/RFM/concentration formulas, or manual refresh pipeline.
- Calling Bitrix from frontend.
- Any Bitrix write operation.
- Exporting CSV/raw data.
- Showing phones, emails, addresses, messengers, comments, files, requisites, activities, arbitrary custom fields, webhook values, or raw payloads.
- Changing `ui-kits/`.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- All financial values shown in Contacts table must be USD values from local backend analytics.
- Do not add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit `.env`, DuckDB files, Parquet snapshots, raw exports, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Keep the UI dense and operational.

## Acceptance Criteria

- Contacts analytics API returns `budget_usd`, `budget_in_work_usd`, and `lost_budget_usd` for each contact.
- `budget_usd` is all assigned deals in USD.
- `budget_in_work_usd` is open assigned deals in USD.
- `lost_budget_usd` is lost assigned deals in USD.
- `revenue_usd` remains won-only and is displayed as `Выручка`.
- `estimated_profit_usd` remains `revenue_usd * 0.50` and is displayed as `Прибыль`.
- Count labels are `Успешные`, `Открытые`, `Проигранные`.
- First click on a sortable column sorts descending; second click toggles ascending.
- New budget columns are sortable server-side before pagination.
- Contacts working area uses full available screen width with small side padding and horizontal table scroll where needed.
- Existing refresh UX, filters, ID search, reset, dates, and Bitrix `Посмотреть` links remain working.
- No frontend Bitrix calls are added.
- No Bitrix write methods are added or called.
- Backend tests pass.
- Frontend build passes.
- `.ai/report.md` is updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-14 Add contact budget breakdown columns
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
- new backend budget fields are implemented and covered by tests;
- frontend uses new fields and labels, not old won-only value as `Бюджет`;
- first-click sort behavior is descending;
- full-width working area is implemented without changing `ui-kits/`;
- required backend tests and frontend build are run, or any inability is explicitly documented with reason;
- `.ai/report.md` states that no Bitrix write methods were added or called;
- frontend still calls only local backend endpoints, not Bitrix;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
