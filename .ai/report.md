# Отчет: TASK-2026-06-21-11

Статус: done

## Кратко

Реализован storage milestone: backend теперь использует настраиваемый локальный DuckDB storage boundary, хранит append-only metadata по dataset runs, активирует только успешные synthetic/Bitrix runs, откатывает handled failed Bitrix replacements, пишет allowlisted raw Parquet snapshots и отдает общий typed status по активному dataset/latest run.

Фронтенд, live Bitrix smoke test, NBRB, auth, scheduler, persisted analytics tables, CI и deployment не реализовывались.

## Измененные файлы

- `.env.example` — добавлены placeholder storage env vars.
- `docker-compose.yml` — добавлен bind mount `./data:/app/data` для локального persistent runtime.
- `README.md` — обновлен текущий backend/storage статус.
- `backend/README.md` — задокументированы storage modules, env vars, snapshots и dataset status endpoint.
- `backend/app/core/config.py` — добавлены `APP_DATA_DIR`, `APP_DUCKDB_PATH`, нормализация пустого DuckDB path.
- `backend/app/local_database.py` — shared DuckDB connection стал lazy и настраиваемым.
- `backend/app/storage/connection.py` — новый configured DuckDB connection helper.
- `backend/app/storage/schema.py` — добавлены `local_dataset_runs` и `local_active_dataset`.
- `backend/app/storage/snapshots.py` — новый allowlisted raw Parquet snapshot writer.
- `backend/app/storage/status.py` — новый слой dataset run/active metadata.
- `backend/app/storage/__init__.py` — обновлено описание storage package.
- `backend/app/pipeline/synthetic.py` — synthetic run теперь транзакционно загружает, snapshot-ит и активирует dataset.
- `backend/app/bitrix/ingestion.py` — manual Bitrix ingestion теперь транзакционно загружает, snapshot-ит и активирует только success; handled failures пишут error run без активации.
- `backend/app/api/models.py` — расширен `PipelineStatusResponse`, добавлен `DatasetStorageStatusResponse`.
- `backend/app/main.py` — synthetic/Bitrix sync передают configured data dir; добавлен `GET /api/datasets/status`.
- `backend/tests/test_storage_schema.py` — добавлены проверки persistent temp DuckDB и новых metadata tables.
- `backend/tests/test_pipeline.py` — добавлена проверка raw Parquet snapshots и active run для synthetic.
- `backend/tests/test_bitrix_ingestion.py` — добавлены проверки snapshots, activation и failed run preservation.
- `backend/tests/test_api_local.py` — API tests используют temp persistent storage; добавлена проверка `/api/datasets/status`.
- `backend/tests/test_api_bitrix.py` — no-credentials API test изолирован temp persistent storage.
- `docs/architecture.md` — обновлены storage/snapshot/activation факты.
- `docs/data-model.md` — описаны persistent DuckDB, dataset activation и snapshot boundaries.
- `docs/development.md` — описаны storage env vars, generated data location и safe local flow.
- `docs/project-status.md` — обновлены done/not done/next steps.
- `docs/testing.md` — обновлена текущая storage/snapshot/activation test coverage.

`AGENTS.md` не изменялся: текущие правила уже запрещают коммитить DuckDB, Parquet, raw exports и secrets.

## Запущенные проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit before work:
  `327a582 planner: TASK-2026-06-21-11 Implement persistent dataset storage milestone`.
- `git status --short` — passed. Showed pre-existing modified `.ai/task.md`.

Syntax/import:

- `python -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — not run: `python` command is absent in this environment.
- `python3 -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — passed.

Tests:

- `python -m pytest` from `backend/` — not run: `python` command is absent in this environment.
- `python3 -m pytest` from `backend/` — not run: system Python has no `pytest` installed.
- `/tmp/bitrix-task-06-venv/bin/python -m pytest` from `backend/` — passed: 47 tests passed in 39.63s.

Compose and sanity:

- `docker compose config` from repo root — passed. Rendered backend service with `APP_DATA_DIR=data`, blank `APP_DUCKDB_PATH`, and bind mount `./data:/app/data`; no real secrets.
- `/tmp/bitrix-task-06-venv/bin/python -c "from app.core.config import Settings; from app.storage.connection import resolve_duckdb_path; s=Settings(APP_DATA_DIR='data', APP_DUCKDB_PATH=''); print(resolve_duckdb_path(s))"` from `backend/` — passed; output `data/analytics.duckdb`.

Final git checks after staging:

- `git status --short --branch` — passed. Showed TASK-11 files staged and pre-existing `.ai/task.md` still unstaged.
- `git diff --stat HEAD` — passed. Included staged TASK-11 changes plus the pre-existing unstaged `.ai/task.md` diff.
- `git diff --name-only --cached` — passed. Listed only TASK-11 implementation/docs/test files plus `.ai/report.md`; did not include `.ai/task.md`, `ui-kits/`, generated data, DuckDB files, Parquet files, CSV exports, dependency folders, caches, or frontend builds.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.

## Реализованное поведение

- Runtime DuckDB path is configurable:
  - `APP_DATA_DIR=data`;
  - blank `APP_DUCKDB_PATH` uses `APP_DATA_DIR/analytics.duckdb`;
  - tests can still pass `:memory:` or temp file DuckDB connections directly.
- Backend shared connection is lazy and initialized through the configured storage boundary.
- Schema initialization remains idempotent and now includes:
  - `local_dataset_runs`;
  - `local_active_dataset`;
  - existing `local_dataset_status` for backward-compatible sync status.
- Successful synthetic and manual Bitrix runs:
  - load raw data;
  - normalize data;
  - write allowlisted raw Parquet snapshots when a data dir is provided;
  - store run metadata;
  - become the active local dataset.
- Handled manual Bitrix failures:
  - rollback any transaction-backed raw/normalized replacement;
  - store an error run;
  - do not replace or deactivate the previous successful active dataset.
- Snapshot output is limited to allowed raw tables/columns:
  - `raw_contacts`;
  - `raw_deals`;
  - `raw_deal_contact_links`;
  - `raw_stages`.
- `GET /api/datasets/status` returns active dataset/latest run metadata with safe messages, counts, UTC timestamps, relative snapshot identifiers, and no local absolute paths, raw rows, webhook URLs, or file contents.

## Факты

- No live Bitrix calls were made.
- No real credentials, raw Bitrix data, DuckDB files, Parquet files, CSV exports, dependency folders, caches, or frontend builds were staged.
- `.ai/task.md` had a pre-existing working-tree modification before TASK-11 implementation and was not edited intentionally.
- `ui-kits/` was not modified.

## Предположения

- The current single active raw/normalized table set plus transaction rollback is sufficient for this milestone; a full staging-table swap can be planned later if needed.
- Relative snapshot identifiers such as `snapshots/<dataset_kind>/<run_id>/<table>.parquet` are safe to expose in status responses.
- The existing `/tmp/bitrix-task-06-venv` is the configured backend dev environment for this workspace because system Python lacks pytest.

## Неизвестное

- Live Bitrix field availability and real `BITRIX_CONTACT_TYPE_FIELD`.
- Real production data volume and whether it will require a full staging-table swap instead of the current transaction-backed replacement.
- Final production migration, backup, and deployment strategy.

## Риски или следующий шаг

Next step: run discovery against a real read-only Bitrix credential, set `BITRIX_CONTACT_TYPE_FIELD`, perform a manual local sync, and then decide whether NBRB integration or a full staging-table swap should be the next backend milestone.
