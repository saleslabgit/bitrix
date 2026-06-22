# Task: TASK-2026-06-22-06

Status: planned
Created from: current `main` after user reported frontend Compose runtime error

## Title

Fix Compose ui-kits mount

## Problem

When running the full stack through Docker Compose, the frontend Vite dev server fails with:

```text
[plugin:vite:css] [postcss] ENOENT: no such file or directory, open '../../ui-kits/styles.css'
/app/src/styles.css
```

Root cause: the frontend container mounts only `./frontend` to `/app`, while `frontend/src/styles.css` imports `../../ui-kits/styles.css`. Inside the container, that relative path resolves outside `/app` to `/ui-kits/styles.css`, but `ui-kits/` is not mounted there.

## Goal

Fix the full-stack Compose startup so this command works and the Contacts screen opens:

```bash
docker compose up --build
```

The fix must keep the manual frontend flow working:

```bash
cd frontend
npm install
npm run dev
```

## Scope

### 1. Fix design-system asset availability in Compose

Implement the smallest maintainable fix. Expected solution:

- mount repository `./ui-kits` into the frontend container at the path expected by the existing import, likely `/ui-kits:ro`.

Alternative solutions are acceptable only if they preserve both:

- Compose launch;
- manual local frontend launch.

Do not copy or duplicate the `ui-kits/` files into `frontend/`.

### 2. Verify frontend startup, not just build

`npm run build` alone is insufficient because the reported failure happens in Vite dev server under Compose.

Run and document checks that prove the browser-visible dev server no longer shows the Vite CSS ENOENT overlay:

```bash
docker compose config
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
curl -f http://localhost:5173/health
curl -f http://localhost:5173/api/datasets/status
```

Also inspect frontend container logs for absence of the `ui-kits/styles.css` ENOENT error.

Stop services afterward:

```bash
docker compose down -v
```

If Docker cannot be run in the environment, document the exact reason in `.ai/report.md` and still make the config fix.

### 3. Documentation and report

Update:

- `.ai/report.md` — root cause, changed files, exact checks, and user verification command;
- `docs/development.md` and/or `frontend/README.md` only if the launch instructions or Compose behavior materially change.

## Out Of Scope

- New screens.
- Frontend redesign.
- Backend API changes.
- Bitrix calls.
- Bitrix sync.
- Bitrix write methods.
- Production Docker/Nginx/HTTPS.
- CI.
- Authentication.

## Acceptance Criteria

- Compose frontend container can read `ui-kits/styles.css`.
- `docker compose up --build` starts backend and frontend without the Vite CSS ENOENT overlay.
- `http://localhost:5173` returns the frontend page.
- Proxy checks for `/health` and `/api/datasets/status` still work through frontend/Vite.
- Manual local frontend flow remains valid.
- No `ui-kits/` files are modified or staged.
- No generated artifacts, secrets, `.env`, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, or `frontend/dist` are staged.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-06 Fix Compose ui-kits mount
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run after implementation:

```bash
docker compose config
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
curl -f http://localhost:5173/health
curl -f http://localhost:5173/api/datasets/status
docker compose logs frontend
docker compose down -v
```

Run frontend build if frontend files beyond Compose/docs are changed:

```bash
cd frontend
npm run build
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
- staged files are only files intentionally changed for `TASK-2026-06-22-06` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
