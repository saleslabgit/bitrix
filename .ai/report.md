# Отчет: TASK-2026-06-22-24

Статус: done

## Кратко

Исправил направление ABC transition для нового ABC analytics report:

```text
ABC было -> ABC стало
```

Root cause: предыдущая реализация считала переход как
`comparison segment -> current segment`, из-за чего потеря клиента могла
выглядеть как рост.

## Измененные файлы

- `backend/app/reports/analytics.py`
- `backend/app/api/models.py`
- `backend/app/main.py`
- `backend/tests/test_analytics.py`
- `backend/tests/test_api_local.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `docs/development.md`
- `docs/data-model.md`
- `docs/project-status.md`
- `frontend/README.md`
- `.ai/report.md`

## Backend

`GET /api/reports/abc/analytics` теперь использует явные роли периодов:

- `date_from` / `date_to` — source/base period, `Было`;
- `compare_date_from` / `compare_date_to` — target/result period, `Стало`.

Response shape переименован с ambiguous `current_*` / `compare_*` на:

- `base_*`;
- `target_*`.

Семантика:

- `segment_change = base_segment -> target_segment`;
- `migration_priority = priority(base_segment, target_segment)`;
- `segment_changed = base_segment != target_segment`;
- без `Стало` отчет остается single-period ABC по `Было`;
- с `Стало` включаются клиенты с won revenue в любом из двух периодов.

Добавлен mapping:

```text
C -> Нет продаж = наблюдать
```

Loss transitions больше не могут стать `развивать` или `закрепить`.

Legacy `GET /api/reports/abc` не менялся.

## Frontend

ABC UI labels теперь явно показывают направление:

- `Было с`;
- `Было по`;
- `Стало с`;
- `Стало по`;
- `Выручка было`;
- `ABC было`;
- `Выручка стало`;
- `ABC стало`.

Состояние `bitrix-sales.abc.v1` сохранено. Старые persisted sort fields,
например `current_revenue_usd`, больше не входят в allowlist и безопасно
fallback-ятся к default `base_revenue_usd`.

Contacts и Deals не изменялись по поведению. Region filters/columns в ABC не
добавлялись.

## Документация

Обновлены:

- `docs/development.md`;
- `docs/data-model.md`;
- `docs/project-status.md`;
- `frontend/README.md`.

## Запущенные проверки

Before implementation:

- `git log --oneline -5`
- `git status --short --branch`

Backend focused:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_analytics.py tests/test_api_local.py`
  — passed, `51 passed`.

Backend full:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest` — passed,
  `111 passed`.

Frontend:

- `cd frontend && npm run build` — passed.

Operator/safety:

- `docker compose config` — passed.
- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write
  method was added.

## Факты

- Backend ABC analytics endpoint still reads local DuckDB-backed data only.
- Frontend ABC screen still calls only `/api/reports/abc/analytics`.
- No Bitrix calls were added to report page load paths.
- No Bitrix write methods were added.
- No forbidden personal fields were added to response models or UI.
- `ui-kits/` was not changed.

## Предположения

- Existing query parameter names remain acceptable for compatibility as long as
  UI and response semantics clearly describe `Было` / `Стало`.

## Неизвестное

- Browser visual verification was not run. The UI change is covered by
  TypeScript/Vite build.
- Full `docker compose up --build -d` and HTTP smoke check were not run.
  `docker compose config` was verified.

## Риски или следующий шаг

Review should verify in browser that a customer with old `A` and no target
revenue is shown as `A -> Нет продаж` with priority `срочно`.
