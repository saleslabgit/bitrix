# Отчет: TASK-2026-06-22-18

Статус: done

## Кратко

Добавил локальный Deals report: backend endpoint с deal-level аналитикой,
frontend экран Deals рядом с Contacts, отдельное состояние фильтров/сортировки,
документацию и тесты.

## Измененные файлы

- `backend/app/reports/analytics.py`
- `backend/app/api/models.py`
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
- `README.md`
- `.ai/report.md`

## Backend

Добавлен `GET /api/reports/deals/analytics`.

Параметры:

- `limit`, `offset`;
- exact `deal_id`;
- `status`;
- `contact_type`;
- `region`;
- inclusive `deal_created_from` / `deal_created_to`;
- allowlisted `sort` и `order`.

Ответ содержит `total`, `limit`, `offset`, `items`, где row включает:
`deal_id`, `deal_name`, `status_group`, `contact_type_normalized`,
`region_normalized`, `budget_usd`, `estimated_profit_usd`, `created_date`,
`closed_date`.

Семантика денег:

- `budget_usd` — USD amount конкретной сделки;
- `estimated_profit_usd` — won-only: `budget_usd * 0.50` для `won`, иначе
  `0.00`.

Сортировка стабильная и детерминированная, с final tie-breaker по `deal_id`.
`NULL` closed dates не ломают сортировку.

Endpoint читает только локальные DuckDB-backed normalized deals через уже
существующий `_load_deal_facts()`. Новые таблицы, миграции, Bitrix calls, NBRB
calls или внешние запросы не добавлялись.

## Frontend

Добавлен экран Deals:

- переключение Contacts / Deals в sidebar;
- общий dataset status/manual refresh flow;
- общий защищенный metadata cache `bitrix-sales.filter-metadata.v1`;
- отдельный storage key для Deals: `bitrix-sales.deals.v1`;
- фильтры exact deal ID, status, type, region, created date range с draft state
  и `Применить даты`;
- sortable table columns: ID/link, deal name, status, type, region, budget,
  profit, created date, closed date;
- pagination, loading, error, empty, reset, selected-filter-count states.

Contacts behavior сохранен. Reset Contacts и Reset Deals очищают только state
соответствующего отчета и не удаляют cached metadata options.

Frontend по-прежнему вызывает только локальные backend endpoints:

```text
GET /api/reports/contacts/analytics
GET /api/reports/deals/analytics
GET /api/meta/filters
GET /api/datasets/status
POST /api/local/refresh-data
```

Прямых Bitrix API calls во frontend не добавлено. Ссылки ведут только на
карточки контактов/сделок в Bitrix UI.

## Документация

Обновлены:

- `frontend/README.md`;
- `docs/development.md`;
- `docs/data-model.md`;
- `docs/project-status.md`;
- `README.md`.

## Запущенные проверки

Перед реализацией:

- `git log --oneline -5`
- `git status --short`

Backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/python -m compileall app` —
  passed.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_analytics.py tests/test_api_local.py`
  — passed, `36 passed`.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed,
  `96 passed`.

Frontend:

- `cd frontend && npm run build` — passed.
- повторно `cd frontend && npm run build` — passed.

Operator/safety:

- `docker compose config` — passed.
- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

## Факты

- No Bitrix write methods were added.
- No backend report endpoint calls Bitrix, NBRB, or external services.
- No frontend Bitrix API calls were added.
- Deal analytics are calculated on demand from local normalized deals and local
  currency rates.
- `ui-kits/` was not changed.
- Local/generated build output was not staged.

## Предположения

- Existing `/api/meta/filters` remains the shared metadata source for Contacts
  and Deals. It provides statuses/date ranges from local deals and type/region
  options from normalized contacts.

## Неизвестное

- Browser-level manual verification was not run.
- Full `docker compose up --build -d` flow was not run in this session. The
  Compose frontend command runs dependency installation inside the container and
  may require network access; local Compose configuration also reads local
  environment settings. `docker compose config` was verified instead.

## Риски или следующий шаг

Next review should click through both reports against a prepared local dataset:
switch Contacts/Deals, apply deal ID/status/type/region/date filters, sort
budget/profit/date columns, and verify pagination plus Bitrix detail links.
