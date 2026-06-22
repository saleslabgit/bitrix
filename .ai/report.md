# Отчет: TASK-2026-06-22-06

Статус: done

## Кратко

Исправлен Compose runtime для frontend Vite dev server: frontend container теперь получает read-only mount дизайн-системы.

Root cause:

```text
frontend/src/styles.css -> @import "../../ui-kits/styles.css"
```

В контейнере frontend рабочий каталог смонтирован как `/app`, поэтому импорт из `/app/src/styles.css` резолвится в `/ui-kits/styles.css`. До этой задачи `ui-kits/` в контейнер не монтировался, из-за чего Vite мог показывать CSS ENOENT overlay.

Fix:

```yaml
- ./ui-kits:/ui-kits:ro
```

Manual frontend flow остается рабочим, потому что локально тот же импорт продолжает резолвиться в репозиторный `ui-kits/`.

## Измененные файлы

- `docker-compose.yml` — добавлен read-only bind mount `./ui-kits:/ui-kits:ro` в `frontend` service.
- `docs/development.md` — уточнено, что Compose монтирует `ui-kits/` read-only для Vite CSS imports.
- `frontend/README.md` — уточнено, что Compose монтирует `ui-kits/` read-only.
- `.ai/report.md` — this report.

`ui-kits/` files were not modified or staged. `.ai/task.md` remains a pre-existing unstaged planner change and was not staged by Codex. `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, and `frontend/dist` were not staged.

## User Verification Command

```bash
docker compose up --build
```

Open:

```text
http://localhost:5173
```

The Contacts screen should open without the Vite `[plugin:vite:css]` ENOENT overlay.

## Bitrix Calls

Bitrix methods called in this task:

```text
none
```

No Bitrix sync was run. No Bitrix row-listing methods were called. No Bitrix write methods were called.

## Запущенные проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit was `01fde5a planner: TASK-2026-06-22-06 Fix Compose ui-kits mount`.
- `git status --short --branch` — passed. Showed only pre-existing modified `.ai/task.md`.

Documentation/library checks:

- Context7 docs queried for Docker Compose bind mount syntax.

Runtime checks:

- `docker compose config` — passed. The rendered config includes `frontend` bind mount:
  - source: repository `ui-kits`;
  - target: `/ui-kits`;
  - `read_only: true`.
- `docker compose up --build -d` — passed. Backend and frontend containers started.
- `curl -f -sS http://localhost:8000/health` — passed.
- `curl -f -sS http://localhost:5173/` — passed.
- `curl -f -sS http://localhost:5173/health` — passed through the Vite proxy to backend.
- `curl -f -sS http://localhost:5173/api/datasets/status` — passed through the Vite proxy to backend.
- Additional Vite module checks:
  - `curl -f -sS http://localhost:5173/src/main.tsx` — passed, HTTP `200`.
  - `curl -f -sS http://localhost:5173/src/styles.css` — passed, HTTP `200`, proving Vite could transform the CSS import graph.
- `docker compose logs frontend --tail 160` — passed. Logs showed Vite ready on `0.0.0.0:5173`.
- `docker compose logs frontend | rg "ENOENT|ui-kits/styles\\.css|\\[plugin:vite:css\\]"` — no matches. Command exited `1` because no error pattern was found.
- `docker compose down -v` — passed. Containers/network were stopped and removed, including the anonymous node_modules volume.

`npm run build` was not run because no frontend source files changed; only Compose/docs/report changed.

Backend tests were not run because backend code did not change.

Pre-staging checks:

- `git status --short --branch` — passed. Showed TASK-2026-06-22-06 files plus pre-existing unstaged `.ai/task.md`.
- `git diff --stat HEAD` — passed. Included tracked task files plus pre-existing `.ai/task.md`.
- `git diff --name-only --cached` — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.
- `git status --short --ignored frontend backend/data data ui-kits .env` — passed. `.env`, generated data, `frontend/dist/`, `frontend/node_modules/`, and `frontend/tsconfig.tsbuildinfo` were ignored and not staged.

Final staged checks:

- `git status --short --branch` — passed. `.ai/task.md` remained unstaged.
- `git diff --stat HEAD` — passed. Included staged TASK-2026-06-22-06 files plus pre-existing unstaged `.ai/task.md`.
- `git diff --name-only --cached` — passed. Listed only `.ai/report.md`, `docker-compose.yml`, `docs/development.md`, and `frontend/README.md`.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.
- `git status --short --ignored frontend backend/data data ui-kits .env` — passed. `.env`, generated data, `frontend/dist/`, `frontend/node_modules/`, `frontend/tsconfig.tsbuildinfo`, and `ui-kits/` were not staged.
- `git log --oneline -1` — passed. Latest relevant commit remained `01fde5a planner: TASK-2026-06-22-06 Fix Compose ui-kits mount`.

## Known Limitations

- Compose still runs the Vite development server, not a production frontend image.
- npm still reports 1 low severity vulnerability during container `npm ci`; no `npm audit fix` was run to avoid unrelated dependency changes.
