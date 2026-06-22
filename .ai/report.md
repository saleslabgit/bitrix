# Отчет: TASK-2026-06-22-16

Статус: done

## Кратко

Исправил стабильность фильтров Contacts:

- backend metadata helper теперь безопасен для прямого вызова, пустой локальной
  схемы, таблиц без строк, сделок без `closed_at` и старых/грязных локальных
  таблиц с `NULL` в distinct-значениях фильтров;
- frontend хранит последний успешный `/api/meta/filters` response и не стирает
  dropdown options при transient metadata error;
- date inputs для даты создания сделки теперь редактируются как drafts и
  применяются к активному query state только после явного `Применить даты`.

## Измененные файлы

- `backend/app/reports/local.py`
- `backend/tests/test_api_local.py`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `.ai/report.md`

## Backend

`get_filter_metadata()` теперь вызывает `initialize_schema(connection)` сам.
Это закрывает прямые вызовы helper на новом DuckDB connection без
предварительной подготовки схемы.

Distinct-списки `contact_types`, `regions`, `statuses` теперь отбрасывают
`NULL` и пустые строки перед построением response. Это защищает
`FilterMetadataResponse`, где эти поля типизированы как строки, от validation
500 на старых или частично подготовленных локальных таблицах.

Проверенные metadata states:

- прямой вызов helper на новом in-memory DuckDB без схемы;
- endpoint `meta_filters()` до подготовки dataset;
- пустые contacts и одна open-сделка с `closed_at = NULL`;
- nullable older-local-schema таблицы с `NULL` в distinct metadata columns;
- synthetic dataset после локального sync.

Report APIs продолжают читать только локальные DuckDB-backed таблицы. Bitrix и
NBRB вызовы в metadata/report path не добавлялись.

## Frontend

Dropdown metadata:

- добавлен `lastFilterMetadata`;
- при успешном metadata fetch последнее значение сохраняется в state;
- select options берутся из `filterQuery.data ?? lastFilterMetadata`;
- metadata error по-прежнему показывает alert с retry;
- если успешной metadata загрузки еще не было, dropdowns остаются пустыми и
  disabled;
- если успешная metadata уже была, transient error больше не очищает options и
  не сбрасывает выбранные `contactType`, `region`, `status`.

Deal creation dates:

- добавлены draft values для `dealCreatedFrom` и `dealCreatedTo`;
- `onChange` date inputs меняет только drafts;
- активные `filters.dealCreatedFrom` / `filters.dealCreatedTo` меняются только
  кнопкой `Применить даты`;
- кнопка активна только когда draft отличается от active filters, даты пустые
  или полные `YYYY-MM-DD`, и диапазон не инвертирован;
- применение дат сбрасывает `offset` в `0`;
- `Сбросить` очищает drafts, active filters, persisted state и invalidates
  contacts query;
- applied dates продолжают сохраняться в `localStorage`.

Frontend still calls only local backend endpoints:

```text
GET /api/reports/contacts/analytics
GET /api/meta/filters
GET /api/datasets/status
POST /api/local/refresh-data
```

## Root Causes / Diagnosis

Empty dropdowns:

- frontend used `filterQuery.data?.contact_types ?? []`,
  `filterQuery.data?.regions ?? []`, and `filterQuery.data?.statuses ?? []`
  directly;
- when metadata refetch failed without usable current data, options collapsed to
  empty arrays and dropdowns were disabled on `filterQuery.isError`.

`/api/meta/filters` 500:

- direct helper calls were not self-contained and relied on callers to
  initialize DuckDB schema first;
- a second realistic failure mode was response validation when older or
  partially prepared local normalized tables contained `NULL` distinct values
  for metadata option columns, while `FilterMetadataResponse` requires strings.

Date input refetches:

- date inputs wrote directly into active `filters.dealCreatedFrom` and
  `filters.dealCreatedTo` on every `onChange`;
- those fields are part of the Contacts query key, so in-progress date edits
  could trigger backend table requests.

## Запущенные проверки

Before implementation:

- `git log --oneline -5`
- `git status --short`

Backend:

- `cd backend && python -m pytest tests/test_api_local.py` — не запустился,
  system `python` отсутствует.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_api_local.py`
  — passed, `10 passed`.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed, `89 passed`.

Frontend:

- `cd frontend && npm run build` — passed.

Safety:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

## Факты

- No Bitrix calls were added.
- No Bitrix write methods were added or called.
- No extraction, normalization, manual refresh, contact selection, currency
  conversion, or report metric semantics were changed.
- `ui-kits/` was not changed.
- Docker/operator startup was not changed, so Compose flow was not run.

## Предположения

- User-reported periodic metadata 500 is covered by the now-tested local
  metadata edge cases: unprepared/direct helper state and `NULL` metadata
  values from older/dirty local normalized tables.

## Неизвестное

- Browser-level manual verification was not run. TypeScript/Vite build passed,
  and the date behavior is implemented at React state/query-key level.

## Риски или следующий шаг

If operators want date picker selection to apply without a button, the next
iteration should add browser-level tests for target browsers first. This task
uses explicit apply to avoid native `type="date"` partial-input differences.
