# Task: TASK-2026-06-22-31

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-30`

## Title

Prepare lean no-Docker VPS deployment

## Goal

Prepare the project for deployment on a very small test VPS:

```text
1 vCPU
1 GB RAM
5 GB SSD
```

The deployment path must avoid Docker on the VPS and must avoid building the frontend on the VPS. The server should run only the Python backend, serve prebuilt frontend static files, reverse proxy `/api/*` and `/health`, persist `data/`, and keep local development behavior unchanged.

## User Request

The user first asked for production deployment preparation, then found that Docker is not practical on the available Mac/server path. The current target is now the weak VPS above, and the user said:

```text
Короче мак не вывезет, нужно делать деплой на слабый сервер, что я указал
```

This task supersedes the previous Docker-production plan in the current `TASK-2026-06-22-31` file. Do not implement the old Docker production compose/Caddy plan unless it is needed only as optional documentation.

## Facts

- Current default `docker-compose.yml` is a local development setup and must remain usable for local development.
- Current dev compose starts:
  - backend from `backend/Dockerfile` on port `8000`;
  - frontend from `node:20-slim` running Vite dev server on port `5173`.
- Frontend has `npm run build` and produces a Vite static build.
- Backend is FastAPI and can run with `uvicorn app.main:app`.
- Backend settings read `.env` from the repository root when run from the `backend/` directory, via `env_file="../.env"`.
- Runtime data is stored under `APP_DATA_DIR`, normally `data/`.
- Auth is already implemented through env variables:
  - `APP_AUTH_ENABLED`;
  - `APP_AUTH_USERNAME`;
  - `APP_AUTH_PASSWORD`;
  - `APP_AUTH_SESSION_SECRET`;
  - `APP_AUTH_SESSION_TTL_SECONDS`;
  - `APP_AUTH_COOKIE_SECURE`.
- Production should use `APP_AUTH_ENABLED=true` and a strong `APP_AUTH_SESSION_SECRET`.
- With HTTPS, production should use `APP_AUTH_COOKIE_SECURE=true`.
- Docker Compose must not auto-refresh Bitrix data. In no-Docker deployment, service startup must also not auto-refresh Bitrix data.
- Bitrix refresh remains a manual UI action after login.
- Bitrix webhook and auth credentials must stay in server-local `.env` and must not be committed.
- `docs/project-status.md` currently lists CI and production deployment as intentionally not done.

## Assumptions

- The VPS OS is a common Ubuntu/Debian server with `systemd`, `apt`, and `nginx` available.
- The frontend can be built on another machine or CI-like environment and uploaded as a tarball/artifact to the VPS.
- The VPS can install Python 3.12, `python3.12-venv`, nginx, git, and unzip/tar tooling.
- Node.js and npm should not be required on the VPS.
- Docker should not be required on the VPS.
- HTTPS may be added later or via the VPS/provider/reverse proxy. The first target can document HTTP test deployment plus HTTPS settings needed for secure cookies.

## Unknowns

- Exact VPS OS/version.
- Final domain name.
- Whether HTTPS will be terminated by nginx/certbot, provider proxy, or another external proxy.
- Backup destination and retention policy.
- Whether the user will upload a pre-existing `data/` directory or refresh from Bitrix on the VPS.

Do not block the task on these unknowns. Use placeholders and document operator steps clearly.

## Scope

### 1. Preserve local development

Keep the existing local development behavior intact:

```bash
docker compose up --build
```

Do not remove or replace the dev Docker Compose flow. Do not change the current local Vite dev flow unless a small documentation clarification is needed.

### 2. Add no-Docker deployment assets

Add lightweight deployment templates under a clear path such as `deploy/no-docker/`.

Required assets:

- systemd service template for backend, for example `bitrix-sales-backend.service`.
- nginx site config template that:
  - serves frontend static files from a deploy directory;
  - reverse proxies `/api/` to `127.0.0.1:8000`;
  - reverse proxies `/health` to `127.0.0.1:8000`;
  - falls back to `index.html` for SPA routes;
  - does not expose backend directly.
- safe production env example for no-Docker deployment, for example `.env.production.example` or `deploy/no-docker/.env.production.example`.
- optional helper scripts only if they stay simple and safe. Prefer docs/templates over complex automation.

### 3. Support prebuilt frontend artifact workflow

Document and, if useful, add a small helper script for building the frontend outside the VPS.

Requirements:

- Build command remains:

```bash
cd frontend && npm ci && npm run build
```

- `frontend/dist` must not be committed.
- The docs must explain how to package and upload the built frontend to the VPS, for example as `frontend-dist.tar.gz`.
- The server-side nginx config should serve from a stable directory, for example:

```text
/opt/bitrix-sales/frontend-dist
```

- The server must not require Node.js/npm for normal operation.

### 4. Backend no-Docker runtime

Document backend setup on the VPS:

- project directory, for example `/opt/bitrix-sales/app`;
- server-local `.env` in the project root;
- persistent data directory, for example `/opt/bitrix-sales/app/data`;
- Python venv under the backend directory or deploy directory;
- install backend dependencies with:

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
pip install -e .
```

- systemd starts backend with uvicorn bound only to localhost:

```text
127.0.0.1:8000
```

- service restart policy should be suitable for a small VPS.

### 5. Add weak-server operator documentation

Add or update deployment docs. Prefer a dedicated `docs/deployment.md` and link from `docs/development.md`.

Docs must include:

- why this no-Docker path is used for the 1 GB RAM / 5 GB SSD test server;
- expected limitations of that server size;
- recommended free-space and RAM checks;
- creating swap, for example 1-2 GB, with clear caution that disk is only 5 GB;
- installing minimal OS packages;
- cloning/updating the repository;
- creating server-local `.env` from the production example;
- generating `APP_AUTH_SESSION_SECRET`;
- frontend build outside the server and upload/install on server;
- backend venv setup;
- installing systemd service;
- installing nginx config;
- start/restart/status/log commands;
- health/app verification commands;
- update flow after new commits;
- backup/restore guidance for `data/`;
- clear statement that Bitrix refresh is manual through UI after login;
- clear statement that local dev still uses `docker compose up --build`.

### 6. Update project status

Update `docs/project-status.md` to reflect:

- no-Docker weak VPS deployment preparation exists after this task;
- actual server deployment, domain, HTTPS, and backup destination remain external/operator steps unless completed outside the repo;
- Docker production deployment is not the primary path for the current weak test VPS.

## Out Of Scope

- Actually SSHing into the VPS.
- Installing packages on the VPS from Codex.
- Committing real `.env`, credentials, webhook URLs, auth passwords, or session secrets.
- Committing local DB/data, raw Bitrix exports, Parquet, CSV, logs, caches, `node_modules`, or `frontend/dist`.
- CI/CD pipeline.
- GitHub Actions deployment.
- Docker production compose as the primary solution for this task.
- Kubernetes, managed database, cloud object storage, complex secret managers.
- Automated scheduled Bitrix refresh.
- Changing analytics logic.
- Changing frontend report behavior.
- Changing auth semantics beyond deployment env guidance.
- Full backup automation with retention.

## Constraints

- Work from current repository files.
- Preserve default local development behavior.
- Keep Bitrix read-only.
- Do not add CRM write methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit secrets, real `.env`, webhook URLs, credentials, DuckDB files, Parquet, CSV, raw data, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Do not change `ui-kits/`.
- Service startup must not refresh Bitrix data.
- Browser access should remain same-origin through nginx so HttpOnly auth cookies work cleanly.
- Backend must bind to localhost in no-Docker production; nginx is the public entry point.

## Acceptance Criteria

### Local development

- Existing local dev command remains documented and valid:

```bash
docker compose up --build
```

- No-Docker deployment docs do not remove or weaken the local dev instructions.

### No-Docker deployment assets

- A systemd backend service template exists.
- An nginx site config template exists.
- A safe production env example exists with placeholders only.
- The templates are consistent with the actual backend command and frontend build output.
- Backend is not documented or configured as publicly exposed directly.
- Frontend is served as static files, not Vite dev server.
- `/api/*` and `/health` are routed to backend through nginx.
- SPA fallback to `index.html` is configured.

### Weak-server fit

- Docs explicitly avoid Docker and frontend build on the VPS.
- Docs explain how to build frontend elsewhere and upload the artifact.
- Docs include disk/RAM caveats for 1 GB RAM / 5 GB SSD.
- Docs include a minimal swap recommendation and warn about limited disk.

### Security and operations

- Production env guidance enables auth and uses secure-cookie guidance for HTTPS.
- Secrets are placeholders only.
- Bitrix refresh remains manual through UI.
- Data persistence and backup focus on `data/`.
- No Bitrix write methods are added.

### Documentation

- `docs/deployment.md` or equivalent contains enough steps for a manual no-Docker VPS deploy.
- `docs/development.md` links to the deployment guide and preserves local setup.
- `docs/project-status.md` is updated.
- `.ai/report.md` is updated by Codex.

## Checks

Required before implementation:

```bash
git log --oneline -5
git status --short
```

Frontend build, because deployment docs depend on the static artifact:

```bash
cd frontend && npm run build
```

Backend tests only if backend code changes:

```bash
cd backend && python -m pytest
```

Config/template sanity checks as applicable:

```bash
nginx -t -c <temporary test config path>
```

If nginx is not installed in the execution environment, document that limitation in `.ai/report.md` and at least review the config syntax manually.

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src deploy docs
```

Secret/artifact check before commit:

```bash
git status --short
```

## Hard Workflow Gate

Before committing, verify:

- only task-related files are staged;
- `.ai/report.md` is updated;
- no real credentials or secrets are staged;
- no `.env`, local DB, raw/generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes are staged;
- local dev Docker Compose remains present and unchanged unless documented as a tiny non-breaking clarification;
- no-Docker deployment is the primary documented path for the weak VPS;
- frontend build result is recorded, but `frontend/dist` is not committed;
- nginx/systemd templates are consistent with actual project paths and commands;
- no Bitrix write methods were added.

Commit message:

```text
codex: TASK-2026-06-22-31 Prepare lean VPS deployment
```