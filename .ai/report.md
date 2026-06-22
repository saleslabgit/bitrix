# Отчет: TASK-2026-06-22-02

Статус: done

## Кратко

Подготовлена безопасная mapping template table для настройки `contact_type_rules`.

Фактические колонки заполнены из:

- Bitrix metadata-only method `crm.contact.fields`;
- локальных DuckDB aggregate counts из активного dataset.

Пользователю нужно заполнить только decision columns:

- `normalized_type`;
- `region`;
- `priority`;
- `is_active`.

Codex не заполнял бизнес-маппинг, не создавал `contact_type_rules`, не запускал sync и не вызывал Bitrix row-listing methods.

## Измененные файлы

- `backend/app/bitrix/contact_type_metadata.py` — helper для извлечения enum option IDs/labels из metadata `crm.contact.fields`.
- `backend/app/reports/contact_type_mapping.py` — helper для локальных aggregate counts по contact type option IDs и raw combinations.
- `backend/tests/test_contact_type_metadata.py` — тесты metadata enum extraction и safe local aggregate logic.
- `docs/data-model.md` — описан metadata/local aggregate mapping helper.
- `docs/development.md` — зафиксирована metadata-only граница для contact type mapping flow.
- `docs/project-status.md` — обновлен текущий следующий шаг.
- `.ai/report.md` — этот отчет и mapping template.

`.ai/task.md` была pre-existing unstaged change and was not staged by Codex. `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, frontend, and `ui-kits/` were not intentionally modified or staged.

## Bitrix Metadata Calls

Called methods:

```text
crm.contact.fields: 1
```

Forbidden methods not called:

```text
crm.contact.list: 0
crm.deal.list: 0
crm.deal.contact.items.get: 0
*.add: 0
*.update: 0
*.delete: 0
```

No Bitrix contact/deal rows, contact/deal IDs, contact/deal names, phones, emails, addresses, messengers, comments, files, activities, webhook URLs, tokens, local absolute paths, generated file contents, or row samples were printed or included in this report.

## Mapping Template

Fill only the `TODO_USER` columns. Factual columns should not be edited unless the source data is re-profiled.

| bitrix_option_id | bitrix_option_label | contacts_count | observed_raw_combinations | normalized_type | region | priority | is_active |
|---:|---|---:|---|---|---|---|---|
| 59 | Подрядчик | 281 | `[151, 59] (6); [1943, 249, 59] (1); [1943, 59] (6); [245, 59] (1); [249, 59, 251] (1); [251, 59] (3); [253, 59] (2); [59, 151] (5); [59, 1943, 253] (1); [59, 1943] (4); [59, 251, 1943] (1); [59, 251, 253] (2); [59, 253] (1); [59, 61] (5); [59, 65] (9); [59] (220); [61, 59, 65] (1); [61, 59] (6); [65, 59] (6)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 61 | Дизайнер / архитектор | 1605 | `[247, 61] (3); [255, 61] (1); [59, 61] (5); [61, 151] (2); [61, 247] (2); [61, 255] (1); [61, 59, 65] (1); [61, 59] (6); [61, 65] (2); [61] (1581); [65, 61] (1)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 65 | Конечный клиент | 1943 | `[1943, 65] (1); [2829, 65] (1); [59, 65] (9); [61, 59, 65] (1); [61, 65] (2); [65, 1943] (1); [65, 247] (1); [65, 59] (6); [65, 61] (1); [65] (1920)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 67 | Поставщик | 109 | `[67, 1945] (1); [67] (108)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 151 | Дилер | 126 | `[151, 59] (6); [151] (112); [1943, 151] (1); [59, 151] (5); [61, 151] (2)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 245 | Другое | 22 | `[245, 59] (1); [245] (21)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 247 | Проектировщик | 51 | `[247, 61] (3); [247] (45); [61, 247] (2); [65, 247] (1)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 249 | Конкурент | 8 | `[1943, 249, 59] (1); [249, 59, 251] (1); [249] (6)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 251 | Дилер РБ | 56 | `[249, 59, 251] (1); [251, 1943] (1); [251, 253] (1); [251, 59] (3); [251] (47); [59, 251, 1943] (1); [59, 251, 253] (2)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 253 | Мастер-класс | 17 | `[251, 253] (1); [253, 59] (2); [253] (10); [59, 1943, 253] (1); [59, 251, 253] (2); [59, 253] (1)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 255 | РФ Дизайнер/Архитектор | 319 | `[255, 61] (1); [255] (317); [61, 255] (1)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 469 | Перевозчик | 53 | `[469] (53)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 1943 | Партнер | 45 | `[1943, 151] (1); [1943, 249, 59] (1); [1943, 59] (6); [1943, 65] (1); [1943] (28); [251, 1943] (1); [59, 1943, 253] (1); [59, 1943] (4); [59, 251, 1943] (1); [65, 1943] (1)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 1945 | маркетинг | 4 | `[1945] (3); [67, 1945] (1)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 2341 | Дилер РФ | 32 | `[2341, 2343] (1); [2341] (29); [2343, 2341] (2)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 2343 | Подрядчик РФ | 31 | `[2341, 2343] (1); [2343, 2341] (2); [2343] (28)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 2345 | Проектировщик РФ | 1 | `[2345] (1)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 2785 | Строители РФ | 8 | `[2785] (8)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |
| 2829 | Прораб РБ | 4 | `[2829, 65] (1); [2829] (3)` | TODO_USER | TODO_USER | TODO_USER | TODO_USER |

## Запущенные проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit before implementation was `0c784e8 planner: TASK-2026-06-22-02 Extract contact type enum labels`.
- `git status --short --branch` — passed. Showed only pre-existing modified `.ai/task.md`.
- `docs/workflow.md` — not found in repository; used root `WORKFLOW.md`.
- `docs/crm_analytics_system_tz.md` — not found in repository; used root `SPEC.md`.

Targeted implementation checks:

- `python -m pytest tests/test_contact_type_metadata.py` from `backend/` — not run: `python` command is absent in this environment.
- temporary backend venv Python `-m pytest tests/test_contact_type_metadata.py` from `backend/` — passed: 2 tests passed.

Metadata/local aggregate extraction:

- Bitrix metadata extraction via `crm.contact.fields` — passed; labels found for all 19 observed option IDs.
- Local DuckDB aggregate extraction from `raw_contacts` — passed; aggregate counts found for all 19 observed option IDs.

Additional checks still to run after report update:

- temporary backend venv Python `-m pytest` from `backend/` — passed: 53 tests passed.
- `python3 -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — passed.
- `git status --short --branch` before staging — passed. Showed TASK-2026-06-22-02 files modified/untracked plus pre-existing unstaged `.ai/task.md`.
- `git diff --stat HEAD` before staging — passed. Included tracked TASK-2026-06-22-02 changes plus pre-existing `.ai/task.md`; untracked new files are not shown by this command before staging.
- `git diff --name-only --cached` before staging — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` before staging — passed with no output.
- `git status --short --branch` after staging — passed. Showed only TASK-2026-06-22-02 files staged and pre-existing `.ai/task.md` unstaged.
- `git diff --stat HEAD` after staging — passed. Included staged TASK-2026-06-22-02 changes plus pre-existing unstaged `.ai/task.md`.
- `git diff --name-only --cached` after staging — passed. Listed only `.ai/report.md`, backend metadata/mapping helpers/tests, and updated docs.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` after staging — passed with no output.
- `git log --oneline -1` after staging — passed. Latest relevant commit remained `0c784e8 planner: TASK-2026-06-22-02 Extract contact type enum labels`.

## Факты

- `UF_CRM_1595304971232` metadata includes labels for all observed option IDs.
- Local aggregate counts exist for all 19 observed option IDs.
- Current active rules are still not created in this task.
- Business decision columns remain `TODO_USER`.
- No forbidden CRM methods were called.

## Предположения

- `contacts_count` counts a contact once per option ID contained in `contact_type_raw`; a contact with a multi-option raw combination contributes to each contained option ID.
- `observed_raw_combinations` are configuration/domain aggregates and are safe to report.

## Неизвестное

- Which labels should be merged into shared `normalized_type` values.
- Region mapping for each option.
- Priority order for analytical contact selection.
- Whether any option should be inactive for normalization.

## Риски или следующий шаг

Next step: user should fill `normalized_type`, `region`, `priority`, and `is_active` in the mapping table. After that, the next task can create/activate `contact_type_rules` and rerun local normalization from persisted data.
