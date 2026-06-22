# Отчет: TASK-2026-06-22-05

Статус: done

## Кратко

Добавлен full-stack local Compose запуск:

```bash
docker compose up --build
```

Теперь Compose поднимает:

- `backend` на `http://localhost:8000`;
- `frontend` на `http://localhost:5173`.

Frontend service использует официальный `node:20-slim`, запускает существующий Vite dev server на `0.0.0.0:5173`, проксирует `/api` и `/health` на `http://backend:8000` через Compose service networking и не пишет `node_modules` в рабочее дерево благодаря anonymous volume `/app/node_modules`.

Backend business logic и frontend report behavior не менялись.

## Измененные файлы

- `docker-compose.yml` — добавлен `frontend` service, `VITE_BACKEND_URL=http://backend:8000`, port `5173:5173`, bind mount `./frontend:/app`, anonymous `/app/node_modules`, `depends_on: backend`.
- `frontend/vite.config.ts` — Compose/runtime `process.env.VITE_BACKEND_URL` теперь имеет приоритет над default `http://localhost:8000`.
- `docs/development.md` — описан one-command full-stack запуск, URLs, Compose proxy и verification checklist.
- `frontend/README.md` — добавлен Compose запуск, ручной frontend flow и verification checklist.
- `.ai/report.md` — this report.

`.ai/task.md` остается pre-existing unstaged planner change and was not staged by Codex. `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, `ui-kits/`, and Docker volumes/images were not staged.

## User Verification Checklist

- Open `http://localhost:8000/health` and confirm backend health responds.
- Open `http://localhost:5173` and confirm the frontend loads.
- Confirm the Contacts table loads.
- Confirm search, filters, and pagination work.
- If the frontend shows an API error, check `http://localhost:8000/api/datasets/status` and confirm an active dataset is available.

## Architecture Notes

- No `frontend/Dockerfile` was added. The Compose service uses the official Node image directly because this is the smallest maintainable development setup.
- The manual frontend flow still defaults to `http://localhost:8000`:

```bash
cd frontend
npm install
npm run dev
```

- Compose overrides only the proxy target:

```text
VITE_BACKEND_URL=http://backend:8000
```

- `docker compose config` reads local `.env` when present. The command passed, but no local secret/env values are copied into this report.

## Bitrix Calls

Bitrix methods called in this task:

```text
none
```

No Bitrix sync was run. No Bitrix row-listing methods were called. No Bitrix write methods were called.

## Запущенные проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit was `b45ecfd planner: TASK-2026-06-22-05 Run full stack with Compose`.
- `git status --short --branch` — passed. Showed only pre-existing modified `.ai/task.md`.

Documentation/library checks:

- Context7 docs queried for Docker Compose service configuration.

Implementation checks:

- `npm run build` from `frontend/` — passed:
  - `tsc -b`;
  - `vite build`.
- `docker compose config` from repository root — passed.
- `docker compose build` from repository root — passed. Built the backend image.
- `docker compose up --build -d` from repository root — passed. Started backend and frontend containers.
- Host HTTP checks with escalated network access — passed:
  - `curl http://localhost:8000/health` returned HTTP `200`;
  - `curl http://localhost:5173/` returned HTTP `200`.
- Compose-internal frontend proxy checks — passed:
  - `http://localhost:5173/health` from the frontend container returned HTTP `200`;
  - `http://localhost:5173/api/datasets/status` from the frontend container returned HTTP `200`;
  - direct `http://backend:8000/health` from the frontend container returned HTTP `200`.
- `docker compose down -v` — passed. Containers/network were stopped and removed, including the anonymous node_modules volume.

Backend tests were not run because backend code did not change.

Pre-staging checks:

- `git status --short --branch` — passed. Showed TASK-2026-06-22-05 files plus pre-existing unstaged `.ai/task.md`.
- `git diff --stat HEAD` — passed. Included tracked task files plus pre-existing `.ai/task.md`.
- `git diff --name-only --cached` — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.
- `git status --short --ignored frontend backend/data data ui-kits .env` — passed. `.env`, generated data, `frontend/dist/`, `frontend/node_modules/`, and `frontend/tsconfig.tsbuildinfo` were ignored and not staged.

Final staged checks:

- `git status --short --branch` — passed. `.ai/task.md` remained unstaged.
- `git diff --stat HEAD` — passed. Included staged TASK-2026-06-22-05 files plus pre-existing unstaged `.ai/task.md`.
- `git diff --name-only --cached` — passed. Listed only `.ai/report.md`, `docker-compose.yml`, `docs/development.md`, `frontend/README.md`, and `frontend/vite.config.ts`.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.
- `git status --short --ignored frontend backend/data data ui-kits .env` — passed. `.env`, generated data, `frontend/dist/`, `frontend/node_modules/`, `frontend/tsconfig.tsbuildinfo`, and `ui-kits/` were not staged.
- `git log --oneline -1` — passed. Latest relevant commit remained `b45ecfd planner: TASK-2026-06-22-05 Run full stack with Compose`.

## Known Limitations

- Compose runs the Vite development server, not a production frontend build.
- No Nginx, HTTPS, production deployment, CI, authentication, new screens, or new backend endpoints were added.
- `npm install`/`npm ci` still reports 1 low severity npm vulnerability from the current dependency tree; no `npm audit fix` was run to avoid unplanned dependency changes.
