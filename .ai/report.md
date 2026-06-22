# Отчет: TASK-2026-06-22-14

Статус: done

## Кратко

Добавил в Contacts analytics отдельные USD-бюджеты для проверки сделок и
обновил таблицу под бизнес-лейблы пользователя.

`Бюджет` теперь больше не использует won-only `revenue_usd`. Он показывает
сумму всех назначенных contact deals в USD. `Выручка` осталась won-only.

## Backend Fields

В `ContactAnalyticsRow` / `ContactAnalyticsResponse` добавлены поля:

```text
budget_usd
budget_in_work_usd
lost_budget_usd
```

Формулы:

- `budget_usd` — сумма `amount_usd` всех сделок, где
  `analytical_contact_id = contact_id`;
- `budget_in_work_usd` — сумма `amount_usd` open-сделок контакта;
- `lost_budget_usd` — сумма `amount_usd` lost-сделок контакта;
- `revenue_usd` — без изменений, won-only revenue;
- `estimated_profit_usd` — без изменений, `revenue_usd * 0.50`.

Все суммы используют локально нормализованные USD values из report layer. ABC,
RFM, concentration, normalization, refresh, contact selection, and currency
loading behavior не менялись.

Новые budget поля добавлены в server-side sort allowlist:

```text
budget_usd
budget_in_work_usd
lost_budget_usd
```

Sorting остается deterministic с tie-break по `contact_id`.

## Frontend

Таблица Contacts теперь показывает финансовые колонки:

| Label | Source |
|---|---|
| `Бюджет` | `budget_usd` |
| `Бюджет в работе` | `budget_in_work_usd` |
| `Бюджет проигранных` | `lost_budget_usd` |
| `Выручка` | `revenue_usd` |
| `Прибыль` | `estimated_profit_usd` |

Count labels изменены:

| Old | New |
|---|---|
| `Won` | `Успешные` |
| `Open` | `Открытые` |
| `Lost` | `Проигранные` |

Sort behavior изменен:

- first click on a different sortable column sets `order=desc`;
- repeated click on the active column toggles `desc` / `asc`;
- offset still resets to `0`.

Working area layout changed to use the available width inside the app shell.
`page-header`, `toolbar`, `table-card`, and alerts are no longer constrained by
`max-width: var(--grid-desktop-max)`. `.main-panel` keeps small side padding and
the table still uses horizontal scroll.

Existing refresh UX, filters, ID search, reset, dates, and Bitrix `Посмотреть`
links remain in the same screen.

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
- `.ai/report.md`

Pre-existing unstaged local changes in `.ai/task.md`, `AGENTS.md`, and
`WORKFLOW.md` were not made by Codex for this task and were not intentionally
modified.

## Checks

Before implementation:

- `git log --oneline -5` — latest relevant commit was
  `795d08f planner: TASK-2026-06-22-14 Add contact budget breakdown columns`.
- `git status --short --branch` — showed pre-existing modified `.ai/task.md`,
  `AGENTS.md`, and `WORKFLOW.md`.

Focused backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_analytics.py tests/test_api_local.py`
  — passed, `22 passed`.

Full backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed, `82 passed`.

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

- Contacts table remains aggregate contact-level analytics, not a per-deal
  table.
- Budget fields reflect the current report period and assigned local report
  rows used by `list_contact_analytics()`.
- `revenue_usd` remains won-only.
- `estimated_profit_usd` remains `revenue_usd * 0.50`.
- No `ui-kits/` files were changed.

## Unknowns

- Browser-level visual verification with a live backend dataset was not run in
  this task. TypeScript/Vite build passed.

## Risks Or Next Step

The table is intentionally wider after adding all requested budget columns. It
uses full available working width plus horizontal scroll on narrower screens.

No Bitrix write methods were added or called.
