# Отчет: TASK-2026-06-22-15

Статус: done

## Кратко

Сделал Contacts screen более стабильным рабочим местом для проверки данных:
отключил disruptive background refetch, добавил сохранение состояния таблицы в
browser local storage и добавил фильтр по дате создания сделки.

## Backend

`GET /api/reports/contacts/analytics` получил новые query parameters:

```text
deal_created_from=YYYY-MM-DD
deal_created_to=YYYY-MM-DD
```

Семантика:

- фильтр применяет inclusive range к `_DealFact.created_at.date()`;
- это отдельная семантика от существующих `date_from` / `date_to`, которые
  продолжают использовать report date через `_reporting_date()`;
- metrics/counts/budgets/revenue/profit считаются по deal set после фильтра по
  creation date;
- status filter применяется поверх уже отфильтрованного по creation date deal
  set;
- если creation-date range активен, contacts без matching assigned deals не
  показываются.

Bitrix extraction, normalization, contact selection, currency loading,
manual refresh, ABC/RFM/concentration/type-region reports не менялись.

## Frontend

Persisted state:

- storage key: `bitrix-sales.contacts.v1`;
- fields: `search`, `contactId`, `contactType`, `region`, `status`,
  `dealCreatedFrom`, `dealCreatedTo`, `sort`, `order`, `limit`, `offset`;
- persisted values are validated/coerced before use;
- invalid or incompatible storage falls back to defaults;
- search and contact ID drafts are initialized from restored filters;
- `Сбросить` clears in-memory state and removes the storage key.

Background refetch behavior:

- TanStack Query defaults now use `staleTime: Infinity`;
- `refetchOnMount`, `refetchOnReconnect`, and `refetchOnWindowFocus` are
  disabled;
- manual `Обновить из Bitrix` still invalidates dataset status, filters, and
  contacts;
- explicit retry buttons, filter/sort/date/pagination changes still fetch via
  their query key changes or explicit `refetch()`.

Deal creation date UI:

- added native date inputs labeled `Создана с` and `Создана по`;
- frontend sends `deal_created_from` and `deal_created_to` only when non-empty;
- date changes reset `offset` to `0`;
- invalid range (`from > to`) shows a local validation alert and prevents the
  contacts request until fixed;
- date filters persist across reload and clear on reset.

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
- `frontend/src/main.tsx`
- `frontend/src/styles.css`
- `frontend/README.md`
- `docs/development.md`
- `.ai/report.md`

Pre-existing unstaged local changes in `.ai/task.md`, `AGENTS.md`, and
`WORKFLOW.md` were not made by Codex for this task and were not intentionally
modified.

## Checks

Before implementation:

- `git log --oneline -5` — latest relevant commit was
  `f1b930d planner: TASK-2026-06-22-15 Persist Contacts UI state and add deal creation date filter`.
- `git status --short --branch` — showed pre-existing modified `.ai/task.md`,
  `AGENTS.md`, and `WORKFLOW.md`.

Focused backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_analytics.py tests/test_api_local.py`
  — passed, `25 passed`.

Full backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed, `85 passed`.

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

- Deal creation date filtering uses local `normalized_deals.created_at` through
  `_DealFact.created_at.date()`, not closed date and not `_reporting_date()`.
- Existing `date_from` / `date_to` behavior remains report-date based.
- Persisted UI state stores only filter/sort/page settings, not backend rows,
  secrets, raw payloads, or personal fields.
- No `ui-kits/` files were changed.

## Unknowns

- Browser-level visual verification with a live backend dataset was not run in
  this task. TypeScript/Vite build passed.
- The original source of the user's perceived self-refresh was not isolated;
  the implemented fix disables the disruptive TanStack Query auto-refetch paths
  and persists workspace state across browser reload.

## Risks Or Next Step

If operators later need shareable filter links, the next step should be a
router/query-string state layer. This task intentionally used local storage only
to keep scope focused on the current single-screen app.

No Bitrix calls or write methods were added or called.
