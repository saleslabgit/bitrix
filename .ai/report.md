# Отчет: TASK-2026-06-22-03

Статус: done

## Кратко

Выполнен backend/data-readiness milestone для активного live dataset без нового Bitrix sync:

- user-approved contact type mapping implemented as source-controlled data;
- normalization now resolves Bitrix enum option IDs inside raw combinations like `[61, 59, 65]`;
- missing/empty type normalizes to `Конечный клиент / Без региона / priority 4`;
- inactive/unknown options do not win active normalization or analytical-contact selection;
- local raw tables were not overwritten;
- local normalization was rerun from persisted DuckDB raw tables;
- NBRB read-only rates were loaded into local `currency_rates`;
- live local analytics report paths were smoke-tested.

No Bitrix sync, Bitrix row-listing methods, or Bitrix write methods were called.

## Измененные файлы

- `backend/app/domain/contact_type_resolution.py` — option-ID parsing and active rule resolution.
- `backend/app/domain/contact_selection.py` — analytical contact selection now uses only active resolved rules.
- `backend/app/domain/__init__.py` — exports contact type resolution helpers.
- `backend/app/pipeline/normalization.py` — contact normalization now uses option-ID rule resolution.
- `backend/app/pipeline/approved_contact_type_rules.py` — source-controlled approved live mapping, including `__MISSING__`.
- `backend/app/pipeline/local_refresh.py` — local-only helper to replace rules and rerun normalization.
- `backend/app/pipeline/currency_rates.py` — NBRB read-only currency-rate loader with historical currency metadata periods.
- `backend/app/reports/contact_type_mapping.py` — reuses shared option-ID parser.
- `backend/app/reports/profile.py` — profile rule coverage now understands option-ID rules.
- `backend/tests/test_contact_selection.py` — updated selection semantics.
- `backend/tests/test_live_data_readiness.py` — tests approved mapping, missing type rule, inactive/unknown behavior, and mocked NBRB loading.
- `backend/tests/test_dataset_profile.py` — updated expected analytical-contact gap count under inactive/missing eligibility rules.
- `docs/data-model.md` — documented option-ID rules, missing rule, selection tie-breakers, and NBRB rates.
- `docs/development.md` — documented local readiness helpers.
- `docs/project-status.md` — updated current backend readiness state.
- `.ai/report.md` — this report.

`.ai/task.md` was a pre-existing unstaged planner change and was not staged by Codex. `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, frontend, and `ui-kits/` were not staged.

## Bitrix Calls

Bitrix methods called in this task:

```text
none
```

Forbidden Bitrix methods not called:

```text
crm.contact.list: 0
crm.deal.list: 0
crm.deal.contact.items.get: 0
*.add: 0
*.update: 0
*.delete: 0
```

No Bitrix sync was run. No Bitrix row-listing methods were called. No Bitrix write methods were called.

## Local Rules Applied

- rules stored in `contact_type_rules`: `20`
- active rules: `13`
- missing type source rule: `__MISSING__ -> Конечный клиент / Без региона / priority 4 / active`
- option tie-breaker inside one raw combination: lowest priority number wins; if equal priority, smallest Bitrix option ID wins
- analytical contact tie-breaker after resolved priority: Bitrix primary flag, then smallest contact ID

## Active Dataset Status

- active dataset name: `bitrix-manual`
- active dataset kind: `bitrix_manual`
- active state: `success`
- raw contacts: `14216`
- raw deals: `9142`
- raw links: `8830`
- normalized contacts: `14216`
- normalized deals: `9142`

## Normalization Verification

Normalized contacts by type:

```text
Дизайнер: 1922
Дилер: 212
Конечный клиент: 11514
Не определено: 230
Подрядчик: 292
Проектировщик: 46
```

Normalized contacts by region:

```text
Без региона: 11514
Беларусь: 2086
Не определено: 230
Россия: 386
```

Normalized deals by type:

```text
Дизайнер: 1118
Дилер: 149
Конечный клиент: 7132
Не определено: 487
Подрядчик: 237
Проектировщик: 19
```

Normalized deals by region:

```text
Без региона: 7132
Беларусь: 1349
Не определено: 487
Россия: 174
```

Undefined state:

- contacts with undefined type: `230`
- contacts with undefined region: `230`
- deals with undefined type: `487`
- deals with undefined region: `487`
- contacts mostly undefined: `false`
- deals mostly undefined: `false`

Deal/link integrity after local renormalization:

- deals without analytical contact: `487`
- deals without any local link: `312`
- links whose contact is missing from raw contacts: `0`
- links whose deal is missing from raw deals: `0`

## Currency Rates

Rates were loaded from the official NBRB read-only API into local `currency_rates`.

NBRB endpoint classes used:

```text
exrates/currencies
exrates/rates/dynamics/{Cur_ID}
```

Loaded local rate rows:

```text
BYN: 2020-07-28 -> 2026-06-22, rows 2155, source NBRB
EUR: 2020-07-28 -> 2026-06-22, rows 2155, source NBRB
RUB: 2020-07-28 -> 2026-06-22, rows 2155, source NBRB
USD: 2020-07-28 -> 2026-06-22, rows 2155, source NBRB
```

Total loaded rows: `8620`.

Current limitation: the active raw deals include dates after `2026-06-22`. For those future dates, analytics use the latest loaded local rate on or before the deal date. This matches current report selection behavior and should be refreshed when newer NBRB rates are available.

## Analytics Endpoint Smoke

FastAPI endpoint functions were invoked directly against the configured live local DuckDB connection. Only aggregate counts were inspected.

```text
contacts analytics total: 14216
contacts analytics returned with limit=5: 5
ABC rows: 14216
RFM rows: 14216
stale open deals rows: 3655
deal-cycle overall closed deals: 5314
concentration entries: 3
type report rows: 6
region report rows: 4
type-region matrix rows: 9
```

The concentration report returned positive total revenue. No row-level report items, contact/deal IDs, contact/deal names, personal fields, secrets, local absolute paths, or generated file contents are included here.

## Запущенные проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit before implementation was `157777c planner: TASK-2026-06-22-03 Apply live data rules and rates`.
- `git status --short --branch` — passed. Showed only pre-existing modified `.ai/task.md`.

Implementation checks:

- targeted backend tests with temporary backend venv Python:
  `-m pytest tests/test_contact_selection.py tests/test_live_data_readiness.py tests/test_pipeline.py tests/test_dataset_profile.py tests/test_analytics.py` — passed: 25 tests passed.
- full backend tests with temporary backend venv Python: `-m pytest` — passed: 56 tests passed.
- `python3 -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py` from `backend/` — passed.
- `docker compose config` from repository root — not run successfully: Docker CLI is not available in this WSL distro.

Live/local operations:

- `apply_approved_rules_and_renormalize(get_connection())` — passed.
- `load_currency_rates_for_raw_deals(get_connection())` — passed after adding historical NBRB metadata period support.
- aggregate profile verification from local DuckDB — passed.
- analytics endpoint smoke through `app.main` report functions — passed.

Pre-staging git checks:

- `git status --short --branch` — passed. Showed TASK-2026-06-22-03 files modified/untracked plus pre-existing unstaged `.ai/task.md`.
- `git diff --stat HEAD` — passed. Included tracked TASK-2026-06-22-03 changes plus pre-existing `.ai/task.md`; untracked new files are not shown by this command before staging.
- `git diff --name-only --cached` — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.
- `git status --short --ignored data backend/data` — passed. Showed ignored generated `backend/data/`; generated data was not staged.

Final git checks after staging:

- `git status --short --branch` — passed. Showed only TASK-2026-06-22-03 files staged and pre-existing `.ai/task.md` unstaged.
- `git diff --stat HEAD` — passed. Included staged TASK-2026-06-22-03 changes plus pre-existing unstaged `.ai/task.md`.
- `git diff --name-only --cached` — passed. Listed only `.ai/report.md`, backend domain/pipeline/report/test files, and updated docs.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.
- `git log --oneline -1` — passed. Latest relevant commit remained `157777c planner: TASK-2026-06-22-03 Apply live data rules and rates`.

## Факты

- Approved mapping was implemented exactly as source-controlled `ContactTypeRule` rows.
- Local normalization now parses option IDs from combination strings.
- Missing/empty contact type now normalizes to `Конечный клиент / Без региона`.
- Non-empty raw values with only inactive/unknown options remain `Не определено`.
- Active normalized type/region outputs are no longer mostly undefined.
- Local NBRB rates exist for `BYN`, `EUR`, `RUB`, and `USD` across the active local deal date range through `2026-06-22`.
- No Bitrix sync, row-listing, or write method was called.

## Предположения

- NBRB `exrates/rates/dynamics/{Cur_ID}` official rates are BYN rates for the configured `Cur_Scale`; the loader stores BYN-per-one-currency-unit values.
- The source-controlled `__MISSING__` rule is the canonical representation for missing Bitrix contact type values in local rules.

## Неизвестное

- Whether future production should persist a separate rule label/source column beyond the existing `raw_value` field.
- Whether automatic/scheduled NBRB refresh should be added before deployment.

## Риски или следующий шаг

The backend local dataset is ready for frontend/report integration work. Before production use, add an operator-facing or scheduled refresh path for NBRB rates and decide whether local rule application should become an authenticated API/admin operation.
