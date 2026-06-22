# Task: TASK-2026-06-22-05

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-04`

## Title

Run full stack with Compose

## Goal

Make local testing convenient for the user by allowing backend and frontend to run together with one command:

```bash
docker compose up --build
```

After this task, the user should be able to open the frontend in a browser and test the Contacts screen against the local backend without manually starting two separate processes.

## Scope

### 1. Add Frontend To Docker Compose

Update `docker-compose.yml` so it starts both services:

- `backend` on `http://localhost:8000`;
- `frontend` on `http://localhost:5173` or another documented port if `5173` is unavailable.

The frontend service must:

- run the existing Vite dev server;
- bind to `0.0.0.0` so it is reachable from the host;
- proxy `/api` and `/health` to the backend service inside Compose;
- use Compose service networking, expected backend target `http://backend:8000`;
- avoid committing `node_modules`, `dist`, caches, or generated build artifacts.

Acceptable implementation options:

- add a small `frontend/Dockerfile` for development; or
- use an official Node image directly in Compose if that is cleaner and documented.

Prefer the simplest maintainable approach that fits the existing repo.

### 2. Keep Existing Manual Frontend Flow Working

Do not break the current manual flow:

```bash
cd frontend
npm install
npm run dev
```

The Vite proxy should still default to `http://localhost:8000` outside Compose, while Compose can override `VITE_BACKEND_URL=http://backend:8000`.

### 3. Documentation

Update:

- `docs/development.md` — one-command full-stack launch and URLs;
- `frontend/README.md` — Compose launch plus manual launch;
- `.ai/report.md` — changed files, checks, exact commands, known limitations.

Include a short user-facing verification checklist in docs or report:

- backend health is reachable;
- frontend opens;
- Contacts table loads;
- filters/search/pagination work;
- if frontend shows API error, check backend dataset/status.

### 4. Checks

Run and document:

```bash
docker compose config
```

If Docker is available, also run the strongest practical check without leaving long-running services behind, for example:

```bash
docker compose build
```

or a bounded startup/health check. Stop services afterward if they are started.

Run frontend build from `frontend/`:

```bash
npm run build
```

Run backend tests only if backend code changes.

## Out Of Scope

- Changing backend business logic.
- Changing frontend report behavior beyond wiring needed for Compose.
- New screens.
- New backend endpoints.
- Bitrix calls.
- Bitrix sync.
- Bitrix write methods.
- Production deployment.
- Nginx/HTTPS.
- CI.
- Authentication.

## Acceptance Criteria

- `docker compose up --build` starts backend and frontend together.
- Frontend is reachable from the host at a documented URL.
- Frontend API requests work through the Vite proxy to the backend Compose service.
- Existing manual frontend dev flow still works.
- `docker compose config` passes, or inability to run Docker is documented with exact reason.
- `npm run build` passes from `frontend/`.
- Docs and `.ai/report.md` include clear launch instructions.
- No generated artifacts, secrets, `.env`, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, or `frontend/dist` are staged.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-05 Run full stack with Compose
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
cd frontend
npm run build
```

If dependencies need installing locally, use the existing `package-lock.json` and document the exact command.

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
- staged files are only files intentionally changed for `TASK-2026-06-22-05` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
