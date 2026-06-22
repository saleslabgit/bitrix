# Task: TASK-2026-06-22-24

Status: planned
Created from: current `main` after reviewed `TASK-2026-06-22-23`

## Title

Fix ABC comparison direction

## Goal

Correct the ABC comparison model so period transitions always mean:

```text
Было -> Стало
```

A customer who had revenue and ABC segment in the source/baseline period but has no won revenue in the compared/result period must be shown as a loss, for example:

```text
A -> Нет продаж = срочно
```

The current implementation from `TASK-2026-06-22-23` is conceptually wrong for the product workflow because it treats the comparison period as the previous segment and the main period as the current segment. This can make a lost customer look like a growth case such as `развивать` or `закрепить`.

## User Request

The user found that a customer with deals before 2023, when compared with 2025, is shown as `развивать`. This is wrong.

If a customer stopped buying, the transition must be from the old segment to `Нет продаж`:

```text
A -> Нет продаж
```

The whole transition logic must be reviewed and fixed, not only one label.

## Facts

- `TASK-2026-06-22-23` added `GET /api/reports/abc/analytics` and a frontend `ABC` report screen.
- Current backend implementation calculates transition direction as:

```text
comparison segment -> current/main segment
```

- Current docs also state the same direction.
- This direction does not match the user's intended workflow.
- The intended workflow is:

```text
source/baseline period -> compared/result period
```

- ABC is still based only on won USD revenue by `closed_at` period.
- Bitrix is read-only and report page loads must not call Bitrix.
- Region UI remains hidden while region logic is unfinished.

## Product Semantics To Implement

The ABC screen must have two unambiguous period roles:

| Role | Meaning |
|---|---|
| `Было` / source period | the earlier or baseline period from which the transition starts |
| `Стало` / result period | the period being compared against the baseline |

Transition direction is always:

```text
ABC было -> ABC стало
```

Examples:

| Было | Стало | Correct transition | Correct priority |
|---|---|---|---|
| customer was A before 2023 | no won revenue in 2025 | `A -> Нет продаж` | `срочно` |
| customer was B before 2023 | no won revenue in 2025 | `B -> Нет продаж` | `важно` |
| customer was C before 2023 | no won revenue in 2025 | `C -> Нет продаж` | `наблюдать` |
| no won revenue before 2023 | became A in 2025 | `Нет продаж -> A` | `закрепить` |
| B or C before | became A later | `B/C -> A` | `развивать` |

## Assumptions

- The current UI labels `Период` and `Сравнение` are ambiguous and should be replaced with explicit `Было` and `Стало` labels.
- It is acceptable to change the new ABC analytics response shape introduced in the previous task because it has not yet been accepted by the user as correct.
- Existing Contacts and Deals screens must remain unchanged.
- Existing legacy `GET /api/reports/abc` should remain compatible unless a focused test proves it must change.

## Scope

### 1. Backend ABC direction fix

Update `backend/app/reports/analytics.py` and API models/routes so ABC analytics uses explicit before/after semantics.

Recommended implementation:

- Treat `date_from` / `date_to` as the source/baseline period (`Было`).
- Treat `compare_date_from` / `compare_date_to` as the result period (`Стало`).
- Keep query parameter names if that is the smallest safe change, but internally and in response naming prefer clear concepts:
  - `base_*` / `target_*`, or
  - `before_*` / `after_*`, or
  - `previous_*` / `current_*`.
- Do not keep misleading response names if they cause frontend confusion. If names change, update `frontend/src/api.ts`, tests, and docs together.

Required row semantics:

```text
segment_change = <base_segment> -> <target_segment>
migration_priority = priority(base_segment, target_segment)
segment_changed = base_segment != target_segment
```

Rows included:

- without a target/result period selected, the report can behave as a single-period ABC table over the source/base period;
- with a target/result period selected, include customers with won revenue in either period, so lost and newly active customers are visible.

Required migration priority mapping:

| Transition | Priority |
|---|---|
| `A -> Нет продаж` | `срочно` |
| `A -> C` | `срочно` |
| `A -> B` | `важно` |
| `B -> Нет продаж` | `важно` |
| `B -> C` | `наблюдать` |
| `C -> Нет продаж` | `наблюдать` |
| `B -> A` | `развивать` |
| `C -> A` | `развивать` |
| `Нет продаж -> A` | `закрепить` |
| unchanged | `без изменений` |
| any other changed transition | `изменение` |

Do not let a loss of revenue become a growth priority.

### 2. Frontend ABC labels and table semantics

Update `frontend/src/App.tsx`, `frontend/src/api.ts`, and styles only as needed.

Required UI language:

- Rename period inputs to clearly express direction:
  - `Было с`
  - `Было по`
  - `Стало с`
  - `Стало по`
- Rename table/summary labels to avoid `current` / `compare` ambiguity:
  - `Выручка было`
  - `ABC было`
  - `Выручка стало`
  - `ABC стало`
  - `Переход`
  - `Приоритет`
- The transition displayed in the table must match `ABC было -> ABC стало`.
- `Только изменения` must filter by this corrected direction.
- Summary totals should be clear, for example `Выручка было` and `Выручка стало` when the result period is enabled.
- When result period is not enabled, the table should remain a normal single-period ABC report and should not show misleading transition columns.
- Keep separate `bitrix-sales.abc.v1` state. If persisted old values/sort fields become invalid after response field renaming, safely fall back to defaults.

### 3. Tests

Add or update backend tests so the bug cannot return.

Required test scenarios:

- customer was `A` in base period and has no won revenue in target period -> `A -> Нет продаж`, priority `срочно`;
- customer was `B` in base and has no won revenue in target -> `B -> Нет продаж`, priority `важно`;
- customer was `C` in base and has no won revenue in target -> `C -> Нет продаж`, priority `наблюдать`;
- customer had no won revenue in base and becomes `A` in target -> `Нет продаж -> A`, priority `закрепить`;
- customer moves `B/C -> A` -> priority `развивать`;
- unchanged rows stay `Без изменений` / `без изменений`;
- `changed_only` uses corrected direction;
- filters and sorting still apply after corrected row construction;
- API response does not expose forbidden personal fields.

Update existing tests that currently assume the old direction.

### 4. Documentation and report

Update docs so future work does not reintroduce the bug:

- `docs/development.md`;
- `docs/data-model.md`;
- `frontend/README.md`;
- `docs/project-status.md` if useful.

Update `.ai/report.md` with:

- root cause: direction was wrong/ambiguous;
- exact corrected direction;
- backend and frontend files changed;
- tests/checks run;
- confirmation no Bitrix calls/write methods were added.

## Out Of Scope

- Changing ABC thresholds or ABC classification algorithm itself.
- Adding charts.
- RFM/reactivation reports.
- CSV/export.
- Authentication.
- Bitrix ingestion, refresh, reconciliation, contact-deal link extraction, NBRB rate loading, or normalization rule changes.
- Live Bitrix diagnostics or external service calls from report endpoints.
- Region filter/columns in the frontend.
- Editing `ui-kits/`.
- Showing phone, email, address, messenger, comments, files, requisites, raw Bitrix rows, webhook values, or arbitrary custom fields.

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
- Keep all financial values in USD.
- Keep revenue semantics won-only.

## Acceptance Criteria

- ABC comparison direction is corrected to `Было -> Стало`.
- A customer with `A` in the source/base period and no won revenue in the target/result period displays `A -> Нет продаж` with priority `срочно`.
- A customer with no base revenue and target `A` displays `Нет продаж -> A` with priority `закрепить`.
- Loss transitions never appear as `развивать` or other growth priorities.
- Frontend labels make the direction clear: `Было` and `Стало`.
- Table columns show `Выручка было`, `ABC было`, `Выручка стало`, `ABC стало`, `Переход`, `Приоритет` when comparison is enabled.
- `Только изменения`, segment/priority filters, sorting, pagination, and totals use the corrected direction.
- Single-period ABC still works when the target/result period is not selected.
- Existing Contacts and Deals behavior is not regressed.
- Region filters/columns are not shown in ABC frontend.
- Backend tests cover the corrected transition matrix.
- Frontend build passes.
- No Bitrix calls or external service calls are added to report page loads.
- No Bitrix write methods are added.
- Documentation and `.ai/report.md` are updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-24 Fix ABC comparison direction
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
- ABC transition direction is corrected and covered by tests;
- `A -> Нет продаж` loss scenario is tested and passes;
- frontend wording no longer leaves direction ambiguous;
- no frontend region filters/columns are added;
- existing Contacts and Deals behavior remains intact;
- no frontend Bitrix calls are added;
- no backend report endpoint calls Bitrix, NBRB, or external services;
- no Bitrix write methods are added anywhere;
- required backend tests and frontend build are run, or inability is explicitly documented;
- `.ai/report.md` describes implementation, checks, facts, unknowns, and risks;
- staged files are only task files plus `.ai/report.md` and relevant docs/code/tests;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
