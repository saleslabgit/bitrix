# Отчет: TASK-2026-06-22-21

Статус: done

## Кратко

Связал Contacts deal counters с Deals report и временно скрыл region UI на
frontend.

`TASK-2026-06-22-20 Stabilize filter metadata endpoint` был отменен
пользователем и в этой задаче не реализовывался.

## Измененные файлы

- `backend/app/reports/analytics.py`
- `backend/app/main.py`
- `backend/tests/test_analytics.py`
- `backend/tests/test_api_local.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/README.md`
- `docs/development.md`
- `docs/data-model.md`
- `docs/project-status.md`
- `.ai/report.md`

## Backend

`GET /api/reports/deals/analytics` теперь принимает:

```text
client_id
```

Семантика:

- `client_id` фильтрует по локальному
  `normalized_deals.analytical_contact_id` через существующий deal facts path;
- фильтр локальный, без Bitrix/NBRB/external calls;
- `client_id` компонуется с `status`, `contact_type`, date range, sorting,
  pagination и filtered totals;
- если переданы и `client_id`, и `client_search`, exact `client_id` имеет
  приоритет, а fuzzy search не отсекает exact-client rows.

Добавлены тесты на exact client filter, status composition, totals before
pagination и приоритет `client_id` над `client_search`.

## Frontend

Contacts table:

- non-zero `Всего сделок` открывает Deals с exact client filter и без status;
- non-zero `Успешные` открывает Deals с exact client filter и `won`;
- non-zero `Открытые` открывает Deals с exact client filter и `open`;
- non-zero `Проигранные` открывает Deals с exact client filter и `lost`;
- zero counters rendered as muted text, not clickable actions;
- buttons are keyboard-accessible native buttons;
- existing Bitrix contact detail links remain unchanged.

Deals navigation state:

- click from Contacts resets unrelated old Deals filters;
- sets hidden `clientId` for exact backend filtering;
- sets visible `Клиент` input to clicked contact name;
- resets Deals pagination to first page through `initialDealFilters`;
- keeps default Deals sort from `initialDealFilters`;
- manual edit of the `Клиент` input clears hidden exact `clientId` and returns
  to fuzzy `client_search` behavior.

Region UI:

- Contacts region filter hidden;
- Deals region filter hidden;
- Contacts region column hidden;
- Deals region column hidden;
- frontend selected-filter counts no longer include region;
- frontend no longer sends `region` query params for Contacts or Deals;
- old persisted region values in localStorage are ignored;
- old persisted `region_normalized` sort values fall back to visible default
  sort because frontend sort allowlists no longer include region.

Backend region fields/query support and storage schema were not removed.

## Документация

Обновлены:

- `frontend/README.md`;
- `docs/development.md`;
- `docs/data-model.md`;
- `docs/project-status.md`.

## Запущенные проверки

Before implementation:

- `git log --oneline -5`
- `git status --short --branch`

Backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/python -m compileall app` —
  passed.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_analytics.py tests/test_api_local.py`
  — passed, `44 passed`.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed,
  `104 passed`.

Frontend:

- `cd frontend && npm run build` — passed.
- repeated `cd frontend && npm run build` — passed.

Operator/safety:

- `docker compose config` — passed.
- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

## Факты

- Frontend still calls only local backend endpoints.
- Backend report endpoints read local DuckDB-backed data only.
- No Bitrix calls were added to report page load paths.
- No Bitrix write methods were added.
- No forbidden personal fields were added to response models or UI.
- Region backend support remains in place for later use.
- `ui-kits/` was not changed.

## Предположения

- Exact Contacts-to-Deals navigation should use local analytical contact ID
  rather than client name to avoid ambiguity when display names collide.

## Неизвестное

- Browser click-through verification was not run. The behavior is implemented at
  React state/query level and TypeScript/Vite build passed.
- Full `docker compose up --build -d` flow was not run. `docker compose config`
  was verified.

## Риски или следующий шаг

Review should verify in browser against a prepared local dataset:

- click each non-zero Contacts counter type;
- confirm Deals `Клиент` shows the contact name;
- confirm Deals request uses `client_id`;
- manually edit Deals `Клиент` and confirm fuzzy search is used;
- confirm region filters/columns are not visible.
