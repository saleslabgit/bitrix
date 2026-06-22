# Отчет: TASK-2026-06-22-28

Статус: done

## Кратко

Добавил viewport-bounded таблицы со sticky headers/bottom controls для Contacts,
Deals и ABC, а также modal chart по won USD revenue выбранного контакта.

## Измененные файлы

- `backend/app/api/models.py`
- `backend/app/main.py`
- `backend/app/reports/analytics.py`
- `backend/tests/test_api_local.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/README.md`
- `docs/data-model.md`
- `docs/development.md`
- `.ai/report.md`

## Backend

- Добавлен local-only endpoint:
  `GET /api/reports/contacts/{contact_id}/won-revenue-series`.
- Query params: optional inclusive `date_from` / `date_to` over
  `normalized_deals.closed_at.date()`.
- Источник данных: `normalized_deals` и существующая `_load_deal_facts()` USD
  conversion logic.
- Endpoint включает только deals with:
  - `analytical_contact_id == contact_id`;
  - `status_group == "won"`;
  - non-null `closed_at`.
- Точки агрегируются по close date ascending. Несколько won deals на одну дату
  суммируются в одной точке.
- Existing contact без matching won deals возвращает empty `points` и нулевые
  totals.
- Missing contact возвращает safe `404`.
- Endpoint не отдает deal names, raw rows, personal fields, local paths,
  webhook values или secrets и не вызывает Bitrix.

## Frontend

- Добавлен `recharts`.
- Contact name в Contacts table стал button-like control.
- Click открывает modal с `role="dialog"` и `aria-modal="true"`.
- Modal показывает contact name, contact ID, period label, total won revenue,
  won deal count и line chart by close date.
- Modal поддерживает loading, error, empty state, close button, backdrop close и
  Escape close.
- Закрытие modal не сбрасывает filters, sorting или pagination.
- Для текущей задачи Contacts `Создана с` / `Создана по` передаются в chart
  request как selected period context и явно подписаны в modal.

## Sticky Tables

- Contacts, Deals и ABC table cards стали flex containers с viewport-bounded
  max height.
- `.table-scroll` теперь скроллит rows по vertical и horizontal axes.
- `thead th` sticky внутри scroll area.
- Pagination находится outside row scroll area и остается видимой внизу card.
- Deals и ABC totals bars остаются outside row scroll area; top/bottom totals
  читаемы при вертикальном скролле rows.
- Contacts/Deals toolbars переведены на wrapping `auto-fit` grid, чтобы фильтры
  не выходили за common desktop viewport.

## Документация

- `docs/development.md` описывает новый endpoint, modal chart period mapping и
  bounded table behavior.
- `docs/data-model.md` описывает contact won revenue series output.
- `frontend/README.md` описывает modal chart и sticky/bounded table behavior.

## Запущенные проверки

Before implementation:

- `git log --oneline -5`
- `git status --short --branch`

Docs:

- Context7 Recharts docs fetched for current `ResponsiveContainer`,
  `LineChart`, `XAxis`, `YAxis`, `Tooltip`, accessibility behavior.

Backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/pytest tests/test_api_local.py`
  — passed, `17 passed`.
- `cd backend && /tmp/bitrix-backend-venv/bin/pytest`
  — passed, `115 passed`.

Frontend:

- `cd frontend && npm run build` — passed.
  Vite reported a bundle-size warning after adding Recharts; build succeeded.
- Re-ran `cd frontend && npm run build` after CSS fixes — passed with the same
  bundle-size warning.

Runtime / browser:

- `docker compose up --build -d` — passed.
- `curl -f http://127.0.0.1:8000/health` — passed.
- New contact revenue endpoint returned `200` for an existing local contact.
- `curl -f http://127.0.0.1:5173/` — passed.
- Playwright desktop smoke at `1366x768`:
  - Contacts table rendered 25 rows;
  - `.table-scroll` had `overflowY: auto`;
  - table header `position: sticky`;
  - table card stayed inside viewport with pagination visible;
  - toolbar stayed inside viewport;
  - clicking a contact name opened an accessible modal;
  - modal rendered summary and SVG chart for a contact with won revenue;
  - browser console had `0` errors.
- `docker compose down -v` — passed.

Safety:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

## Факты

- No Bitrix calls were added to report page load, chart modal, Docker startup,
  or local read endpoints.
- No CRM write methods were added.
- No `ui-kits/` files were changed.
- No secrets, `.env`, local DB files, Parquet snapshots, CSV exports,
  `node_modules`, `frontend/dist`, logs, raw data, or generated data are staged.

## Предположения

- Mapping current Contacts date inputs (`Создана с` / `Создана по`) to chart
  close-date filters is acceptable for this task because the modal labels the
  period explicitly and the backend endpoint already supports true close-date
  parameters.

## Неизвестное

- Mobile visual verification was not run. CSS includes mobile constraints for
  modal height, chart height, and single-column summary, but the Playwright
  smoke was desktop-only.

## Риски или следующий шаг

- Recharts increases the frontend bundle enough for Vite to warn about chunks
  over 500 kB. This is not a functional failure, but future chart-heavy work
  may benefit from code-splitting.
- A later UX task should add explicit Contacts close-date filters if the chart
  period semantics need to be separated from deal creation date filters.
