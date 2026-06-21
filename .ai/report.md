# Отчет: TASK-2026-06-21-14

Статус: done

## Кратко

Исправлен live Bitrix sync path: normal manual sync больше не вызывает `crm.deal.contact.items.get` по каждой сделке. Deal-contact links строятся локально из downloaded deal fields `CONTACT_ID` и `CONTACT_IDS`. Первый corrected live read-only sync успешно завершился, активировал dataset `bitrix-manual`, записал snapshots и проверил read endpoint counts без вывода raw CRM rows.

## Измененные файлы

- `backend/app/bitrix/allowlist.py` — добавлены safe deal fields `CONTACT_ID` и `CONTACT_IDS` в deal select.
- `backend/app/bitrix/transform.py` — добавлена локальная реконструкция `DealContactLink` из downloaded deal rows; пустые/нулевые contact IDs пропускаются.
- `backend/app/bitrix/ingestion.py` — normal manual ingestion больше не вызывает `client.get_deal_contact_links(deal_id)`.
- `backend/tests/test_bitrix_client.py` — allowlist test покрывает новые deal contact fields.
- `backend/tests/test_bitrix_discovery.py` — metadata fixture обновлен под новые required deal fields.
- `backend/tests/test_bitrix_ingestion.py` — ingestion проходит с fake client без `get_deal_contact_links`; добавлено покрытие локального link construction.
- `SPEC.md` — corrected rule: mass sync builds links locally and must not use per-deal `crm.deal.contact.items.get`.
- `docs/data-model.md` — documented local link reconstruction from `CONTACT_ID`/`CONTACT_IDS`.
- `docs/development.md` — documented that normal manual sync does not mass-call per-deal link API.
- `docs/project-status.md` — updated current state after first successful live sync.
- `.ai/report.md` — this report.

`AGENTS.md`, `.env`, generated data, frontend, and `ui-kits/` were not modified for staging.

## Safe Metadata Inspection

Live metadata inspection used only `crm.deal.fields`.

Safe deal contact-link fields found:

- `CONTACT_ID`: exists.
- `CONTACT_IDS`: exists.

No raw deal/contact rows or field values were printed for this inspection.

## Read-Only Guardrails

Allowed live methods for this task:

- `crm.contact.fields`
- `crm.deal.fields`
- `crm.contact.list`
- `crm.deal.list`
- `crm.status.list`

Normal manual sync now uses:

- `crm.status.list`
- `crm.contact.list`
- `crm.deal.list`

Normal manual sync does not call `crm.deal.contact.items.get`.

No live write methods were called. No live `crm.deal.add`, `crm.deal.update`, `crm.deal.delete`, `crm.contact.add`, `crm.contact.update`, `crm.contact.delete`, or other create/update/delete/write-capable CRM method was called.

No live write-method rejection test was performed against the production webhook.

## Live Methods Actually Called

Across TASK-14 live metadata/discovery/sync checks:

- `crm.deal.fields`
- `crm.contact.fields`
- `crm.status.list`
- `crm.contact.list`
- `crm.deal.list`

Corrected successful sync method counts:

- `crm.contact.fields`: `1`
- `crm.deal.fields`: `1`
- `crm.status.list`: `1`
- `crm.contact.list`: `285`
- `crm.deal.list`: `183`
- `crm.deal.contact.items.get`: `0`

## Discovery Result

Live discovery with configured field:

- state: `success`
- contact fields count: `175`
- deal fields count: `176`
- configured contact type field: `UF_CRM_1595304971232`
- contact type field exists: `true`
- missing required contact fields count: `0`
- missing required deal fields count: `0`

## Sync Result

First corrected manual read-only sync completed successfully.

Safe counts/status:

- sync state: `success`
- sync message: `Manual Bitrix ingestion completed.`
- dataset name: `bitrix-manual`
- dataset kind: `bitrix_manual`
- active dataset name: `bitrix-manual`
- active dataset kind: `bitrix_manual`
- active state: `success`
- latest run state: `success`
- raw contacts count: `14216`
- raw deals count: `9142`
- raw links count: `8830`
- normalized contacts count: `14216`
- normalized deals count: `9142`
- snapshot count: `4`
- contacts read endpoint total: `14216`
- contacts read endpoint returned with `limit=1`: `1`

No raw CRM rows, contact/deal values, webhook URL, token, local DB contents, snapshot contents, phones, emails, addresses, comments, files, or personal fields were printed or included in this report.

## Generated Artifacts

- Local ignored generated directory observed: `backend/data/`.
- Generated local data was not staged.
- `.env` was not staged.
- No DuckDB files, Parquet snapshots, CSV exports, logs, caches, dependency folders, frontend builds, or `ui-kits/` files were staged.

## Запущенные проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit before work:
  `577f133 planner: TASK-2026-06-21-14 Build deal-contact links locally`.
- `git status --short --branch` — passed. Showed only pre-existing modified `.ai/task.md`.

Targeted tests:

- `python -m pytest tests/test_bitrix_client.py tests/test_bitrix_discovery.py tests/test_bitrix_ingestion.py tests/test_api_bitrix.py` from `backend/` — not run: `python` command is absent in this environment.
- `/tmp/bitrix-task-06-venv/bin/python -m pytest tests/test_bitrix_client.py tests/test_bitrix_discovery.py tests/test_bitrix_ingestion.py tests/test_api_bitrix.py` from `backend/` — passed: 14 tests passed.

Syntax/import:

- `python3 -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — passed.

Full tests:

- `/tmp/bitrix-task-06-venv/bin/python -m pytest` from `backend/` — passed: 48 tests passed in 39.84s.

Runtime/config:

- Redacted `docker compose config` from repo root — passed; webhook value was redacted in observed output, contact type field was visible as `UF_CRM_1595304971232`.
- `git status --short --ignored data backend/data` — passed; showed generated `backend/data/` ignored.
- `git status --short --branch` before staging — passed; showed TASK-14 files modified and pre-existing `.ai/task.md` unstaged.
- `git diff --stat HEAD` before staging — passed; showed TASK-14 files plus pre-existing `.ai/task.md`.
- `git diff --name-only --cached` before staging — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` before staging — passed with no output.

Live checks:

- Live deal metadata inspection with `crm.deal.fields` — passed; found `CONTACT_ID` and `CONTACT_IDS`.
- Corrected live discovery — passed.
- First corrected live manual sync — passed and activated `bitrix-manual`.

Final git checks after staging:

- `git status --short --branch` — passed. Showed only TASK-14 files staged and pre-existing `.ai/task.md` unstaged.
- `git diff --stat HEAD` — passed. Included staged TASK-14 changes plus pre-existing unstaged `.ai/task.md` diff.
- `git diff --name-only --cached` — passed. Listed only `.ai/report.md`, `SPEC.md`, backend Bitrix code/tests, and updated docs.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.

## Факты

- Live Bitrix metadata exposes `CONTACT_ID` and `CONTACT_IDS` in deal fields.
- The corrected sync path completed without `crm.deal.contact.items.get`.
- Bitrix contact type field `UF_CRM_1595304971232` exists.
- The first active live dataset is now stored locally under ignored generated storage.

## Предположения

- `CONTACT_ID` represents the primary deal contact when present.
- `CONTACT_IDS` can contain additional linked contacts; extra IDs are stored as non-primary because sort order and role are not available from the normal deal list response.
- Empty, zero, and missing contact IDs are not meaningful links and should be skipped.

## Неизвестное

- Whether Bitrix has deal-contact role/sort metadata available through any safe bulk read path; normal sync currently stores those fields as `NULL`.
- Real contact type/region rule values for analytics configuration.

## Риски или следующий шаг

Next step: inspect the synced dataset quality without exposing personal data, configure contact type/region rules from the approved field values, then plan NBRB currency integration.
