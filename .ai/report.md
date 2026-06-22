# Отчет: TASK-2026-06-22-27

Статус: done

## Кратко

Устранена backend-причина intermittent `500` на `GET /api/meta/filters` и
смежных локальных read endpoints: FastAPI sync routes больше не используют одну
process-global DuckDB connection параллельно из разных worker threads.

## Root Cause

Точный traceback в локальном runtime не воспроизвелся до фикса. По коду
подтверждена опасная схема:

- `backend/app/local_database.py` хранил одну глобальную DuckDB connection;
- FastAPI sync endpoints могут выполняться параллельно в threadpool;
- `get_connection()` возвращал один и тот же connection object всем endpoints;
- `get_connection()` дополнительно вызывал `initialize_schema()` на каждом
  доступе, то есть DDL попадал в горячий путь чтения.

Это создавало конкурентное использование одного DuckDB connection object и
конкурентный schema init во время одновременных запросов frontend к status,
metadata и report endpoints.

## Измененные файлы

- `backend/app/local_database.py`
- `backend/app/main.py`
- `backend/tests/test_api_local.py`
- `docs/data-model.md`
- `docs/development.md`
- `.ai/report.md`

## Реализация

- Добавлен process-local `RLock` вокруг общей DuckDB connection.
- Добавлен `connection_scope()` для endpoint-level блокировки: локальная DB
  операция endpoint-а выполняется целиком внутри lock, а не только момент
  получения connection.
- `get_connection()` оставлен для существующих прямых тестов и вспомогательных
  сценариев, но теперь лениво инициализирует схему только один раз за lifecycle
  connection.
- `reset_connection()` теперь закрывает connection и сбрасывает флаг schema
  initialization под тем же lock.
- Локальные status, filters, refresh, diagnostics и report endpoints переведены
  на `connection_scope()`.
- Добавлен concurrent regression test, который параллельно читает
  `dataset_status`, `meta_filters`, Contacts, Deals и ABC analytics через route
  functions после подготовки локального synthetic dataset.

## Документация

- `docs/data-model.md` описывает process-local DuckDB connection, одноразовую
  schema initialization и endpoint-level serialization.
- `docs/development.md` уточняет runtime behavior для concurrent frontend
  requests к локальным read/refresh endpoints.

## Запущенные проверки

Before implementation:

- `git log --oneline -5`
- `git status --short`

Backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_api_local.py`
  — passed, `14 passed`.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest`
  — passed, `112 passed`.

Runtime smoke:

- `docker compose up --build -d` — passed.
- `curl -f http://127.0.0.1:8000/health` — passed.
- `curl -f http://127.0.0.1:8000/api/datasets/status` — passed.
- `curl -f http://127.0.0.1:8000/api/meta/filters` — passed.
- `curl -f http://127.0.0.1:5173/` — passed.
- `docker compose down -v` — passed.

Safety:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

## Факты

- No frontend code changed.
- No Bitrix calls were added to Docker startup or local read endpoints.
- Manual refresh remains explicit through API/UI action.
- No CRM write methods were added.
- No secrets, raw rows, local DB files, Parquet snapshots, CSV exports, or
  forbidden personal fields were committed.

## Предположения

- Intermittent `500` was caused by concurrent operations on the shared DuckDB
  connection and/or concurrent schema initialization on hot read paths.

## Неизвестное

- The original production traceback was not available in the repository and was
  not reproduced locally before the fix.

## Риски или следующий шаг

Endpoint-level serialization trades concurrent local DuckDB query execution for
stability with the existing single shared connection. If report latency becomes
an issue later, the next step should be a deliberate connection-management
design, not ad hoc shared connection reuse.
