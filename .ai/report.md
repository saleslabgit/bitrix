# Отчет: TASK-2026-07-20-06

Статус: done

## Кратко

Explicit reconciliation теперь загружает final-stage history для каждого
confirmed current won/lost deal до решения о локальном upsert, включая сделки с
уже заполненным `actual_closed_at`. Поэтому reopen/reclose в ту же стадию
обновляет stale factual timestamp.

После factual resolution полный remote `DealSnapshot` сравнивается с локальным
по всем approved полям. Upsert выполняется только для отсутствующей или реально
измененной строки; approved history по bounded IDs сохраняется транзакционно
даже для неизменной сделки.

## Измененные файлы

- `backend/app/reports/contact_deal_diagnostics.py`
- `backend/tests/test_contact_deal_diagnostics.py`
- `backend/README.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/project-status.md`
- `.ai/report.md`

## Запущенные проверки

- Focused reconciliation:
  `python -m pytest tests/test_contact_deal_diagnostics.py -q` — `15 passed`.
- Final full backend suite: `python -m pytest -q` —
  `160 passed in 167.99s`.
- `python3 -m compileall backend/app backend/tests` — passed.
- `cd frontend && npm run build` — passed; осталось существующее Vite warning
  о chunk больше 500 kB.
- `docker compose config --quiet` — passed.
- `docker compose -f docker-compose.prod.yml config --quiet` — passed.
- Synthetic operator flow через `/tmp/task06-compose.override.yml` с
  `APP_AUTH_ENABLED=false` и `BITRIX_WEBHOOK_URL=""`: `/health` и frontend —
  HTTP 200; `POST /api/sync/run` — success с `No Bitrix calls were made`;
  `docker compose ... down -v` — passed.
- Safety search CRM writes нашел только intentional negative test
  `crm.deal.update`; wildcard selects не найдены.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'` — passed.

## Факты

- Один bounded `list_deal_stage_history()` получает все confirmed current
  closed IDs; N+1 отсутствует.
- `apply_actual_close_times()` применяется ко всем confirmed transformed deals:
  closed получают latest exact/fallback, open получают `NULL`.
- Existing-local reclose test сохраняет unchanged stage/category/status/planned
  date/KEV, но обновляет factual close May -> June; Deals API и cycle используют
  June.
- Local state загружается как typed `DealSnapshot`: name, Decimal amount,
  currency, UTC creation/planned/factual timestamps, stage, category, status и
  KEV сравниваются детерминированно.
- Отдельный test доказывает update при изменении только name, amount, currency и
  creation time. Unchanged closed test доказывает history fetch и пустой deal
  upsert.
- Deprecated physical `closed_at` остается `NULL` и не участвует в сравнении.
- Existing fallback, missing factual, open, batching, idempotency и forced
  rollback tests сохранены и проходят.
- Live Bitrix calls не выполнялись; Docker startup не изменялся.

## Предположения

- Новых предположений сверх `.ai/task.md` нет.

## Неизвестное

- Live tenant history completeness и webhook permission намеренно не
  проверялись.

## Риски или следующий шаг

- Live operator reconciliation остается отдельным явно разрешаемым действием.
  При отсутствии exact history и `movedTime` safe failure сохраняет предыдущий
  active dataset.
