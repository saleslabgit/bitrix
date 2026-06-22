# Task: TASK-2026-06-22-04

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-03`

## Title

Build contacts frontend

## Goal

Create the first visible frontend milestone: a React/TypeScript/Vite app with one working report screen, `Contacts`, backed by the existing local backend API and styled according to the design-system assets in `ui-kits/`.

This task must keep scope intentionally narrow. Do not build dashboard, ABC, RFM, stale deals, concentration, or other report screens yet. The purpose is to prove the frontend foundation, API integration, design-system usage, table UX, filters, and local development flow on one useful report that can be expanded later.

## Product Scope

Build only this screen:

```text
Contacts: таблица контактов с поиском и фильтрами
```

The screen must support:

- contact list table;
- search;
- contact type filter;
- region filter;
- deal status filter where supported by the existing endpoint;
- pagination through `limit`/`offset`;
- loading state;
- error state;
- empty state;
- visible dataset/API status indicator if lightweight to add from existing endpoints.

Use existing backend endpoints only unless a tiny frontend-support fix is truly unavoidable:

- `GET /api/reports/contacts`;
- `GET /api/meta/filters`;
- optionally `GET /api/datasets/status` or `GET /api/datasets/profile` for a compact status badge.

Do not create a new backend report for this task.

## Required Table Columns

Use columns already returned by the existing contacts endpoint. Expected columns include:

- contact name;
- raw contact type if available;
- normalized contact type;
- region;
- total deals count;
- won deals count;
- open deals count;
- lost deals count;
- total amount original.

If the current response shape differs, follow the actual typed backend response and document the difference in `.ai/report.md`. Do not expose forbidden personal fields such as phone, email, address, messenger, comments, files, requisites, or arbitrary Bitrix fields.

## Frontend Architecture

Implement a minimal but real frontend app under `frontend/`:

- React;
- TypeScript;
- Vite;
- API client layer for backend calls;
- components split enough to remain maintainable, but no over-engineering;
- TanStack Query may be used if appropriate and available; if not used, explain why in `.ai/report.md`;
- table implementation can be plain React table for this first milestone or TanStack Table if the setup cost is reasonable.

Required npm scripts:

```text
dev
build
```

Add a test or validation script if practical. At minimum, `npm run build` must pass.

## Design System Requirement

Before building UI, inspect `ui-kits/` and follow its design tokens/specification/components as the source of truth.

Requirements:

- do not invent an unrelated visual style;
- use colors, typography, spacing, radius, controls, and layout direction from `ui-kits/` where available;
- if `ui-kits/` contains only static/exported design specs, translate them into CSS variables/components in the frontend;
- do not modify `ui-kits/` unless absolutely required to read/use assets; prefer leaving it untouched;
- document in `.ai/report.md` which `ui-kits/` files were inspected and what was used.

## Backend Boundary

Avoid backend changes. Existing backend is already ready for this first frontend screen.

Allowed only if strictly necessary:

- tiny CORS/dev-server config needed for local frontend-to-backend development;
- tiny response typing/doc correction if the existing API shape is inconsistent with code.

Forbidden:

- new Bitrix calls;
- Bitrix sync;
- Bitrix row listing;
- Bitrix write methods;
- new report endpoints;
- changing contact normalization/business rules;
- changing currency-rate logic.

## Documentation And Report

Update:

- `.ai/report.md` — implementation summary, inspected design-system files, endpoints used, checks run, known limitations;
- `docs/development.md` — how to install/run/build the frontend and expected backend URL/config;
- `docs/project-status.md` — first frontend screen is implemented, still intentionally limited to Contacts.

Update other docs only if needed.

## Out Of Scope

- Dashboard.
- ABC screen.
- RFM screen.
- Deal reconciliation screen.
- Stale deals screen.
- Deal cycle screen.
- Concentration screen.
- Type/region analytics screen.
- Authentication.
- Production deployment.
- CI.
- Scheduled sync or scheduled NBRB refresh.
- Any Bitrix API call.
- Any CRM write method.
- Modifying generated local data, DuckDB files, Parquet snapshots, CSV exports, `.env`, logs, caches, or `ui-kits/`.

## Acceptance Criteria

- `frontend/` contains a working React/TypeScript/Vite app.
- The app has one implemented screen: Contacts table with search, filters, pagination, loading, error, and empty states.
- The Contacts screen reads data from existing backend endpoints.
- The UI follows the `ui-kits/` design-system direction and reports what was used.
- No forbidden personal fields are displayed.
- No Bitrix calls are added or run.
- No generated data/secrets are staged.
- Frontend build passes.
- `.ai/report.md` and docs are updated.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-04 Build contacts frontend
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run frontend checks from `frontend/` after implementation:

```bash
npm install
npm run build
```

If a package manager lockfile is created, commit the relevant lockfile. Do not commit `node_modules`.

If tests or lint are added, run them and document exact commands.

Run backend tests only if backend code is changed.

Run from repository root if Docker is available:

```bash
docker compose config
```

Before committing:

```bash
git status --short --branch
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

If any required check cannot be run, document the exact reason in `.ai/report.md`.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- the latest relevant commit is this planner commit;
- `.ai/report.md` is updated;
- every required check is either run and reported, or explicitly documented as not run with reason;
- `.ai/report.md` explicitly states that no Bitrix calls were added or run;
- staged files are only files intentionally changed for `TASK-2026-06-22-04` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
