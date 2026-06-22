# Отчет: TASK-2026-06-22-29

Статус: done

## Кратко

Исправил regression report workspace width после TASK-28: table card больше не
сжимается в узкую centered card в loading/pending state и занимает всю доступную
ширину main content в loaded state. Пагинация скрыта, пока активный table query
ожидает данные.

## Измененные файлы

- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `.ai/report.md`

## Root Cause

- `.table-card` наследовала shared rule с `.toolbar`: `margin: 0 auto`.
- В flex column auto horizontal margins и отсутствие явной ширины мешали card
  растягиваться по cross axis.
- Loading skeleton/state content мог задавать визуальную ширину shell.
- Пагинация показывалась при готовом dataset даже во время pending table query,
  поэтому на loading screen появлялась misleading page строка.

## Frontend

- `.table-card` теперь явно растягивается по main panel content width:
  `align-self: stretch`, `width: 100%`, `max-width: none`, `margin: 0`.
- `.table-card` сохранила full-height flex behavior, internal overflow и
  bottom pagination layout.
- `.table-scroll` получил explicit `width: 100%` и продолжает быть внутренней
  vertical/horizontal scroll area.
- `.state-panel` и `.skeleton-table` занимают full-width/full-height available
  area внутри card.
- Pagination теперь показывается только когда dataset готов, refresh не идет,
  status/table queries не pending, table query не в error, и active range валиден.

## Сохраненное поведение TASK-28

- Compact top action row сохранен.
- Right filter drawer открывается.
- Sticky headers сохранены.
- Bottom pagination сохранена в loaded state.
- Contact revenue chart modal открывается и рендерит SVG chart.

## Запущенные проверки

Frontend:

- `cd frontend && npm run build` — passed.
  Vite reported the existing Recharts-related bundle-size warning; build
  succeeded.

Runtime / browser:

- `docker compose up --build -d` — passed.
- `curl -f http://127.0.0.1:8000/health` — passed.
- `curl -f http://127.0.0.1:5173/` — passed.
- Playwright desktop smoke at `1366x768`, pending/loading state:
  - skeleton visible;
  - pagination hidden;
  - main panel width `1126px`;
  - table card width `1086px`, matching content width after panel padding;
  - card no longer centered by skeleton content.
- Playwright desktop smoke at `1366x768`, loaded state:
  - 25 table rows rendered;
  - main panel width `1126px`;
  - table card width `1086px`, matching content width after panel padding;
  - card height `676px`, bottom near viewport bottom;
  - `.table-scroll` kept internal vertical overflow;
  - table header `position: sticky`;
  - pagination visible;
  - filter drawer opened.
- Playwright chart smoke:
  - contact modal opened with `aria-modal="true"`;
  - close button present;
  - revenue chart SVG rendered;
  - chart summary rendered;
  - table rows still present behind modal.
- `docker compose down -v` — passed.

Safety:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write method
  was added.

## Факты

- Backend code was not changed.
- No Bitrix calls were added.
- No CRM write methods were added.
- No documentation files needed changes because this is a CSS/layout regression
  fix, not a material workflow or architecture change.
- No `node_modules`, `frontend/dist`, `.playwright-mcp`, local DB files,
  snapshots, logs, raw data, generated data, `.env`, or secrets are staged.

## Предположения

- Treating `.main-panel` padding as available content inset is correct; the card
  fills the content area inside that padding, not the full viewport.

## Неизвестное

- Mobile browser visual verification was not run; the regression and acceptance
  criteria targeted the report workspace width on the desktop operator flow.

## Риски или следующий шаг

- The report shell still shares some visual base rules with `.toolbar`. If more
  workspace-specific card behavior is needed later, separating the shared rule
  into explicit component classes would reduce accidental coupling.
