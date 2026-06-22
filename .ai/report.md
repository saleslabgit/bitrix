# Отчет: TASK-2026-06-22-01

Статус: done

## Кратко

Добавлен локальный safe profile helper и `GET /api/datasets/profile` для агрегированной проверки качества текущего DuckDB dataset. Активный dataset `bitrix-manual` прочитан только из локальной базы. Bitrix live calls в этой задаче не выполнялись.

Профиль подтвердил главный blocker для следующего продуктового решения: активных правил `contact_type_rules` сейчас `0`, поэтому все normalized contacts/deals остаются в `Не определено` по типу и региону. Нужно подтвердить бизнес-маппинг фактических raw значений contact type в normalized type, priority и region.

## Измененные файлы

- `backend/app/reports/profile.py` — новый local-only helper безопасного профилирования dataset.
- `backend/app/api/models.py` — typed response models для profile endpoint.
- `backend/app/main.py` — добавлен `GET /api/datasets/profile`.
- `backend/tests/test_dataset_profile.py` — unit coverage профиля на synthetic/local fixture data, включая empty Bitrix values `False` и `[]`.
- `backend/tests/test_api_local.py` — API coverage и проверка, что profile response не возвращает snapshot paths и forbidden field parts.
- `docs/data-model.md` — описан safe dataset quality profile.
- `docs/development.md` — задокументирован `GET /api/datasets/profile`.
- `docs/project-status.md` — обновлен текущий статус и следующий шаг.
- `.ai/report.md` — этот отчет.

`AGENTS.md`, `.ai/task.md`, `.env`, generated data under `data/` or `backend/data/`, DuckDB files, Parquet snapshots, CSV exports, logs, caches, frontend, and `ui-kits/` were not intentionally modified or staged.

## Active Local Dataset Status

- active dataset name: `bitrix-manual`
- active dataset kind: `bitrix_manual`
- active dataset state: `success`
- latest run dataset name: `bitrix-manual`
- latest run state: `success`
- raw contacts: `14216`
- raw deals: `9142`
- raw links: `8830`
- normalized contacts: `14216`
- normalized deals: `9142`
- snapshot count: `4`
- expected tables: all expected tables exist

No local absolute paths, snapshot identifiers, generated file contents, raw rows, contact names, deal names, contact/deal IDs, webhook URLs, tokens, or private row-level fields were included in this report.

## Contact Type Raw Profile

For profiling, empty Bitrix field representations `False` and `[]` are counted in the `Не заполнено` bucket. This is not a business mapping.

- distinct non-empty raw contact type values: `54`
- contacts missing type: `9592`
- active contact type rules: `0`
- raw values without active rule: `54`

Aggregate raw contact type distribution:

```text
[151, 59]: 6
[151]: 112
[1943, 151]: 1
[1943, 249, 59]: 1
[1943, 59]: 6
[1943, 65]: 1
[1943]: 28
[1945]: 3
[2341, 2343]: 1
[2341]: 29
[2343, 2341]: 2
[2343]: 28
[2345]: 1
[245, 59]: 1
[245]: 21
[247, 61]: 3
[247]: 45
[249, 59, 251]: 1
[249]: 6
[251, 1943]: 1
[251, 253]: 1
[251, 59]: 3
[251]: 47
[253, 59]: 2
[253]: 10
[255, 61]: 1
[255]: 317
[2785]: 8
[2829, 65]: 1
[2829]: 3
[469]: 53
[59, 151]: 5
[59, 1943, 253]: 1
[59, 1943]: 4
[59, 251, 1943]: 1
[59, 251, 253]: 2
[59, 253]: 1
[59, 61]: 5
[59, 65]: 9
[59]: 220
[61, 151]: 2
[61, 247]: 2
[61, 255]: 1
[61, 59, 65]: 1
[61, 59]: 6
[61, 65]: 2
[61]: 1581
[65, 1943]: 1
[65, 247]: 1
[65, 59]: 6
[65, 61]: 1
[65]: 1920
[67, 1945]: 1
[67]: 108
Не заполнено: 9592
```

Raw values currently without active rules:

```text
[151, 59]
[151]
[1943, 151]
[1943, 249, 59]
[1943, 59]
[1943, 65]
[1943]
[1945]
[2341, 2343]
[2341]
[2343, 2341]
[2343]
[2345]
[245, 59]
[245]
[247, 61]
[247]
[249, 59, 251]
[249]
[251, 1943]
[251, 253]
[251, 59]
[251]
[253, 59]
[253]
[255, 61]
[255]
[2785]
[2829, 65]
[2829]
[469]
[59, 151]
[59, 1943, 253]
[59, 1943]
[59, 251, 1943]
[59, 251, 253]
[59, 253]
[59, 61]
[59, 65]
[59]
[61, 151]
[61, 247]
[61, 255]
[61, 59, 65]
[61, 59]
[61, 65]
[61]
[65, 1943]
[65, 247]
[65, 59]
[65, 61]
[65]
[67, 1945]
[67]
```

## Normalization State

- normalized contacts with undefined type: `14216`
- normalized contacts with undefined region: `14216`
- normalized deals with undefined type: `9142`
- normalized deals with undefined region: `9142`
- normalized contacts mostly undefined: `true`
- normalized deals mostly undefined: `true`

Normalized deals by type:

```text
Не определено: 9142
```

Normalized deals by region:

```text
Не определено: 9142
```

Normalized deals by type/region:

```text
Не определено / Не определено: 9142
```

## Deal And Link Integrity

- deals without analytical contact: `312`
- deals without any local link: `312`
- links whose contact is missing from raw contacts: `0`
- links whose deal is missing from raw deals: `0`

## Deal Status, Currency, And Dates

Status group counts:

```text
lost: 4308
open: 3816
won: 1018
```

Currency counts:

```text
BYN: 4803
EUR: 50
RUB: 1256
USD: 3033
```

Deal date ranges:

- created min: `2020-07-28 11:17:29`
- created max: `2026-06-19 15:32:10`
- closed min: `2020-07-28 03:00:00`
- closed max: `2026-06-26 03:00:00`

## Category And Stage Counts

Category/stage counts are reported by IDs only.

```text
0 / 1: 99
0 / 10: 137
0 / 11: 2
0 / 12: 112
0 / 13: 96
0 / 14: 12
0 / 15: 6
0 / 16: 4
0 / 17: 58
0 / 18: 2
0 / 19: 10
0 / 20: 8
0 / 21: 32
0 / 22: 13
0 / 23: 32
0 / 24: 71
0 / 25: 58
0 / 26: 216
0 / 27: 4
0 / 28: 2
0 / 3: 504
0 / 4: 525
0 / 5: 12
0 / 7: 11
0 / 8: 34
0 / 9: 1223
0 / APOLOGY: 291
0 / EXECUTING: 2
0 / FINAL_INVOICE: 2
0 / LOSE: 793
0 / NEW: 18
0 / PREPAYMENT_INVOICE: 2
0 / UC_HA0HCN: 5
0 / WON: 1018
5 / C5:APOLOGY: 1
5 / C5:EXECUTING: 29
5 / C5:LOSE: 460
5 / C5:PREPARATION: 14
5 / C5:UC_1CVW4Q: 9
5 / C5:UC_1HUL1U: 1
5 / C5:UC_80IW4T: 2
5 / C5:UC_9PNI1X: 10
5 / C5:UC_GEQHM0: 6
5 / C5:WON: 156
7 / C7:LOSE: 1937
7 / C7:UC_6LY2X1: 89
7 / C7:UC_861BOR: 2
7 / C7:UC_NGXO5D: 25
7 / C7:UC_NVXPZR: 10
9 / C9:EXECUTING: 3
9 / C9:FINAL_INVOICE: 1
9 / C9:LOSE: 24
9 / C9:UC_0GZD91: 2
9 / C9:UC_5Q260B: 1
9 / C9:UC_9T39SM: 1
9 / C9:UC_UISYO6: 2
9 / C9:WON: 368
11 / C11:EXECUTING: 9
11 / C11:LOSE: 3
11 / C11:PREPARATION: 15
11 / C11:PREPAYMENT_INVOIC: 16
11 / C11:UC_CCBLT9: 87
11 / C11:UC_G15ORZ: 10
11 / C11:UC_IMGQBE: 7
11 / C11:UC_J627NB: 100
15 / C15:FINAL_INVOICE: 31
15 / C15:LOSE: 45
15 / C15:NEW: 45
15 / C15:PREPARATION: 8
15 / C15:PREPAYMENT_INVOIC: 49
15 / C15:UC_8W44UB: 16
15 / C15:UC_CGHSWF: 34
15 / C15:UC_EHNYVP: 42
15 / C15:UC_LCEKYC: 2
17 / C17:EXECUTING: 4
17 / C17:FINAL_INVOICE: 5
17 / C17:NEW: 1
17 / C17:PREPARATION: 5
17 / C17:PREPAYMENT_INVOIC: 13
17 / C17:UC_5CD0QF: 4
17 / C17:UC_S9PYH3: 16
17 / C17:UC_W8VZ81: 8
```

## Запущенные проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit was `5392b4f planner: TASK-2026-06-22-01 Profile live dataset quality`.
- `git status --short` — passed. Showed pre-existing modified `.ai/task.md`.

Implementation checks:

- `python -m pytest tests/test_dataset_profile.py tests/test_api_local.py` from `backend/` — not run: `python` command is absent in this environment.
- `python3 -m pytest tests/test_dataset_profile.py tests/test_api_local.py` from `backend/` — not run: `pytest` is not installed for system `python3`.
- temporary venv Python `-m pytest tests/test_dataset_profile.py tests/test_api_local.py` from `backend/` — passed: 8 tests passed.
- temporary venv Python `-m pytest` from `backend/` — passed: 51 tests passed.
- `python3 -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — passed.
- `docker compose config` from repository root — not run successfully: Docker CLI is not available in this WSL distro.

Local profile inspection:

- Local DuckDB profile read through `get_dataset_profile(get_connection())` — passed.
- No Bitrix client, Bitrix discovery, Bitrix sync, live webhook, or external CRM method was called.

Pre-commit checks before staging:

- `git status --short --branch` — passed. Showed TASK-2026-06-22-01 files modified/untracked plus pre-existing unstaged `.ai/task.md`.
- `git diff --stat HEAD` — passed. Included TASK-2026-06-22-01 tracked changes plus pre-existing `.ai/task.md`; untracked new files are not shown by this command before staging.
- `git diff --name-only --cached` — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.

Final git checks after staging:

- `git status --short --branch` — passed. Showed only TASK-2026-06-22-01 files staged and pre-existing `.ai/task.md` unstaged.
- `git diff --stat HEAD` — passed. Included staged TASK-2026-06-22-01 changes plus pre-existing unstaged `.ai/task.md`.
- `git diff --name-only --cached` — passed. Listed only `.ai/report.md`, backend profile/API/test files, and updated docs.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.

## Факты

- Active local dataset is `bitrix-manual` and latest run state is `success`.
- All expected storage tables exist in the configured local DuckDB database.
- The current live dataset has `14216` raw/normalized contacts and `9142` raw/normalized deals.
- The current live dataset has `8830` local deal-contact links.
- No link points to a missing raw contact or missing raw deal.
- `312` deals have no local link and no analytical contact.
- Active contact type rules count is `0`.
- All normalized contact/deal type and region outputs are currently `Не определено`.
- No Bitrix live calls were made in this task.

## Предположения

- String values `False` and `[]` in `contact_type_raw` represent empty Bitrix field values for profiling purposes.
- Contact type raw aggregate labels are configuration/domain values and are safe to report as counts.

## Неизвестное

- Business meaning of the observed contact type raw option IDs.
- Which raw values should map to each normalized contact type.
- Priority order for analytical contact selection.
- Region mapping for each normalized type.
- Whether multi-value raw contact type combinations should be mapped as combinations or split by a business rule.

## Риски или следующий шаг

Next step: user/business owner should confirm mappings for the observed raw contact type values into `normalized_type`, `priority`, and `region`. After rules are configured, rerun local normalization/profile from persisted data and verify that type/region outputs are no longer mostly `Не определено`.
