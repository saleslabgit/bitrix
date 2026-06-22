# Отчет: TASK-2026-06-22-08

Статус: done

## Кратко

Contacts screen переключен с original-currency totals на USD analytics metrics.

Основная таблица теперь использует:

```text
GET /api/reports/contacts/analytics
```

В таблице отображаются:

- контакт;
- normalized type;
- region;
- total/won/open/lost deal counts;
- `Выручка USD` из `revenue_usd`;
- `Расчетная прибыль USD` из `estimated_profit_usd`;
- latest deal date.

`total_amount_original` больше не используется как основная финансовая метрика на Contacts screen.

## Измененные файлы

- `backend/app/reports/analytics.py` — добавлен scoped `status` filter для contact analytics.
- `backend/app/main.py` — `GET /api/reports/contacts/analytics` принимает `status`.
- `backend/tests/test_api_local.py` — добавлена проверка status filter для analytics endpoint.
- `frontend/src/api.ts` — frontend client переключен на `ContactAnalyticsPageResponse` shape и `/api/reports/contacts/analytics`.
- `frontend/src/App.tsx` — таблица использует USD revenue/profit, добавлены blocking refresh progress и user-facing success counts.
- `frontend/src/styles.css` — добавлены стили header refresh action, success alert, spinner, USD cells.
- `docs/development.md` — обновлен список endpoints для Contacts screen и примечание про USD analytics.
- `frontend/README.md` — указано, что Contacts table использует USD analytics metrics.
- `docs/project-status.md` — обновлен текущий статус проекта.
- `.ai/report.md` — this report.

`.ai/task.md` остался pre-existing unstaged planner change и не изменялся Codex. `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` не staged.

## API And Filter Behavior

Contacts screen uses:

```text
GET /api/reports/contacts/analytics
GET /api/meta/filters
GET /api/datasets/status
POST /api/local/refresh-data
```

Status filter remains available and effective. It is now supported by `GET /api/reports/contacts/analytics`, matching the existing screen behavior instead of leaving a silent no-op filter.

## Refresh UX

While refresh is running, the table area shows:

```text
Загрузка данных из Bitrix...
Это может занять несколько минут.
```

Duplicate refresh clicks are disabled. After success, the UI shows a user-facing summary built from safe response counts, for example:

```text
Обновление завершено: 14 216 контактов, 9 142 сделок, 320 курсов загружено.
```

The frontend no longer uses backend technical text such as `Manual Bitrix refresh completed.` as the main refresh completion message.

## Bitrix Calls

Live Bitrix refresh was not run.

Bitrix methods called during this task:

```text
none
```

No Bitrix write methods were added or called. The only `crm.*update` string found by safety search remains the existing negative test that asserts write methods are rejected.

## Проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit was `629c027 planner: TASK-2026-06-22-08 Improve contacts USD and refresh UX`.
- `git status --short --branch` — passed. Showed only pre-existing modified `.ai/task.md`.

Backend:

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

Safety checks:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests` — passed for implementation scope. It found only the existing `crm.deal.update` negative test.
- `git status --short --branch` — passed. `.ai/task.md` remained unstaged.
- `git diff --stat HEAD` — passed. It includes the pre-existing unstaged `.ai/task.md` diff.
- `git diff --name-only --cached` before staging — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed.
- `git status --short --ignored frontend backend/data data ui-kits .env` — passed. `.env`, `backend/data/`, `data/`, `frontend/dist/`, `frontend/node_modules/`, and `frontend/tsconfig.tsbuildinfo` were ignored and not staged.
- Final `git diff --name-only --cached` — passed. Staged files are only TASK-2026-06-22-08 implementation/docs/report files:
  - `.ai/report.md`
  - `backend/app/main.py`
  - `backend/app/reports/analytics.py`
  - `backend/tests/test_api_local.py`
  - `docs/development.md`
  - `docs/project-status.md`
  - `frontend/README.md`
  - `frontend/src/App.tsx`
  - `frontend/src/api.ts`
  - `frontend/src/styles.css`
- `git log --oneline -1` — passed. Latest relevant commit remained `629c027 planner: TASK-2026-06-22-08 Improve contacts USD and refresh UX`.

## Known Limitations

- Contacts screen still remains the only frontend report screen.
- Manual refresh remains synchronous and can block for several minutes, by design for this MVP stage.
- `npm ci` inside the frontend container still reports 1 low severity npm vulnerability; no dependency update or audit fix was run to avoid unrelated changes.
