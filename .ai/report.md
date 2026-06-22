# Отчет: TASK-2026-06-22-31

Статус: done

## Кратко

Подготовил FASTVPS Docker deployment path без изменения локального dev-flow.
Локально по-прежнему используется `docker compose up --build`. Для production
добавлен отдельный `docker-compose.prod.yml`: backend работает только внутри
Docker-сети, built frontend отдается nginx-контейнером, а наружу для панели
публикуется только `127.0.0.1:8080:80`.

## Измененные файлы

- `.dockerignore`
- `.gitignore`
- `docker-compose.prod.yml`
- `deploy/fastvps/.env.production.example`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `docs/deployment.md`
- `docs/development.md`
- `docs/project-status.md`
- `.ai/report.md`

## Что сделано

- Добавлен production frontend Dockerfile с Node build stage и nginx runtime
  stage.
- Добавлен nginx config со SPA fallback на `index.html`.
- `/api/*` и `/health` проксируются из nginx в `http://backend:8000` внутри
  Compose-сети.
- Добавлен production Compose файл с `restart: unless-stopped`, persistent
  bind mount `./data:/app/data`, приватным backend и единственным опубликованным
  web-портом для reverse proxy панели.
- Добавлен safe production env template для FASTVPS с auth enabled и secure
  cookies by default guidance.
- Добавлена `.dockerignore`, чтобы root build context для frontend image не
  включал `.env`, локальные базы, raw/generated data, logs, caches,
  `node_modules` или `frontend/dist`.
- Добавлена документация ручного FASTVPS deploy через HTTPS/reverse proxy панели,
  server commands, update flow, backup/restore guidance и ручной Bitrix refresh
  после login.
- Обновлен project status: production preparation exists; actual server deploy,
  final domain, panel setup, and backup destination remain operator steps.

## Запущенные проверки

- `git log --oneline -5` — passed; последний релевантный коммит:
  `planner: TASK-2026-06-22-31 Prepare FASTVPS Docker deployment`.
- `git status --short` — checked before changes; existing local modifications
  in `.ai/task.md`, `AGENTS.md`, and `WORKFLOW.md` were present and were not
  touched for this task.
- `docker compose config` — passed. Command loaded the local `.env`; no values
  were copied into docs or committed files.
- `docker compose -f docker-compose.prod.yml config` — passed. Command loaded
  the local `.env`; no values were copied into docs or committed files.
- `cd frontend && npm run build` — passed. Vite reported the existing
  Recharts-related bundle-size warning; build succeeded.
- `docker compose -f docker-compose.prod.yml up --build -d` — passed with Docker
  daemon access. It built backend and web images and started the production
  topology. Compose warned about an existing orphan `bitrix-frontend-1` from a
  different/local compose service; it was not removed because it was outside
  this task.
- `curl -f http://127.0.0.1:8080/health` — passed through production nginx to
  backend.
- `curl -f http://127.0.0.1:8080/` — passed and returned the built frontend
  HTML from nginx.
- `docker compose -f docker-compose.prod.yml down` — stopped and removed the
  production backend/web containers. The default network remained because the
  pre-existing orphan container still used it.
- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src deploy docs`
  — found only the existing negative test `crm.deal.update`; no Bitrix write
  method was added.

## Факты

- Default `docker-compose.yml` was not changed.
- Production Compose does not publish backend port `8000`.
- Production browser path is same-origin through nginx: frontend static files,
  `/api/*`, and `/health` use the same web service.
- Docker Compose startup still only starts services. It does not call Bitrix or
  refresh local data automatically.
- `frontend/dist` was generated during build but remains ignored and was not
  staged.
- No real `.env`, webhook URL, auth password, session secret, local database,
  Parquet, CSV, log, cache, `node_modules`, or `ui-kits/` change was added.

## Предположения

- FASTVPS panel can reverse proxy the public HTTPS site to
  `http://127.0.0.1:8080`, or the operator can adjust the published host
  binding/port according to panel requirements.
- The repository-local `./data` directory is acceptable as the first production
  persistence location until the operator chooses a backup destination and
  retention policy.

## Неизвестное

- Final domain name.
- Exact FASTVPS panel UI labels and proxy field names.
- Backup destination and retention policy.
- Whether the first server dataset will be restored from an existing `data/`
  backup or refreshed manually from Bitrix after deployment.

## Риски или следующий шаг

- On the real VPS, create `.env` from `deploy/fastvps/.env.production.example`,
  set strong auth credentials/session secret and the read-only Bitrix webhook,
  then configure the FASTVPS panel HTTPS reverse proxy to the local app port.
