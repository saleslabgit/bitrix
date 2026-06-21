# Отчет: TASK-2026-06-21-07

Статус: done

## Кратко

Реализовал первый локальный backend pipeline milestone на синтетических данных: данные fixture загружаются в DuckDB raw tables, нормализуются в `normalized_contacts` и `normalized_deals`, сохраняется local synthetic pipeline status, а FastAPI получил минимальные read-only endpoints для статуса, запуска локального synthetic pipeline, фильтров и contact summary.

Реальная интеграция Bitrix, NBRB, Parquet, USD conversion и полноценная аналитика не добавлялись.

## Измененные файлы

- `backend/app/api/__init__.py`
- `backend/app/api/models.py`
- `backend/app/local_database.py`
- `backend/app/main.py`
- `backend/app/pipeline/__init__.py`
- `backend/app/pipeline/normalization.py`
- `backend/app/pipeline/synthetic.py`
- `backend/app/pipeline/synthetic_dataset.py`
- `backend/app/reports/__init__.py`
- `backend/app/reports/local.py`
- `backend/app/storage/loaders.py`
- `backend/app/storage/schema.py`
- `backend/pyproject.toml`
- `backend/tests/fixtures/synthetic_dataset.py`
- `backend/tests/test_api_local.py`
- `backend/tests/test_pipeline.py`
- `backend/tests/test_storage_schema.py`
- `backend/README.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/project-status.md`
- `docs/testing.md`
- `.ai/report.md`

## Запущенные проверки

- `git log --oneline -5` — passed; latest relevant commit is `1aca235 planner: TASK-2026-06-21-07 Implement local normalized pipeline and read API milestone`.
- `git status --short` before implementation — passed; showed pre-existing modified `.ai/task.md` and `AGENTS.md` line-ending changes. They were not edited or staged by this task.
- `python3 -m pytest` from `backend/` — failed before test collection because the system interpreter has no `pytest` installed.
- `/tmp/bitrix-task-06-venv/bin/python -m pytest` from `backend/` — passed: 20 tests passed.
- `/tmp/bitrix-task-06-venv/bin/python -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — passed.
- `docker compose config` from repository root — passed.
- Generated Python `__pycache__` artifacts created by checks were removed.

## Критерии приемки

- Raw fixture data can be loaded into DuckDB idempotently — выполнено.
- Normalized contacts and deals are generated from local raw tables — выполнено.
- Contact type and region normalization works with active rules and `Не определено` fallback — выполнено.
- Analytical contact assignment works and each deal appears once in normalized deals — выполнено.
- Deal without contact is preserved as `Без контакта` and `Не определено` — выполнено.
- Status groups are represented correctly for won/open/lost synthetic deals — выполнено.
- Minimal local read API endpoints work against local DuckDB data and return no forbidden fields — выполнено.
- Storage-backed tests cover pipeline and API behavior — выполнено.
- Existing tests continue to pass — выполнено.
- Documentation and `.ai/report.md` reflect the new milestone — выполнено.
- No real secrets, raw data, databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, or generated artifacts are included in task files — выполнено.

## Факты

- New normalized tables: `normalized_contacts`, `normalized_deals`.
- New status table: `local_dataset_status`.
- New local API endpoints:
  - `GET /api/sync/status`;
  - `POST /api/sync/run`;
  - `GET /api/meta/filters`;
  - `GET /api/reports/contacts`.
- `POST /api/sync/run` runs only the local synthetic fixture pipeline in an in-memory DuckDB connection.
- Normalization uses active `contact_type_rules`; inactive, missing, or unknown rules normalize to `Не определено`.
- Deal `7` resolves to contact `4` through the existing priority/primary/id analytical contact rules.
- Deal `30` has no contact and is preserved in normalized deals with `Без контакта`.
- The API tests call endpoint functions directly, not `fastapi.testclient.TestClient`, because the earlier health task documented `TestClient` hangs in this environment.
- DuckDB `TIMESTAMPTZ` fetching required `pytz` in this environment, so the local scaffold stores UTC timestamps in DuckDB `TIMESTAMP` columns and restores UTC-aware datetimes when building domain models.

## Предположения

- In-memory DuckDB is sufficient for this local synthetic milestone and avoids committing local database files.
- Direct DuckDB queries and small helper modules are enough before designing production repository/migration abstractions.
- Contact summaries may include local deal counts and original amount totals without implementing revenue/USD analytics.
- Keeping `tests/fixtures/synthetic_dataset.py` as a compatibility re-export is acceptable after moving the reusable synthetic dataset builder into `app.pipeline.synthetic_dataset`.

## Неизвестное

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual contact type values, priorities, and region mapping.
- Actual pipelines, stages, and currencies in Bitrix.
- Final production storage layout, migration strategy, dataset activation mechanics, and Parquet snapshot format.
- Final frontend response-shape needs beyond the current minimal local API.

## Риски или следующий шаг

Next step: choose the next milestone explicitly: either plan real Bitrix read-only ingestion and field allowlist discovery, or add the first analytics slice on top of the normalized synthetic tables.
