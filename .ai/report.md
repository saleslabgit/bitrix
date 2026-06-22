# Отчет: TASK-2026-06-22-13

Статус: done

## Кратко

Улучшил существующий Contacts screen для быстрой проверки локальных Bitrix
данных после refresh.

Теперь таблица поддерживает server-side сортировку до pagination, точный поиск
по contact ID, надежный reset всех фильтров, ссылку `Посмотреть` на карточку
контакта в Bitrix, колонку `Дата закрытия` по `last_won_date` и колонку
`Бюджет USD` по `revenue_usd`.

## Backend Behavior

`GET /api/reports/contacts/analytics` расширен параметрами:

- `contact_id` — exact positive contact ID filter;
- `sort` — allowlisted sort field;
- `order` — `asc` / `desc`.

Allowed sort fields:

```text
contact_id
contact_name
contact_type_normalized
region_normalized
total_deals_count
won_deals_count
open_deals_count
lost_deals_count
revenue_usd
estimated_profit_usd
last_won_date
latest_deal_date
```

Sorting applies in the Python report layer before slicing by `offset`/`limit`.
Tie-break is always `contact_id` ascending for deterministic output. Unsupported
sort/order values are rejected safely by the report function and FastAPI type
validation for the HTTP path.

## Frontend Behavior

- Added compact `ID контакта` input near text search. It keeps only digits and
  sends `contact_id` only when non-empty.
- Added sortable table header buttons for visible verification columns.
- Clicking a header toggles `asc`/`desc`, updates `sort`/`order`, and resets
  `offset` to `0`.
- Reset now clears text search draft, contact ID draft/filter, type, region,
  status, pagination offset, and invalidates the contacts query.
- Contact ID is shown in its own compact column with:

```text
https://dialar.bitrix24.by/crm/contact/details/{contact_id}/
```

  The link opens in a new tab with `rel="noopener noreferrer"`.
- `Бюджет USD` displays `revenue_usd`. The previous `Выручка USD` label was
  replaced to avoid duplicate/confusing financial columns.
- `Дата закрытия` displays `last_won_date`, with `—` when absent.
- `Расчетная прибыль USD`, deal counts, and `Последняя сделка` remain visible.
- Existing refresh, loading, error, empty, and pagination states remain intact.

Frontend still calls only local backend endpoints:

```text
GET /api/reports/contacts/analytics
GET /api/meta/filters
GET /api/datasets/status
POST /api/local/refresh-data
```

No frontend Bitrix calls were added.

## Changed Files

- `backend/app/reports/analytics.py`
- `backend/app/main.py`
- `backend/tests/test_analytics.py`
- `backend/tests/test_api_local.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/README.md`
- `docs/development.md`
- `.ai/report.md`

Pre-existing unstaged local changes in `.ai/task.md`, `AGENTS.md`, and
`WORKFLOW.md` were not made by Codex for this task and were not intentionally
modified.

## Checks

Before implementation:

- `git log --oneline -5` — latest commit was
  `421304d planner: TASK-2026-06-22-13 Improve Contacts verification UI`.
- `git status --short --branch` — showed pre-existing modified `.ai/task.md`,
  `AGENTS.md`, and `WORKFLOW.md`.

Focused backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_analytics.py tests/test_api_local.py`
  — passed, `20 passed`.

Full backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed, `80 passed`.

Frontend:

- `cd frontend && npm run build` — passed.

Safety:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

Compose/operator startup:

- Not run. Docker startup behavior was not changed. Docker Compose still starts
  services only and does not automatically call Bitrix or refresh local data.

## Facts

- Contacts analytics remains aggregate contact-level data, not a per-deal table.
- `Дата закрытия` uses existing `last_won_date`.
- `Бюджет USD` uses existing `revenue_usd`, not original-currency totals.
- Sorting/filtering use local backend analytics data only.
- The Bitrix link is a plain external contact details link and does not call
  Bitrix from frontend code.

## Unknowns

- Browser-level visual verification with a live backend dataset was not run in
  this task. TypeScript/Vite build passed.

## Risks Or Next Step

If the dense table feels too wide on smaller laptop screens, the next UI-only
adjustment should be column priority/compact display. Current implementation
keeps all requested verification columns and relies on horizontal table scroll.

No Bitrix write methods were added or called.
