# Task: TASK-2026-06-22-25

Status: planned
Created from: current `main` after `TASK-2026-06-22-24`

## Title

Fix ABC filter layout and changed-only UX

## Goal

Fix the ABC report header/filter layout so controls never overflow outside the visible report workspace.

Also make the changed-only filter understandable and safe: it should clearly mean "show only customers whose ABC segment changed between the `Было` and `Стало` periods".

## User Request

The user reported that the ABC filter block overflows horizontally: controls such as `Стало с`, `Стало по`, `Применить стало`, and `Сбросить` run outside the report area on the current screen width.

The user also does not understand the current checkbox labeled `Только изменения`.

## Facts

- `TASK-2026-06-22-23` added the ABC frontend screen.
- `TASK-2026-06-22-24` corrected ABC comparison direction to `Было -> Стало` and relabeled the period inputs.
- Current ABC filter controls are too wide for the current report card/work area and do not wrap or constrain correctly.
- ABC UI state is stored under `bitrix-sales.abc.v1`.
- Contacts and Deals report behavior must remain unchanged.
- Region filters and region columns remain hidden in the frontend.
- ABC report pages read only local backend endpoint `GET /api/reports/abc/analytics`.

## Assumptions

- This is a frontend-only task unless implementation inspection proves a small API parameter guard is required.
- The table itself may keep horizontal scrolling if needed, but filter/header controls must stay inside the visible page/workspace.
- It is acceptable to change CSS layout classes used by the shared report shell as long as Contacts and Deals do not regress visually.

## Unknowns

- Browser visual verification environment may or may not be available to Codex.
- Exact user viewport width is not known; the screenshot appears to be around a common laptop/desktop width with sidebar enabled.

## Scope

### 1. Fix ABC filter layout overflow

Update `frontend/src/App.tsx` and `frontend/src/styles.css` as needed so the ABC filter area is responsive.

Required behavior:

- ABC filter controls must wrap to additional rows or use a responsive grid/flex layout.
- No filter control may extend outside the report card or outside the main visible workspace.
- The left side of the filter row must not be clipped.
- The page must not gain accidental horizontal overflow because of the ABC filter toolbar.
- Date inputs and action buttons should keep usable widths and not collapse into unreadable controls.
- The layout must work with the sidebar visible.
- Keep the existing compact operational style from the current UI.

Recommended approach:

- Prefer a responsive CSS grid/flex layout for the ABC filter toolbar.
- Allow filter groups to wrap.
- Use `min-width: 0`, `max-width: 100%`, and sane control widths where needed.
- Avoid fixed widths that assume a wide screen.

### 2. Clarify changed-only checkbox

Replace the unclear visible copy:

```text
Только изменения
```

with clearer copy, for example:

```text
Только изменившие сегмент
```

or an equivalent concise Russian label.

Required behavior:

- The label must make it clear that the filter is about ABC segment changes.
- The filter must only apply when the `Стало` period is actually enabled/applied.
- If no `Стало` period is enabled, the checkbox should either be hidden or disabled.
- If hidden/disabled while persisted state has `changedOnly = true`, the frontend must not silently send `changed_only=true` for a single-period ABC report.
- When `Стало` is enabled, the checkbox should filter to rows where `segment_changed = true` according to `Было -> Стало` semantics.

### 3. Preserve existing behavior

Do not change:

- backend ABC calculation logic from `TASK-2026-06-22-24`;
- Contacts report filters, columns, and navigation behavior;
- Deals report filters, columns, totals, and navigation behavior;
- Bitrix refresh flow;
- region hidden state;
- `ui-kits/` files.

### 4. Documentation and report

Update only the documentation that is materially affected by this UX behavior.

Always update `.ai/report.md` with:

- what changed;
- which files changed;
- checks run;
- whether browser visual verification was run;
- any remaining risk.

## Out Of Scope

- New backend ABC metrics.
- New report screens.
- Reworking the whole layout system.
- Changing ABC segment thresholds or migration priorities.
- Re-enabling region filters/columns.
- Editing `ui-kits/`.

## Constraints

- Work only in the GitHub repository state.
- Keep Bitrix read-only; this task must not add Bitrix calls.
- Do not expose or commit secrets, `.env`, local databases, generated data, logs, caches, `node_modules`, `frontend/dist`, or raw data.
- Do not add CRM write methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not use `git add .`.

## Acceptance Criteria

- On the ABC screen, the filter/header controls stay inside the visible report workspace at common desktop widths with the sidebar open.
- The ABC filter block no longer overflows to the right as shown in the user screenshot.
- The ABC filter block can wrap to multiple rows without clipping controls.
- The changed-only checkbox has a clear label about segment changes.
- `changed_only=true` is not sent for single-period ABC mode when `Стало` is not enabled.
- With `Стало` enabled, changed-only mode still filters only changed ABC transitions.
- Contacts and Deals screens still build successfully and are not intentionally changed.
- No Bitrix write methods are added.
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

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src
```

If browser verification is practical, run a real visual check for the ABC page width behavior and document the result. If not practical, say so in `.ai/report.md`.

## Hard Workflow Gate

Before committing, verify:

- only task-related files are staged;
- no forbidden artifacts are staged;
- `ui-kits/` is not staged;
- `.ai/report.md` is updated;
- frontend build result is recorded;
- safety search result is recorded.

Commit message:

```text
codex: TASK-2026-06-22-25 Fix ABC filter layout
```