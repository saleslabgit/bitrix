# Отчет: TASK-2026-06-22-22

Статус: done

## Кратко

Добавил won-only `Выручка` в Deals totals и упростил видимые labels totals
bar до:

```text
Бюджет
Выручка
Прибыль
```

## Измененные файлы

- `backend/app/reports/analytics.py`
- `backend/app/api/models.py`
- `backend/tests/test_analytics.py`
- `backend/tests/test_api_local.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/README.md`
- `docs/development.md`
- `docs/data-model.md`
- `docs/project-status.md`
- `.ai/report.md`

## Backend

Deals analytics page response now includes:

```text
filtered_revenue_usd
```

Revenue semantics:

- calculated across all filtered Deals rows before pagination;
- won-only: sums `budget_usd` only for rows where `status_group == "won"`;
- `status=open` and `status=lost` return `0.00` revenue;
- with `status=won`, revenue equals filtered budget for that filtered set.

Existing totals are unchanged:

- `filtered_budget_usd` still sums all filtered deals before pagination;
- `filtered_estimated_profit_usd` remains won-only profit.

No persisted analytics tables or migrations were added. Report endpoint remains
local DuckDB-backed and does not call Bitrix, NBRB, or external services.

## Frontend

`DealTotalsBar` now renders three totals above and below the Deals table:

- `Бюджет`;
- `Выручка`;
- `Прибыль`.

The visible labels no longer include `по фильтру`. Loading, error, invalid-date,
and empty states still do not render stale totals because the totals bar remains
inside the successful non-empty Deals table branch.

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
  — passed, `45 passed`.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed,
  `105 passed`.

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
- Existing Deals budget/profit semantics were preserved.
- `ui-kits/` was not changed.

## Предположения

- Deals `Выручка` means won-only USD revenue for the current filtered Deals set,
  matching project revenue semantics.

## Неизвестное

- Browser visual verification was not run. The UI change is covered by
  TypeScript/Vite build.
- Full `docker compose up --build -d` flow was not run. `docker compose config`
  was verified.

## Риски или следующий шаг

Review should verify in browser that the Deals totals bar shows exactly:
`Бюджет`, `Выручка`, `Прибыль`, both above and below the table.
