# Отчет: TASK-2026-07-20-03

Статус: done

## Кратко

Исправлены review-блокеры funnel analytics: реальные backend sort allowlists
включают средний чек и цикл, ABC/КЭВ используют draft/apply даты создания,
filter badges считают новые фильтры, а cached funnel metadata валидируется
строго и безопасно.

## Измененные файлы

- backend/app/reports/analytics.py
- frontend/src/App.tsx
- SPEC.md
- backend/README.md
- frontend/README.md
- docs/development.md
- docs/deployment.md
- docs/project-status.md
- .ai/report.md

## Запущенные проверки

- Full backend suite в Python 3.12 Docker container: `144 passed in 121.79s`.
- `cd frontend && npm run build`: passed.
- `docker compose config`: passed.
- `docker compose -f docker-compose.prod.yml config`: passed.
- `curl -fsS http://127.0.0.1:8000/health`: passed.
- Frontend operator curl на `127.0.0.1:5173` не выполнен: frontend service не
  был запущен в текущем runtime. Это не меняет успешный build.

## Факты

- Live Bitrix calls не выполнялись; Bitrix write methods и wildcard selects не
  добавлялись.
- Docker startup не менялся и не запускает refresh автоматически.
- После deployment оператор вручную запускает `Обновить из Bitrix` для
  справочника воронок и category-aware stages.
