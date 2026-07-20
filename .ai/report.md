# Отчет: TASK-2026-07-20-06

Статус: done

## Кратко

Bitrix `CLOSEDATE` отделен как плановый `planned_close_at`. Фактический
`actual_closed_at` разрешается из последнего точного перехода в текущую
финальную стадию (`crm.stagehistory.list`, deal/category/stage и `S`/`F`) с
единственным fallback на `movedTime`. Open deals всегда получают `NULL`.

Все close-dependent backend reports, filters, cycles, series, RFM/ABC/KEV,
metadata и currency-rate date selection читают только factual timestamp.
Legacy `closed_at` сохранен как deprecated nullable physical column для
additive migration и не используется аналитикой или новыми snapshots.

## Измененные файлы

- Backend domain, Bitrix allowlist/client/transform/ingestion.
- DuckDB schema, additive migration, loaders, normalization и raw snapshots.
- Analytics, local metadata, profile, diagnostics и currency-rate selection.
- Backend fixtures/tests для batching, pagination, resolver, migration,
  planned-vs-actual, open/reclose/fallback/error и существующей аналитики.
- `SPEC.md`, backend/frontend README и docs data/development/deployment/status.
- `.ai/report.md`.

## Запущенные проверки

- `python3 -m compileall backend/app backend/tests` — passed.
- Focused pytest в одноразовом backend container — `103 passed`.
- Полный pytest в чистом одноразовом backend container:
  `python -m pytest -q` — `151 passed in 137.42s`.
- `cd frontend && npm run build` — passed; осталось существующее Vite warning
  о chunk больше 500 kB.
- `docker compose config --quiet` — passed.
- `docker compose -f docker-compose.prod.yml config --quiet` — passed.
- Local operator flow через `/tmp/task06-compose.override.yml` с
  `APP_AUTH_ENABLED=false` и `BITRIX_WEBHOOK_URL=""`: `/health` и frontend
  вернули HTTP 200; `POST /api/sync/run` завершился success и явно подтвердил
  отсутствие Bitrix calls; `docker compose ... down -v` — passed.
- Safety search запрещенных CRM writes нашел только negative test
  `crm.deal.update`; wildcard selects не найдены.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'` — passed.

## Факты

- `crm.stagehistory.list` добавлен только в read-only allowlist и всегда
  получает `entityTypeId=2`, `TYPE_ID=3`, approved select, bounded ID batches и
  все страницы `start/next`; поддержан официальный `result.items`.
- Raw history содержит только семь одобренных полей и участвует в той же
  transaction/snapshot процедуре.
- Ошибка history/transform/resolution возникает до activation либо откатывает
  transaction; предыдущий active dataset сохраняется.
- Additive migration не копирует ambiguous legacy `closed_at` в factual поле.
- API/frontend field `closed_date` сохранен, но теперь означает factual close.
- Live Bitrix calls не выполнялись. Docker startup не запускает refresh.

## Предположения

- Нет новых предположений сверх `.ai/task.md`.

## Неизвестное

- Полнота stage history, webhook permission для `crm.stagehistory.list` и live
  объем данных остаются непроверенными: live tenant calls были запрещены.

## Риски или следующий шаг

- После deployment требуется один ручной `Обновить из Bitrix`. Если tenant не
  разрешает stage history или у закрытой сделки нет ни exact history, ни
  `movedTime`, refresh завершится безопасной ошибкой и сохранит прежний dataset.
