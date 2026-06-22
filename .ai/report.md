# Отчет: TASK-2026-06-22-17

Статус: done

## Кратко

Закрыл оставшийся сценарий, где `Тип` мог стать пустым после успешного, но
неконсистентного `/api/meta/filters` response.

TASK-16 был недостаточен, потому что защищал UI от failed metadata request, но
не от HTTP 200 payload с пустым `contact_types`. Такой payload считался свежими
данными и перезаписывал последние options.

## Измененные файлы

- `backend/app/main.py`
- `backend/tests/test_api_local.py`
- `frontend/src/App.tsx`
- `frontend/README.md`
- `.ai/report.md`

## Backend

`GET /api/meta/filters` теперь сравнивает metadata с active dataset state:

- no active dataset: empty metadata still allowed;
- active dataset with `normalized_contacts_count == 0`: empty `contact_types`
  still allowed;
- active successful dataset with `normalized_contacts_count > 0` and empty
  `contact_types`: endpoint raises safe `503 Service Unavailable`.

Safe error detail:

```text
Filter metadata is temporarily unavailable. Keep previous options and retry.
```

The response does not include stack traces, local paths, row samples,
contact/deal names, webhook values, or secrets.

The exact timing source of the user's empty snapshot was not reproduced. The
best-supported diagnosis is a transient successful empty metadata snapshot:
active dataset status still says contacts exist, while the metadata query
returns no contact types. That condition is now rejected by backend and ignored
by frontend.

## Frontend

Metadata validation:

- added `isFilterMetadataValidForDataset()`;
- if active dataset `normalized_contacts_count > 0`, metadata is valid only
  when `contact_types.length > 0`;
- invalid fresh metadata is not used for select options;
- invalid fresh metadata is not saved as last metadata;
- selected `contactType`, `region`, and `status` are not cleared by invalid
  metadata.

Metadata cache:

- added browser storage key `bitrix-sales.filter-metadata.v1`;
- cache stores only safe filter option labels and metadata date range strings;
- stored cache is validated/coerced before use;
- valid fresh metadata replaces state and storage;
- invalid, pending, or failed fresh metadata falls back to the last valid cache;
- normal Contacts filter reset does not delete metadata cache, so dropdowns do
  not disappear after resetting table filters.

User-visible diagnostics:

- failed metadata refresh still shows retry;
- invalid successful metadata shows a warning and retry;
- if cached metadata exists, selects stay usable and alert says filters are
  shown from cache;
- if no valid cache exists, dropdowns remain disabled/empty with the same
  retry path.

Frontend still calls only local backend endpoints:

```text
GET /api/reports/contacts/analytics
GET /api/meta/filters
GET /api/datasets/status
POST /api/local/refresh-data
```

## Документация

`frontend/README.md` now documents the safe metadata cache key:

```text
bitrix-sales.filter-metadata.v1
```

## Запущенные проверки

Before implementation:

- `git log --oneline -5`
- `git status --short`

Backend:

- `cd backend && python -m pytest` — не запустился, system `python`
  отсутствует.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_api_local.py`
  — passed, `11 passed`.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed, `90 passed`.

Frontend:

- `cd frontend && npm run build` — passed.

Safety:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

## Факты

- No Bitrix calls were added.
- No Bitrix write methods were added or called.
- No frontend Bitrix calls were added.
- Report and metadata paths still read local DuckDB-backed data only.
- Extraction, normalization, manual refresh, contact selection, currency
  conversion, and analytics formulas were not changed.
- Existing date draft / `Применить даты` behavior was preserved.
- `ui-kits/` was not changed.

## Предположения

- For an active successful dataset with contacts, empty `contact_types` is an
  invalid transient metadata state, because normalized contacts should always
  have a normalized type such as `Не определено` or a configured type.

## Неизвестное

- Browser-level manual verification was not run. The behavior is implemented at
  React state/cache/query level and TypeScript/Vite build passed.

## Риски или следующий шаг

If this symptom appears again, the next check should inspect backend logs around
dataset replacement timing to identify why the metadata snapshot becomes empty.
The UI and endpoint now treat that snapshot as temporary invalid state instead
of replacing dropdown options.
