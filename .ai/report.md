# Отчет: TASK-2026-06-21-09

Статус: done

## Кратко

Реализован первый read-only Bitrix boundary для MVP: безопасные настройки, явные allowlist-ы Bitrix полей, read-only REST client с пагинацией, metadata discovery, ручная mocked-testable загрузка contacts/deals/links/stages в существующие raw DuckDB таблицы и последующая нормализация.

Frontend, NBRB, Parquet snapshots, production dataset activation, scheduler, authentication и live Bitrix checks не добавлялись.

## Измененные файлы

- `backend/app/core/config.py`
- `backend/app/bitrix/__init__.py`
- `backend/app/bitrix/allowlist.py`
- `backend/app/bitrix/client.py`
- `backend/app/bitrix/discovery.py`
- `backend/app/bitrix/ingestion.py`
- `backend/app/bitrix/transform.py`
- `backend/app/storage/loaders.py`
- `backend/app/api/models.py`
- `backend/app/main.py`
- `backend/pyproject.toml`
- `backend/tests/test_bitrix_client.py`
- `backend/tests/test_bitrix_discovery.py`
- `backend/tests/test_bitrix_ingestion.py`
- `backend/tests/test_api_bitrix.py`
- `.env.example`
- `backend/README.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/project-status.md`
- `docs/testing.md`
- `.ai/report.md`

## Запущенные проверки

- `git log --oneline -5` before implementation — passed.
- `git status --short` before implementation — passed; showed pre-existing modified `.ai/task.md`. It was not edited for this task.
- `python -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — not run because `python` command is absent in this environment.
- `python3 -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — passed.
- `python3 -m pytest` from `backend/` — not run because system Python has no `pytest` installed.
- `/tmp/bitrix-task-06-venv/bin/python -m pytest` from `backend/` — passed: 43 tests passed.

## Критерии приемки

- Bitrix settings are added safely and tests run without live credentials — выполнено.
- Read-only Bitrix client supports mocked metadata/list/link/stage flows — выполнено.
- Field allowlists are centralized and tested — выполнено.
- Forbidden fields are not requested and are ignored if present in mocked responses — выполнено.
- Discovery reports configured contact type field present/missing status safely — выполнено.
- Manual mocked ingestion loads contacts, deals, links, and stages into raw DuckDB tables idempotently — выполнено.
- Existing normalization runs after mocked Bitrix raw ingestion — выполнено.
- Sync/discovery status surfaces expose counts/errors without secrets — выполнено.
- Existing synthetic pipeline, analytics, and API tests continue to pass — выполнено.
- Documentation and `.ai/report.md` reflect the new real Bitrix boundary milestone — выполнено.
- No secrets, raw data, databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, generated artifacts, frontend builds, or `ui-kits/` changes were added — выполнено.

## Факты

- New Bitrix package: `backend/app/bitrix/`.
- New settings:
  - `BITRIX_WEBHOOK_URL`;
  - `BITRIX_CONTACT_TYPE_FIELD`;
  - `BITRIX_PAGE_SIZE`.
- New manual Bitrix endpoints:
  - `GET /api/bitrix/discovery`;
  - `POST /api/bitrix/sync/run`;
  - `GET /api/bitrix/sync/status`.
- Existing local synthetic endpoints remain unchanged:
  - `POST /api/sync/run`;
  - `GET /api/sync/status`.
- The Bitrix client allows only read methods:
  - `crm.contact.fields`;
  - `crm.deal.fields`;
  - `crm.contact.list`;
  - `crm.deal.list`;
  - `crm.deal.contact.items.get`;
  - `crm.status.list`.
- Contact select fields are limited to `ID`, `NAME`, `SECOND_NAME`, `LAST_NAME`, plus configured `BITRIX_CONTACT_TYPE_FIELD` when present.
- Deal select fields are limited to `ID`, `TITLE`, `OPPORTUNITY`, `CURRENCY_ID`, `DATE_CREATE`, `CLOSEDATE`, `STAGE_ID`, and `CATEGORY_ID`.
- Manual Bitrix ingestion reloads only `raw_contacts`, `raw_deals`, `raw_deal_contact_links`, and `raw_stages`.
- Manual Bitrix ingestion preserves local `contact_type_rules` and `currency_rates`.
- Missing credentials produce safe structured error/status responses and do not break the regular test suite.

## Предположения

- Traditional Bitrix CRM methods `crm.contact.list` and `crm.deal.list` are acceptable for this first boundary because they match the current raw schema and allow explicit field selection.
- Universal Bitrix item methods can be added later if the real account requires them.
- Discovery candidate fields can list safe custom `UF_*` contact field codes to help choose `BITRIX_CONTACT_TYPE_FIELD`; ingestion still stores only the configured field.
- Existing `local_dataset_status` is acceptable for the first manual Bitrix status row before production dataset activation exists.

## Неизвестное

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual production contact type values, priorities, and region mapping.
- Actual production pipelines, stage IDs, category IDs, currencies, and deal-contact link behavior.
- Whether Bitrix account permissions allow all required read-only methods.
- Final production storage layout, migration strategy, dataset activation mechanics, and Parquet snapshot format.
- Whether the real account should use universal `crm.item.list` methods instead of traditional CRM list methods.

## Риски или следующий шаг

Next likely step: run `GET /api/bitrix/discovery` with a real read-only Bitrix credential, choose and configure `BITRIX_CONTACT_TYPE_FIELD`, then plan production dataset activation and NBRB currency integration.
