# Отчет: TASK-2026-07-20-04

Статус: done

## Кратко

Исправлены отклоненные части funnel analytics: контракт сортировки Contacts,
порядок и footer таблицы Deals, validation UI для дат создания ABC/КЭВ,
строгая проверка cached category metadata и форматирование затронутого JSX.
Рабочая funnel ingestion, локальный category directory и точное разрешение
`(stage_id, category_id)` сохранены.

## Измененные файлы

- `.ai/report.md`
- `backend/app/reports/analytics.py`
- `backend/tests/test_analytics.py`
- `backend/tests/test_api_local.py`
- `backend/README.md`
- `frontend/src/App.tsx`
- `frontend/README.md`
- `docs/data-model.md`
- `docs/project-status.md`

`.ai/task.md`, `AGENTS.md` и `WORKFLOW.md` имели неизвестные локальные изменения
до начала работы; они не изменялись и не включены в commit.

## Запущенные проверки

- Focused backend:
  `cd backend && env BITRIX_WEBHOOK_URL= /tmp/bitrix-task-04-venv/bin/python -m pytest tests/test_analytics.py tests/test_api_local.py`
  — `63 passed in 95.33s`.
- Complete backend suite из `/tmp`, чтобы локальный repository `.env` не влиял
  на fail-closed auth test:
  `env BITRIX_WEBHOOK_URL= /tmp/bitrix-task-04-venv/bin/python -m pytest -c /mnt/e/Projects/bitrix/backend/pyproject.toml /mnt/e/Projects/bitrix/backend/tests`
  — `149 passed in 113.43s`.
- Первая попытка complete suite из `backend/` дала `148 passed, 1 failed`:
  локальный `.env` заполнил auth settings в тесте отсутствующей конфигурации.
  Изолированный повтор выше прошел полностью.
- Frontend: `cd frontend && npm run build` — passed; Vite собрал production
  bundle, с существующим предупреждением о chunk больше 500 kB.
- Compose: `docker compose config` — passed.
- Production Compose: `docker compose -f docker-compose.prod.yml config` — passed.
- Local operator flow с временным override
  `APP_AUTH_ENABLED=false`, `BITRIX_WEBHOOK_URL=""`:
  `docker compose ... up --build -d`, `/health` — HTTP 200, frontend `/` —
  HTTP 200, затем `docker compose ... down -v` — passed.
- Для browser fixture выполнен только локальный `POST /api/sync/run`; ответ
  подтвердил synthetic pipeline и отсутствие Bitrix calls.
- Headless Chromium:
  `/tmp/task04-pw/node_modules/.bin/playwright test --config=/tmp/task04-playwright.config.js`
  — `1 passed`.

## Browser/operator verification

- Deals: header, первая body row и footer содержат по 12 ячеек; порядок
  `status -> КЭВ -> funnel -> cycle` совпадает; footer показывает успешные,
  открытые и проигранные counts.
- ABC и КЭВ: изменение creation-date drafts не отправляет новый applied report
  request; обратные draft ranges показывают validation; обратные persisted
  applied ranges после reload показывают validation и не запускают query.
- Badges: category учитывается в Contacts и Deals; category плюс обе applied
  creation dates дают три активных фильтра в ABC и КЭВ.
- Malformed cached category с отрицательным ID отклоняется целиком и не
  появляется в funnel selector при недоступном fresh metadata request.

## Safety search

- Поиск Bitrix write patterns в `backend/` и `frontend/` нашел только
  существующий negative test вызова `crm.deal.update`; production write methods
  не добавлены.
- `select: ["*"]` в `backend/` и `frontend/` не найден.
- Поиск committed webhook-like значений нашел только placeholder test URLs;
  секреты, `.env`, базы, snapshots, CSV, `frontend/dist`, `node_modules` и
  `ui-kits/` не включены в изменения.
- Live Bitrix calls не выполнялись. Все test/operator команды запускались с
  пустым `BITRIX_WEBHOOK_URL`; Docker startup не запускал refresh.

## Факты

- `average_check_usd` и `average_cycle_days` присутствуют по одному разу в
  type contract и runtime allowlist, принимаются FastAPI endpoint и покрыты
  asc/desc/null/tie тестами.
- Footer Deals использует backend filter-wide totals до pagination, а не
  visible rows.
- Valid empty category array остается допустимым; malformed input возвращает
  failure и не используется как cache.
- Существующие funnel/date/weighted summary, exact stage/category, safe refresh
  failure и contact `661` regressions входят в полностью прошедший backend suite.

## Предположения

- Нет.

## Неизвестное

- Live Bitrix data намеренно не проверялись по ограничениям задачи.

## Риски или следующий шаг

- В frontend по-прежнему нет repository-level unit-test framework; обязательные
  UI regressions проверены временным Playwright operator test и production build.
- Vite сохраняет существующее предупреждение о размере основного JS chunk; это
  не относится к текущей задаче.
