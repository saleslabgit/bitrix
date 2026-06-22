# Task: TASK-2026-06-22-31

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-30`

## Title

Prepare production deployment

## Goal

Prepare the project for a simple VPS deployment while preserving the existing local development flow.

The production setup should run the backend and a built frontend behind a reverse proxy with HTTPS-ready configuration. The current development `docker-compose.yml` must continue to work for local development with the Vite dev server.

## User Request

The user asked how to deploy the app quickly to a VPS, confirmed that local development must keep working, and then said:

```text
тогда сделай задачу на подготовку
```

## Facts

- The current default `docker-compose.yml` is a local development setup.
- Current `docker-compose.yml` starts:
  - `backend` from `backend/Dockerfile` on port `8000`;
  - `frontend` from `node:20-slim` running `npm ci && npm run dev -- --host 0.0.0.0` on port `5173`.
- There is no `frontend/Dockerfile` in the current repository.
- Frontend has `npm run build` and produces a Vite static build.
- Backend is FastAPI and is already containerized.
- Runtime data is stored under `APP_DATA_DIR`, normally `data/`, and mounted as `./data:/app/data` in dev compose.
- Auth is implemented and controlled by env variables:
  - `APP_AUTH_ENABLED`;
  - `APP_AUTH_USERNAME`;
  - `APP_AUTH_PASSWORD`;
  - `APP_AUTH_SESSION_SECRET`;
  - `APP_AUTH_SESSION_TTL_SECONDS`;
  - `APP_AUTH_COOKIE_SECURE`.
- For HTTPS deployment, `APP_AUTH_COOKIE_SECURE=true` should be supported by the deploy docs/config.
- Docker Compose must not auto-refresh Bitrix data. Data refresh remains a manual UI action.
- Bitrix webhook and auth credentials must stay in server-local `.env` or deployment secrets and must not be committed.
- `docs/project-status.md` still lists CI and production deployment as intentionally not done.

## Assumptions

- The first deployment target is a single VPS running Docker Compose.
- One public domain will point to the VPS.
- A simple reverse proxy container is acceptable. Prefer Caddy for the first production deployment because it can manage Let's Encrypt certificates automatically with less configuration than manual Nginx/certbot.
- Backend and frontend should be private inside the Docker network in production; only the reverse proxy should publish public ports.
- The production compose file can be a separate file, for example `docker-compose.prod.yml`, so local development remains unchanged.

## Unknowns

- Final domain name.
- VPS provider and OS image.
- Backup destination and retention policy.
- Whether production will later need CI/CD or manual SSH deploy is enough for the first release.

Do not block this task on those unknowns. Use placeholders and document what the operator must fill in on the VPS.

## Scope

### 1. Preserve local development

Keep the current local development flow intact:

```bash
docker compose up --build
```

The existing dev compose may be left as-is unless a tiny non-breaking improvement is required. Do not replace the Vite dev server in the default dev compose.

### 2. Add production frontend image

Add a production frontend container build.

Requirements:

- Build frontend dependencies with Node.
- Run `npm run build`.
- Serve the built `dist` static files from a lightweight HTTP server image.
- The static server must support SPA fallback to `index.html`.
- The static server must proxy `/api/*` and `/health` to the backend service inside the Docker network, or the reverse proxy must do this clearly and safely.
- Do not commit `frontend/dist`.

Recommended implementation options:

- `frontend/Dockerfile` multi-stage build using `node:20-slim` for build and `nginx:alpine` for serving static files.
- Add an nginx config under `frontend/` or deploy config directory that serves static files and proxies API calls to `backend:8000`.

Alternative acceptable implementation:

- Caddy serves static frontend build and reverse proxies API if the structure stays simple and verified.

### 3. Add production compose

Add `docker-compose.prod.yml`.

Requirements:

- Services should include backend, production frontend/static server, and reverse proxy if needed.
- Only public HTTP/HTTPS ports should be exposed from the production stack, normally `80:80` and `443:443`.
- Backend must not publish `8000` publicly in production.
- Frontend/internal static server should not publish its dev port publicly in production unless it is the reverse proxy itself.
- Backend data must persist via a bind mount or named volume. Prefer preserving the current operator-visible `./data:/app/data` mount for simplicity.
- Add restart policies suitable for VPS use, for example `restart: unless-stopped`.
- Compose must load `.env.example` plus optional `.env`, same as dev, without committing real values.
- Compose startup must not call Bitrix or refresh local data.

### 4. Add reverse proxy / HTTPS-ready config

Add the simplest production reverse proxy configuration.

Preferred Caddy approach:

- Add a `Caddyfile` or deploy Caddy config with a placeholder domain.
- Reverse proxy app traffic to the production frontend/static service.
- Ensure `/api/*` and `/health` reach the backend, either via frontend nginx proxy or directly in Caddy.
- Use an environment variable or documented placeholder for the domain where practical.
- Persist Caddy data/certs with volumes if Caddy is used.

If using Nginx instead:

- Include clear HTTPS/certbot notes or keep it HTTP-only behind an external TLS proxy, but document the tradeoff.

### 5. Add production environment template

Add a safe production env template, for example `.env.production.example` or `deploy/.env.production.example`.

Requirements:

- Include placeholders only.
- Include auth variables with `APP_AUTH_ENABLED=true` and `APP_AUTH_COOKIE_SECURE=true` as production guidance.
- Include `BITRIX_WEBHOOK_URL=` placeholder only, never a real URL.
- Include `BITRIX_CONTACT_TYPE_FIELD=` placeholder.
- Include `APP_DATA_DIR=data`.
- Do not create or commit a real `.env`.

### 6. Add deploy documentation

Update docs so the user can deploy manually to a VPS.

Required docs:

- `docs/development.md` or a new `docs/deployment.md` if clearer.
- `docs/project-status.md`.
- `frontend/README.md` and/or `backend/README.md` only if relevant to explain production behavior.

The deploy docs must include:

- VPS prerequisites: Docker, Docker Compose plugin, Git, domain DNS A record.
- Clone/update commands.
- How to create the server-local `.env` from the production example.
- How to generate a strong `APP_AUTH_SESSION_SECRET`.
- How to start production:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

- How to check status/logs:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

- How to verify health and app URL.
- How to update after new commits:

```bash
git pull
docker compose -f docker-compose.prod.yml up --build -d
```

- How to stop production safely.
- How to back up and restore at least the `data/` directory at a high level.
- State clearly that Bitrix refresh remains manual through the UI after login.
- State clearly that local dev still uses `docker compose up --build`.

## Out Of Scope

- CI/CD pipeline.
- GitHub Actions deployment.
- Cloud-managed database.
- Kubernetes.
- Multi-server deployment.
- Complex secret managers.
- Automated scheduled Bitrix refresh.
- New product features or reports.
- Changing analytics logic.
- Changing auth semantics beyond production env guidance.
- Implementing full backup automation with retention unless it is trivial and well isolated.

## Constraints

- Work only from current GitHub repository files.
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
- Backend/frontend production API calls should remain same-origin from the browser, so HttpOnly auth cookies work cleanly.

## Acceptance Criteria

### Local development

- `docker compose up --build` remains the local dev command.
- Local dev frontend still runs with Vite dev server and existing operator flow.
- Existing local auth-disabled default remains possible with `.env.example`.

### Production compose

- A separate production compose file exists and builds/runs the stack for VPS deployment.
- Backend is not publicly exposed in production compose.
- Only reverse proxy/public web ports are exposed in production compose.
- Production stack serves built frontend static files, not Vite dev server.
- `/api/*` and `/health` are routed to backend successfully in production topology.
- Production data persists under the configured data mount/volume.
- Production compose does not call Bitrix on startup.

### HTTPS/auth readiness

- Reverse proxy configuration is HTTPS-ready with clear domain placeholder/instructions.
- Production env example enables auth and secure cookies by default as guidance, using placeholders only.
- Same-origin browser access is preserved so the existing HttpOnly cookie auth works.

### Documentation

- Deployment docs are sufficient for a manual VPS deploy by the user.
- Docs explain local dev vs production commands.
- Docs explain server-local secrets and `.env` handling.
- Docs include backup guidance for `data/`.
- `docs/project-status.md` is updated to reflect that production deployment preparation exists, while actual deployment host and backup destination remain unknown.

### Safety

- No secrets or forbidden artifacts are committed.
- No `frontend/dist`, local DB, raw data, generated data, logs, caches, or `node_modules` are committed.
- No Bitrix write methods are added.
- `.ai/report.md` is updated.

## Checks

Required before implementation:

```bash
git log --oneline -5
git status --short
```

Suggested implementation checks:

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
curl -f http://localhost/health
curl -f http://localhost/
docker compose -f docker-compose.prod.yml down
```

If the production proxy requires a real domain for HTTPS, test HTTP/local routing as far as practical and document the limitation in `.ai/report.md`.

Backend tests if backend code is changed:

```bash
cd backend && python -m pytest
```

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src
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
- runtime smoke is recorded or a concrete limitation is documented;
- no Bitrix write methods were added.

Commit message:

```text
codex: TASK-2026-06-22-31 Prepare production deployment
```