# Отчет: TASK-2026-07-20-06

Статус: done

## Кратко

Исправлен explicit contact-deal reconciliation: новые и существующие
подтвержденные закрытые сделки теперь проходят тот же factual-close resolver,
что normal manual refresh. History загружается одним bounded вызовом для набора
deal IDs до локальных writes; exact current final-stage history имеет приоритет,
`movedTime` остается единственным fallback.

Reconciliation transactionally upsert-ит полный approved deal state, approved
raw history и links, затем выполняет normalization, status и activation. Любая
handled ошибка разрешения или локальной транзакции не оставляет partial rows и
не заменяет предыдущий active dataset.

## Измененные файлы

- `backend/app/reports/contact_deal_diagnostics.py`
- `backend/tests/test_contact_deal_diagnostics.py`
- `backend/README.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/project-status.md`
- `.ai/report.md`

## Запущенные проверки

- Final focused reconciliation:
  `python -m pytest tests/test_contact_deal_diagnostics.py -q` — `12 passed`.
- Required focused backend set в одноразовом container — `112 passed`.
- Final full backend suite: `python -m pytest -q` —
  `157 passed in 144.03s` (включает финальный rollback test).
- `python3 -m compileall backend/app backend/tests` — passed.
- `cd frontend && npm run build` — passed; осталось существующее Vite warning
  о chunk больше 500 kB.
- `docker compose config --quiet` — passed.
- `docker compose -f docker-compose.prod.yml config --quiet` — passed.
- Operator flow с временным `/tmp/task06-compose.override.yml`,
  `APP_AUTH_ENABLED=false`, `BITRIX_WEBHOOK_URL=""`: backend `/health` и
  frontend вернули HTTP 200; synthetic `POST /api/sync/run` завершился success
  и сообщил `No Bitrix calls were made`; `down -v` — passed.
- Safety search CRM writes нашел только intentional negative test
  `crm.deal.update`; wildcard selects не найдены.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'` — passed.

## Факты

- Reconciliation переиспользует `transform_deals`,
  `transform_deal_stage_history` и `apply_actual_close_times`.
- Для нескольких affected closed deals выполняется один вызов
  `list_deal_stage_history`; per-deal history N+1 отсутствует.
- New/changed/missing-factual deal rows сохраняют `closed_at=NULL`,
  `planned_close_at`, factual `actual_closed_at`, `kev_held` и остальные
  approved поля.
- Approved seven-column history сохраняется idempotent upsert-ом только для
  bounded affected IDs; unrelated history не удаляется.
- Existing valid unchanged closed rows не переписываются. Existing closed rows
  с `actual_closed_at=NULL` ремонтируются; current open rows очищают factual
  timestamp.
- January/February/June test проверяет raw/normalized даты, KEV, history, Deals
  API close date и cycle through June. Reclose, fallback, batching и повторный
  reconciliation также покрыты.
- Forced normalization failure доказал rollback deal/history/link writes и
  сохранение предыдущего active run.
- Live Bitrix calls не выполнялись; Docker startup не изменялся.

## Предположения

- Использованы предположения из `.ai/task.md`; новых нет.

## Неизвестное

- Live tenant history completeness и permission для `crm.stagehistory.list`
  остаются намеренно непроверенными.

## Риски или следующий шаг

- В live окружении отсутствие и exact history, и `movedTime` у подтвержденной
  закрытой сделки вернет safe reconciliation error и сохранит active dataset;
  это следует проверить только отдельным разрешенным operator действием.
