# Task: TASK-2026-06-22-31

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-30`

## Title

Prepare FASTVPS Docker deployment

## Goal

Prepare the project for the fastest practical deployment path on a normal VPS where FASTVPS provides a hosting panel, HTTPS/domain management, and Docker is already available.

The project must provide a production Docker Compose setup that runs the app behind the hosting panel reverse proxy. The app itself should not manage public HTTPS certificates with Caddy/certbot in this task. The FASTVPS panel or provider-level reverse proxy will terminate HTTPS and forward traffic to a local published app port.

Local development must remain unchanged:

```bash
docker compose up --build
```

## User Request

The user first considered a very weak VPS and a no-Docker path, then clarified that FASTVPS can provide a panel with site/HTTPS management and Docker already installed. The user asked to make the task:

```text
Если я буду использовать FASTVPS, там есть уже своя панель, я могу там создать сайт и подключить https и там уже будет установлен докер

Делай задачу
```

This task supersedes the previous no-Docker weak-VPS version of `TASK-2026-06-22-31`.

## Facts

- Current default `docker-compose.yml` is a local development setup and must remain usable for local development.
- Current dev compose starts:
  - `backend` from `backend/Dockerfile` on public local port `8000`;
  - `frontend` from `node:20-slim` running Vite dev server on public local port `5173`.
- Frontend has `npm run build` and produces a Vite static build.
- There is currently no production frontend Dockerfile in the repository.
- Backend is FastAPI and is already containerized.
- Runtime data is stored under `APP_DATA_DIR`, normally `data/`, and dev compose mounts `./data:/app/data`.
- Auth is already implemented through env variables:
  - `APP_AUTH_ENABLED`;
  - `APP_AUTH_USERNAME`;
  - `APP_AUTH_PASSWORD`;
  - `APP_AUTH_SESSION_SECRET`;
  - `APP_AUTH_SESSION_TTL_SECONDS`;
  - `APP_AUTH_COOKIE_SECURE`.
- Production should use `APP_AUTH_ENABLED=true` and a strong `APP_AUTH_SESSION_SECRET`.
- With HTTPS terminated by FASTVPS/panel, production should use `APP_AUTH_COOKIE_SECURE=true` for browser-facing HTTPS.
- Docker Compose must not auto-refresh Bitrix data.
- Bitrix refresh remains a manual UI action after login.
- Bitrix webhook and auth credentials must stay in server-local `.env` and must not be committed.
- `docs/project-status.md` currently lists CI and production deployment as intentionally not done.

## Assumptions

- FASTVPS provides Docker and a hosting panel that can create a site, enable HTTPS, and reverse proxy to a local port on the VPS.
- The production stack can publish one local app port on the host, for example `127.0.0.1:8080:80`.
- The backend should remain private inside the Docker network and must not publish port `8000` publicly in production.
- The frontend should be built inside the frontend production image, because a normal VPS with Docker is now the target.
- HTTPS certificates are handled by the hosting panel, not by a project-owned Caddy/certbot service.
- The final domain name is unknown and should be documented as a placeholder.

## Unknowns

- Exact FASTVPS panel UI and names of its proxy fields.
- Final domain name.
- Whether FASTVPS proxy can target `127.0.0.1:8080` directly or requires a specific local/public port format.
- Backup destination and retention policy.
- Whether the first deployment will transfer an existing `data/` directory or refresh from Bitrix on the server.

Do not block this task on those unknowns. Use placeholders and document what the operator must fill in in the FASTVPS panel.

## Scope

### 1. Preserve local development

Keep the existing local development flow intact:

```bash
docker compose up --build
```

Do not replace the Vite dev server in the default dev compose.

### 2. Add production frontend container

Add a production frontend build/serve setup.

Requirements:

- Add a frontend production Dockerfile, for example `frontend/Dockerfile`.
- Build frontend dependencies with Node.
- Run `npm run build`.
- Serve built `dist` static files from a lightweight HTTP server image, preferably nginx alpine.
- Support SPA fallback to `index.html`.
- Proxy `/api/*` and `/health` to the backend service inside the Docker network, or document and implement equivalent routing through the production web container.
- Do not commit `frontend/dist`.

### 3. Add production Docker Compose for hosting panel reverse proxy

Add `docker-compose.prod.yml`.

Requirements:

- Include backend and production frontend/web services.
- Optionally include only those two services; do not add Caddy/certbot unless strictly necessary.
- Publish only the frontend/web service to the host, preferably bound to localhost:

```yaml
ports:
  - "127.0.0.1:8080:80"
```

- Backend must not publish `8000` in production.
- Backend must be reachable by the frontend/web service over the Docker network, for example `http://backend:8000`.
- Backend data must persist, preferably preserving the operator-visible bind mount:

```text
./data:/app/data
```

- Add `restart: unless-stopped` where appropriate.
- Load `.env.example` plus optional `.env`, same as dev, without committing real values.
- Compose startup must not call Bitrix or refresh local data.

### 4. Add production environment example

Add a safe production env template, for example `.env.production.example` or `deploy/fastvps/.env.production.example`.

Requirements:

- Placeholders only.
- Include auth variables with production guidance:
  - `APP_AUTH_ENABLED=true`;
  - `APP_AUTH_USERNAME=`;
  - `APP_AUTH_PASSWORD=`;
  - `APP_AUTH_SESSION_SECRET=`;
  - `APP_AUTH_COOKIE_SECURE=true`.
- Include `BITRIX_WEBHOOK_URL=` placeholder only, never a real URL.
- Include `BITRIX_CONTACT_TYPE_FIELD=` placeholder.
- Include `BITRIX_PAGE_SIZE=50`.
- Include `APP_DATA_DIR=data` unless code requires another value.
- Do not create or commit a real `.env`.

### 5. Add FASTVPS deployment documentation

Add or update deployment docs. Prefer a dedicated `docs/deployment.md` and link from `docs/development.md`.

Required docs:

- Explain that local development still uses:

```bash
docker compose up --build
```

- Explain that FASTVPS production uses:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

- Explain expected FASTVPS panel setup at a high level:
  - create site/domain in the panel;
  - enable HTTPS in the panel;
  - configure reverse proxy to the local app port, for example `http://127.0.0.1:8080`;
  - ensure the browser accesses the app through the HTTPS domain.
- Include server steps:
  - clone/update repository;
  - create `.env` from the production example;
  - generate a strong `APP_AUTH_SESSION_SECRET`;
  - start/restart/stop production compose;
  - check status/logs;
  - verify health and app URL.
- Include update flow after new commits:

```bash
git pull
docker compose -f docker-compose.prod.yml up --build -d
```

- Include backup/restore guidance for `data/`.
- State clearly that Bitrix refresh remains manual through the UI after login.
- State clearly that Docker Compose startup must not call Bitrix automatically.
- Mention that if the FASTVPS panel cannot proxy to `127.0.0.1:8080`, the operator may need to adjust the published host binding/port according to the panel requirements.

### 6. Update project status

Update `docs/project-status.md` to reflect:

- FASTVPS/Docker deployment preparation exists after this task;
- actual server deployment, final domain, panel configuration, and backup destination remain operator steps;
- no-Docker weak VPS deployment is not the primary path for the current decision.

## Out Of Scope

- Actually SSHing into FASTVPS.
- Configuring the FASTVPS panel from Codex.
- CI/CD pipeline.
- GitHub Actions deployment.
- Project-owned Caddy/certbot HTTPS automation.
- Kubernetes.
- Managed database.
- Complex secret managers.
- Automated scheduled Bitrix refresh.
- New product features or reports.
- Changing analytics logic.
- Changing auth semantics beyond deployment env guidance.
- Full backup automation with retention.

## Constraints

- Work only from current repository files.
- Preserve default local development behavior.
- Keep Bitrix read-only.
- Do not add CRM write methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit real `.env`, credentials, webhook URLs, auth passwords, session secrets, DuckDB files, Parquet, CSV, raw data, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Do not change `ui-kits/`.
- Docker Compose must not automatically refresh data from Bitrix.
- Production browser access must remain same-origin through the panel/frontend web container so HttpOnly auth cookies work cleanly.
- Backend must not be publicly exposed in production compose.

## Acceptance Criteria

### Local development

- `docker compose up --build` remains the local dev command.
- Local dev frontend still runs with Vite dev server and existing operator flow.
- Existing local auth-disabled default remains possible with `.env.example`.

### Production compose

- A separate production compose file exists.
- Production stack builds/runs backend plus built frontend/static web service.
- Backend is not publicly exposed in production compose.
- Only one frontend/web port is published for the hosting panel reverse proxy, preferably `127.0.0.1:8080:80`.
- Production stack serves built frontend static files, not Vite dev server.
- `/api/*` and `/health` route to backend successfully in the production topology.
- Production data persists under the configured `data/` mount/volume.
- Production compose does not call Bitrix on startup.

### FASTVPS/panel readiness

- Docs clearly describe how the FASTVPS panel should proxy HTTPS domain traffic to the local app port.
- The project does not add Caddy/certbot as the primary HTTPS path.
- Production env example enables auth and secure cookies by default as guidance, using placeholders only.
- Same-origin browser access is preserved for existing HttpOnly cookie auth.

### Documentation

- Deployment docs are sufficient for a manual FASTVPS deploy by the user.
- Docs explain local dev vs production commands.
- Docs explain server-local secrets and `.env` handling.
- Docs include backup guidance for `data/`.
- `docs/project-status.md` is updated.
- `.ai/report.md` is updated by Codex.

### Safety

- No secrets or forbidden artifacts are committed.
- No `frontend/dist`, local DB, raw data, generated data, logs, caches, or `node_modules` are committed.
- No Bitrix write methods are added.

## Checks

Required before implementation:

```bash
git log --oneline -5
git status --short
```

Compose checks:

```bash
docker compose config
docker compose -f docker-compose.prod.yml config
```

Frontend build:

```bash
cd frontend && npm run build
```

Production runtime smoke if Docker is available:

```bash
docker compose -f docker-compose.prod.yml up --build -d
curl -f http://127.0.0.1:8080/health
curl -f http://127.0.0.1:8080/
docker compose -f docker-compose.prod.yml down
```

Backend tests if backend code is changed:

```bash
cd backend && python -m pytest
```

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
- default dev compose still exists and remains the local command;
- production compose config validates;
- frontend build is recorded;
- production smoke is recorded or a concrete limitation is documented;
- backend is not publicly exposed in production compose;
- no project-owned HTTPS/certbot/Caddy path is introduced unless explicitly justified as non-primary;
- no Bitrix write methods were added.

Commit message:

```text
codex: TASK-2026-06-22-31 Prepare FASTVPS Docker deployment
```