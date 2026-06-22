# Отчет: TASK-2026-06-22-12

Статус: done

## Кратко

Исправил класс ошибок DuckDB `executemany requires a non-empty list...` в
manual refresh pipeline.

Теперь пустые batch-вставки не вызываются для нормализации и замены approved
contact type rules, а невозможность загрузить ни одной строки валютных курсов
превращается в безопасную доменную ошибку `ValueError` без технического текста
DuckDB. UI-facing manual refresh уже сохраняет такие ошибки как безопасный
status message и не активирует неполный dataset.

## Implementation

- `normalize_local_data()` больше не вызывает `executemany()` для пустых
  `normalized_contacts` и `normalized_deals`.
- `load_currency_rates_for_raw_deals()` теперь явно останавливается с безопасной
  ошибкой, если raw deals есть, но после расчета нет ни одной строки
  `currency_rates`.
- `replace_contact_type_rules(connection, rules=())` очищает таблицу правил,
  возвращает `0` и не вызывает пустой `executemany()`.
- Manual refresh failure path покрыт тестом: предыдущий активный dataset
  сохраняется, статус становится `error`, сообщение безопасное и не содержит
  `executemany`.

## Production `executemany` Audit

Проверено через `rg "executemany" backend/app`.

- `backend/app/storage/loaders.py` уже использует `_executemany_if_rows()`.
- `backend/app/pipeline/normalization.py` исправлен guard-ами перед вставками.
- `backend/app/pipeline/approved_contact_type_rules.py` исправлен для пустого
  набора правил.
- `backend/app/pipeline/currency_rates.py` теперь не доходит до пустого
  `executemany()` и возвращает безопасную доменную ошибку.
- `backend/app/reports/contact_deal_diagnostics.py` direct-вставки уже имеют
  `if not deals/links: return` и не относятся к normal manual refresh path.

## Tests Added

- Empty raw contacts/deals normalization leaves normalized tables empty.
- Deal without contact links still normalizes as no-contact deal.
- Currency loader raises safe `ValueError` when raw deals exist but no rate rows
  can be inserted.
- Empty approved contact type rules clear the table and return `0`.
- Manual refresh surfaces safe error status for empty currency rows and preserves
  the previous active dataset.

## Changed Files

- `backend/app/pipeline/normalization.py`
- `backend/app/pipeline/currency_rates.py`
- `backend/app/pipeline/approved_contact_type_rules.py`
- `backend/tests/test_pipeline.py`
- `backend/tests/test_live_data_readiness.py`
- `backend/tests/test_api_bitrix.py`
- `.ai/report.md`

Pre-existing unstaged local changes in `.ai/task.md`, `AGENTS.md`, and
`WORKFLOW.md` were not made by Codex for this task and were not intentionally
modified.

## Checks

Before continuing implementation:

- `git status --short --branch` — showed pre-existing modified `.ai/task.md`,
  `AGENTS.md`, and `WORKFLOW.md`, plus task files.

Backend dependencies:

- `python3 -m pip install -e '.[dev]'` — failed because system Python is
  externally managed by PEP 668.
- `python3 -m venv /tmp/bitrix-backend-venv` — passed.
- `/tmp/bitrix-backend-venv/bin/pip install -e '.[dev]'` — passed.

Focused backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_pipeline.py tests/test_live_data_readiness.py tests/test_api_bitrix.py tests/test_bitrix_client.py`
  — passed, `27 passed`.

Full backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed, `76 passed`.

Safety:

- `rg "executemany" backend/app` — completed; production call sites audited as
  listed above.
- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

Frontend:

- Not run. No frontend code changed.

Compose/operator startup:

- Not run. Docker/frontend startup behavior was not changed; Docker Compose
  still starts services only and does not trigger Bitrix refresh automatically.

## Facts

- DuckDB rejects `executemany()` with an empty parameter list.
- Normalization can legitimately produce no rows for empty raw tables.
- Manual refresh can fail during preparation before activating a dataset; that
  path now returns safe status while preserving the previous active dataset.
- The original live UI failure was not reproduced against the user's real data
  in this environment, but the empty-batch failure class and audited production
  call sites are covered by tests.

## Unknowns

- Which exact live input combination triggered the user's UI failure. The
  observed DuckDB error class is covered for known manual refresh production
  insertion points.

## Risks Or Next Step

If live refresh still fails, the next useful artifact is the safe
`/api/datasets/status` or `/api/local/refresh-data` message after this commit.
It should no longer expose raw DuckDB `executemany` text for these empty-row
cases.

No Bitrix write methods were added or called.
