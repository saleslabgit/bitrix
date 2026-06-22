# Отчет: TASK-2026-06-22-07

Статус: done

## Кратко

Добавлен ручной UI-triggered refresh flow для локального приложения после `docker compose up --build`.

Docker по-прежнему только стартует сервисы и не запускает Bitrix/NBRB refresh автоматически. Если локальный `data/analytics.duckdb` уже содержит активный dataset, Contacts table загружается как раньше. Если активного dataset нет, frontend показывает состояние:

```text
Локальная база не подготовлена.
Нажмите «Обновить из Bitrix», чтобы загрузить данные.
```

Кнопка `Обновить из Bitrix` вызывает новый backend endpoint:

```text
POST /api/local/refresh-data
```

Endpoint строит Bitrix client из env, запускает существующую read-only manual ingestion, применяет approved contact type rules, перезапускает локальную нормализацию и загружает NBRB rates для raw deals. Успешный dataset активируется только после полной подготовки. Если локальная подготовка или NBRB rates падают, новый dataset не активируется как готовый.

## Измененные файлы

- `backend/app/main.py` — добавлен `POST /api/local/refresh-data`.
- `backend/app/api/models.py` — добавлен typed safe response `LocalDataRefreshResponse`.
- `backend/app/bitrix/ingestion.py` — добавлен optional finalizer hook для переиспользования manual ingestion до activation.
- `backend/app/pipeline/manual_refresh.py` — добавлена orchestration-функция полного ручного refresh.
- `backend/app/pipeline/currency_rates.py` — добавлен controlled transaction mode для вызова внутри refresh transaction и safe NBRB transport error.
- `backend/tests/test_api_bitrix.py` — добавлены mocked tests для full refresh, no-credentials flow и failure-before-activation.
- `frontend/src/api.ts` — добавлен `refreshLocalData()`.
- `frontend/src/App.tsx` — добавлены dataset-not-ready state, refresh mutation, отключение contacts/filter queries до готового dataset.
- `frontend/src/styles.css` — добавлены стили для refresh empty/error/progress state.
- `docs/development.md` — описан простой Docker -> frontend -> manual refresh flow.
- `frontend/README.md` — описан frontend/manual refresh flow.
- `docs/project-status.md` — обновлен текущий статус проекта.
- `.ai/report.md` — this report.

`.ai/task.md` остался pre-existing unstaged planner change и не изменялся Codex. `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` не staged.

## Bitrix Calls

Live Bitrix refresh was not run.

Bitrix methods called during this task:

```text
none
```

No Bitrix write methods were added or called. The code continues to use the existing read-only Bitrix client allowlist for live manual ingestion.

## Проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit was `55325f1 planner: TASK-2026-06-22-07 Add manual data refresh flow`.
- `git status --short` — passed. Showed only pre-existing modified `.ai/task.md`.

Backend:

- `cd backend && python -m pytest` — not run because `python` is not installed in this environment.
- `cd backend && python3 -m pytest` — not run because system Python did not have `pytest`.
- `python3 -m venv /tmp/bitrix-backend-venv` — passed.
- `/tmp/bitrix-backend-venv/bin/python -m pip install -e '.[dev]'` — passed in a temporary venv outside the repository.
- `cd backend && /tmp/bitrix-backend-venv/bin/python -m pytest` — passed, `58 passed`.

Frontend:

- `cd frontend && npm run build` — passed.

Compose:

- `docker compose config` — passed. Output is not copied here because local Compose config expands local env values.
- `docker compose up --build -d` — passed.
- `curl -f -sS http://127.0.0.1:8000/health` — passed.
- `curl -f -sS http://127.0.0.1:5173/` — passed.
- `docker compose down -v` — passed.

Live/manual data refresh was intentionally not run during Compose verification. Only health/frontend root HTTP probes were made.

Safety and Git gate checks:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests` — passed for implementation scope. It found only the existing `crm.deal.update` negative test that asserts write methods are rejected.
- `git status --short --branch` — passed. `.ai/task.md` remained unstaged.
- `git diff --stat HEAD` — passed. It includes the pre-existing unstaged `.ai/task.md` diff.
- `git diff --name-only --cached` before staging — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed.
- `git status --short --ignored frontend backend/data data ui-kits .env` — passed. `.env`, `backend/data/`, `data/`, `frontend/dist/`, `frontend/node_modules/`, and `frontend/tsconfig.tsbuildinfo` were ignored and not staged.
- Final `git diff --name-only --cached` — passed. Staged files are only TASK-2026-06-22-07 implementation/docs/report files:
  - `.ai/report.md`
  - `backend/app/api/models.py`
  - `backend/app/bitrix/ingestion.py`
  - `backend/app/main.py`
  - `backend/app/pipeline/currency_rates.py`
  - `backend/app/pipeline/manual_refresh.py`
  - `backend/tests/test_api_bitrix.py`
  - `docs/development.md`
  - `docs/project-status.md`
  - `frontend/README.md`
  - `frontend/src/App.tsx`
  - `frontend/src/api.ts`
  - `frontend/src/styles.css`
- `git log --oneline -1` — passed. Latest relevant commit remained `55325f1 planner: TASK-2026-06-22-07 Add manual data refresh flow`.

## Known Limitations

- `POST /api/local/refresh-data` is synchronous and can block for several minutes, by design for this MVP task.
- No background queue, scheduler, auth, roles, dashboard, or new report screens were added.
- `npm ci` inside the frontend container still reports 1 low severity npm vulnerability; no dependency update or audit fix was run to avoid unrelated changes.
