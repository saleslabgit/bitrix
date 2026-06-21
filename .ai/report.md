# Отчет: TASK-2026-06-21-08

Статус: done

## Кратко

Реализован локальный backend analytics milestone поверх normalized DuckDB data: добавлены deterministic USD conversion helpers на synthetic `currency_rates`, контактная аналитика, ABC full vs last 12 months, RFM и reactivation signal, deal-cycle metrics, stale open deals, concentration, type/region aggregates и typed FastAPI endpoints.

Реальная интеграция Bitrix, NBRB, frontend, authentication, Parquet и persisted analytics tables не добавлялись.

## Измененные файлы

- `backend/app/api/models.py`
- `backend/app/main.py`
- `backend/app/pipeline/synthetic_dataset.py`
- `backend/app/reports/analytics.py`
- `backend/tests/test_analytics.py`
- `backend/tests/test_api_local.py`
- `backend/README.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/fixtures.md`
- `docs/project-status.md`
- `docs/testing.md`
- `.ai/report.md`

## Запущенные проверки

- `git status --short` before implementation — passed; showed pre-existing modified `.ai/task.md` and `AGENTS.md`. They were not edited for the task.
- `/tmp/bitrix-task-06-venv/bin/python -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — passed.
- `/tmp/bitrix-task-06-venv/bin/python -m pytest` from `backend/` — passed: 31 tests passed.
- `git diff --check` — failed only on pre-existing `.ai/task.md` and `AGENTS.md` whitespace/line-ending changes.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed for task files.
- Generated Python `__pycache__` artifacts created by checks were removed.

## Критерии приемки

- Local USD conversion works from synthetic `currency_rates` without external calls — выполнено.
- Contact analytics calculates won revenue USD, profit USD, counts, and dates correctly — выполнено.
- Revenue and profit include only won deals — выполнено.
- ABC full-period and last-12-month classifications are implemented and tested — выполнено.
- Contacts without won sales are classified as `Нет продаж` in test coverage — выполнено.
- RFM and reactivation signals are implemented and tested on synthetic edge cases — выполнено.
- Deal cycle and stale open deal analytics are implemented and tested — выполнено.
- Concentration, type analytics, and region analytics are implemented and tested — выполнено.
- New API endpoints return typed local analytics data and no forbidden fields — выполнено.
- Existing TASK-07 pipeline/API tests continue to pass — выполнено.
- Documentation and `.ai/report.md` reflect the new analytics milestone and note `ui-kits/` as future frontend design-system input — выполнено.
- No real secrets, raw data, databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, generated artifacts, or frontend builds are included in task files — выполнено.

## Факты

- New analytics module: `backend/app/reports/analytics.py`.
- New local report endpoints:
  - `GET /api/reports/contacts/analytics`;
  - `GET /api/reports/abc`;
  - `GET /api/reports/rfm`;
  - `GET /api/reports/stale-deals`;
  - `GET /api/reports/deal-cycle`;
  - `GET /api/reports/concentration`;
  - `GET /api/reports/type-region`;
  - `GET /api/reports/types-regions`.
- Existing `GET /api/reports/contacts` remains available.
- Report endpoints calculate on demand from `normalized_contacts`, `normalized_deals`, and `currency_rates`.
- No Bitrix, NBRB, or external API calls are made.
- Financial analytics use local USD conversion:
  - `amount_usd = amount_original * source_rate_byn / usd_rate_byn`.
- Closed deals use `closed_at` for rate selection; open deals use `created_at`.
- The selected rate is the latest local rate on or before the target date.
- Synthetic currency rates now include 2023-01-01 and 2025-01-01 rows so historical selection is deterministic for the fixture.
- Estimated profit is always `revenue_usd * 0.50`.
- ABC uses the maximum local report date as the default analysis date and compares full period against the previous 12 months.
- RFM includes explicit `Нет продаж` rows for contacts without won deals in the selected period.
- Reactivation is flagged for repeat buyers whose last won deal is older than the local threshold.
- Stale open deals compare open age with the P75 won-deal cycle for the same contact type and fall back to overall P75.
- API response field for latest deal date is `latest_deal_date`; no activity fields are exposed.

## Предположения

- On-demand analytics are acceptable for this milestone before persisted analytics output tables exist.
- Compact response shapes are sufficient for future frontend iteration and can evolve after screen composition is finalized.
- A local reactivation threshold of 365 days is acceptable because the current docs do not define a separate exact threshold.
- The default synthetic analysis date should be derived from local normalized deal data for deterministic tests.
- `GET /api/reports/types-regions` is kept as a compatibility alias for the SPEC naming while `/api/reports/type-region` satisfies the task naming.

## Неизвестное

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual production contact type values, priorities, and region mapping.
- Actual production pipelines, stages, and currencies in Bitrix.
- Final production storage layout, migration strategy, dataset activation mechanics, and Parquet snapshot format.
- Final frontend response-shape needs beyond the current compact local report API.
- Production NBRB missing-rate policy beyond the documented MVP rule.

## Риски или следующий шаг

Next likely backend milestone: plan real Bitrix read-only ingestion and field allowlist discovery, or production storage/dataset activation mechanics for the local pipeline.
