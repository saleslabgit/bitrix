# Отчет: TASK-2026-07-20-01

Статус: done

## Кратко

Добавлено локальное чтение утвержденного Bitrix-поля сделки
`UF_CRM_1716895716`, его явное преобразование в `kev_held: bool`, безопасная
аддитивная миграция существующей DuckDB и отчет, сравнивающий конверсию
закрытых сделок с проведенным КЭВ и без него. Добавлены API-фильтр и колонка КЭВ
в отчете по сделкам, а также отдельный frontend-экран `КЭВ`.

## Измененные файлы

- `backend/app/bitrix/allowlist.py`
- `backend/app/bitrix/transform.py`
- `backend/app/domain/models.py`
- `backend/app/storage/schema.py`
- `backend/app/storage/loaders.py`
- `backend/app/storage/snapshots.py`
- `backend/app/pipeline/normalization.py`
- `backend/app/pipeline/synthetic_dataset.py`
- `backend/app/reports/analytics.py`
- `backend/app/api/models.py`
- `backend/app/main.py`
- релевантные backend-тесты
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `backend/README.md`
- `frontend/README.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/project-status.md`
- `.ai/report.md`

## Что сделано

- Добавлена константа `UF_CRM_1716895716` и только явные разрешенные варианты
  поля для traditional и universal CRM deal select. Read-only allowlist методов
  не расширялся, `select: ["*"]` не добавлялся.
- Добавлен небольшой явный parser checkbox-значений. Missing/blank, false, zero,
  `N`, `NO`, `FALSE` и неожиданные значения дают `false`; true, ненулевые числа,
  `Y`, `YES`, `TRUE` дают `true`. Сырой Bitrix payload не попадает в API/UI.
- `kev_held` проведен через domain snapshot, raw loader, raw/normalized DuckDB,
  normalization, Parquet snapshot allowlist и synthetic fixture.
- `initialize_schema()` теперь идемпотентно добавляет в существующие
  `raw_deals` и `normalized_deals` колонку
  `BOOLEAN NOT NULL DEFAULT false`, сохраняя строки. Для нового файла колонка
  создается сразу.
- `GET /api/reports/deals/analytics` возвращает `kev_held` и поддерживает точный
  фильтр `kev_held=true|false`. В Deals добавлены колонка `КЭВ`, значения
  `Был`/`Не был` и фильтр `Все`/`Был`/`Не был`.
- Добавлен локальный typed endpoint
  `GET /api/reports/kev-conversion/analytics` с inclusive-фильтрами по
  `closed_at` и optional `contact_type`. Он считает только won/lost сделки,
  исключает open и строки без `closed_at`, возвращает обе группы, nullable
  conversion и nullable разницу в процентных пунктах.
- Добавлен экран `КЭВ` с отдельным browser-storage key, фильтрами периода
  закрытия и типа контакта, компактной таблицей сравнения, разницей в п.п.,
  loading/error/retry/empty/no-denominator states и сохранением auth behavior.
- Документация фиксирует семантику blank = КЭВ не был, формулу
  `won / (won + lost) * 100`, использование `closed_at`, аддитивную миграцию и
  обязательное ручное `Обновить из Bitrix` после deployment.

## Запущенные проверки

- `git log --oneline -5` и `git status --short` — выполнены до изменений.
  Существовавшие локальные изменения в `.ai/task.md`, `AGENTS.md` и
  `WORKFLOW.md` сохранены и не относятся к staging этого задания.
- `cd backend && python -m pytest` — системный Python не содержит `pytest`.
- `docker run --rm -v /mnt/e/Projects/bitrix/backend:/app -w /app bitrix-backend sh -c 'pip install -e ".[dev]" >/tmp/pip.log && python -m pytest'`
  — passed: `144 passed in 116.90s`.
- Полный backend suite покрывает новый schema, file-backed migration предыдущей
  schema с сохранением строк, checked/blank и alias payload variants,
  won/lost/open grouping, inclusive close-date filters, zero denominators, Deals
  boolean filtering и regression существующего analytical contact assignment.
- `cd frontend && npm run build` — passed. Vite оставил существующее
  предупреждение о chunk больше 500 kB; build завершен успешно.
- `docker compose config` — passed.
- `docker compose -f docker-compose.prod.yml config` — passed.
- `docker compose up --build -d` — passed; запуск поднял только сервисы и не
  инициировал refresh.
- `curl -f http://localhost:8000/health` — passed.
- `curl -f http://localhost:5173/` — passed.
- Browser-facing проверка загрузила frontend и ожидаемый login screen при
  включенной локальной auth-конфигурации.
- `docker compose down -v` — passed; временный runtime был остановлен.
- Отдельная локальная проверка на synthetic dataset вызвала только
  `/api/sync/run`; endpoint подтвердил `No Bitrix calls were made`, загрузил 10
  contacts и 30 deals. Временный контейнер после проверки остановлен.
- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src docs`
  — найден только существующий negative test с `crm.deal.update`; Bitrix write
  methods не добавлены.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — ожидаемо сообщает
  trailing whitespace только в существующем локальном изменении `WORKFLOW.md`.
  Этот файл не изменялся и не будет staged в рамках задания.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'` — passed
  для всех файлов задания.

## Факты

- Во время реализации и проверок live Bitrix calls не выполнялись.
- Endpoint конверсии читает только локальную `normalized_deals`.
- Open deals не участвуют в знаменателе; период фильтруется по inclusive
  `closed_at`, а не по `created_at`.
- При нулевом знаменателе API возвращает `null`, UI показывает `—`.
- Существующие won-only revenue и `revenue_usd * 0.50` semantics не менялись.
- Deal-contact assignment и существующие analytics filters/sorting/pagination
  сохранены.
- Docker Compose по-прежнему только запускает сервисы и не обновляет Bitrix
  автоматически.
- Реальные `.env`, webhook, credentials, DuckDB, Parquet, CSV, raw data, logs,
  caches, `node_modules`, `frontend/dist` и `ui-kits/` не добавлялись.

## Предположения

- Поддержанные формы checkbox payload (`true`/`false`, числа, `Y`/`N`,
  `YES`/`NO`, `TRUE`/`FALSE`, camel-case universal alias) покрывают ожидаемый
  контракт до первой ручной production-загрузки.

## Неизвестное

- Точный live Bitrix payload type/value и metadata casing не проверялись по
  условию задания.
- Неизвестна дата, с которой поле исторически заполнялось последовательно.

## Риски или следующий шаг

- Существующие строки после migration корректно получают `kev_held = false`.
  После deployment оператору нужно вручную нажать `Обновить из Bitrix`, чтобы
  локально заполнить новое поле актуальными read-only данными.
- Отчет показывает корреляционное сравнение и не доказывает причинность или
  статистическую значимость, что остается вне scope задания.
