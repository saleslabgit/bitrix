# Отчет: TASK-2026-06-22-19

Статус: done

## Кратко

Исправил report/runtime проблемы и расширил Deals report:

- reported Contacts analytics query больше не падает на USD deals без локальных
  USD rate rows;
- missing non-USD rates теперь дают safe `503`, а не internal `500`;
- `/favicon.ico` отдается Vite dev server с `200`;
- Deals получил поиск по клиенту;
- Deals показывает filtered budget/profit totals над и под таблицей.

## Измененные файлы

- `backend/app/reports/analytics.py`
- `backend/app/api/models.py`
- `backend/app/main.py`
- `backend/tests/test_analytics.py`
- `backend/tests/test_api_local.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/public/favicon.ico`
- `frontend/README.md`
- `docs/development.md`
- `docs/data-model.md`
- `docs/project-status.md`
- `.ai/report.md`

## Root Cause Contacts 500

Reproduced with a minimal local fixture matching the failing shape: an active
local normalized USD deal exists, but `currency_rates` has no USD row.

Root cause:

- `list_contact_analytics()` calls `_load_deal_facts()`;
- `_load_deal_facts()` converted every deal through `_select_rate()`;
- `_select_rate()` required a local `currency_rates` row even for `USD`;
- for USD deals without a stored USD rate row it raised `ValueError`;
- FastAPI did not catch that analytics data error, so the endpoint returned
  `500 Internal Server Error`.

Fix:

- USD deals no longer require a stored rate row; USD amount is already in target
  currency and uses an identity conversion fallback;
- missing rates for non-USD currencies still do not get guessed;
- missing non-USD rates raise `AnalyticsDataUnavailableError`;
- Contacts and Deals analytics endpoints catch that error and return safe
  `503 Service Unavailable` with a generic retry/refresh message, without stack
  traces, local paths, raw rows, secrets, or forbidden personal fields.

Regression coverage includes the exact reported query shape:

```text
GET /api/reports/contacts/analytics?limit=25&offset=0&sort=contact_id&order=desc
```

## Backend

`GET /api/reports/deals/analytics` now accepts:

- `client_search` over local `normalized_deals.analytical_contact_name`;
- existing deal ID, status, type, region, and created-date filters;
- existing sort/order/limit/offset parameters.

Response now includes page-level filtered totals:

- `filtered_budget_usd`;
- `filtered_estimated_profit_usd`.

Totals are calculated across all filtered rows before pagination. Profit totals
reuse deal-row semantics: won-only `budget_usd * 0.50`, otherwise `0.00`.

No report endpoint calls Bitrix, NBRB, or external services.

## Frontend

Deals filter area now includes `Клиент` search. It is:

- case-insensitive on the backend;
- debounced in the frontend;
- persisted under existing `bitrix-sales.deals.v1`;
- cleared by Deals reset only.

Deals totals are shown above and below the table with labels:

- `Бюджет по фильтру`;
- `Прибыль по фильтру`.

Totals render only after a successful non-empty Deals response. Loading, error,
invalid date, and empty states do not show stale or misleading totals.

Added `frontend/public/favicon.ico`. Verified local Vite returned:

```text
GET /favicon.ico -> 200 image/x-icon
```

The React DevTools console line is expected in Vite/React development mode and
was not suppressed.

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
  — passed, `41 passed`.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed,
  `101 passed`.

Frontend:

- `cd frontend && npm run build` — passed.
- repeated `cd frontend && npm run build` — passed.

Operator/safety:

- `docker compose config` — passed.
- sandboxed `cd frontend && npm run dev -- --host 127.0.0.1` — failed with
  `listen EPERM`, then rerun with escalation.
- escalated `cd frontend && npm run dev -- --host 127.0.0.1` — started on
  `http://127.0.0.1:5174/` because 5173 was already in use.
- `curl -sS -o /tmp/bitrix-favicon-check -w '%{http_code} %{content_type} %{size_download}\n' http://127.0.0.1:5174/favicon.ico`
  — `200 image/x-icon 290`.
- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

## Факты

- Frontend still calls only local backend endpoints.
- Backend report endpoints read local DuckDB-backed data only.
- No Bitrix calls were added to report page load paths.
- No Bitrix write methods were added.
- No forbidden personal fields were added to response models or UI.
- `ui-kits/` was not changed.

## Предположения

- `поиск по клиентам` means local analytical contact/client name from
  `normalized_deals.analytical_contact_name`, not phone/email/address or any
  other personal/raw Bitrix field.

## Неизвестное

- Full browser click-through of Contacts and Deals was not performed. The
  frontend build passed and `/favicon.ico` was verified through Vite.
- Full `docker compose up --build -d` flow was not run. Compose config was
  verified; local frontend dev server was started directly for favicon
  verification.

## Риски или следующий шаг

Review should verify in browser against a prepared local dataset:

- Contacts loads with `sort=contact_id&order=desc`;
- Deals client search filters by displayed analytical client;
- Deals totals remain unchanged while moving between pages;
- Deals totals change when filters change.
