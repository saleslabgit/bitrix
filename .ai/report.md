# Отчет: TASK-2026-06-22-25

Статус: done

## Кратко

Исправил ABC filter toolbar, чтобы controls переносились внутри workspace и
не уезжали вправо. Уточнил changed-only UX: фильтр теперь называется
`Только изменившие ABC` и работает только при примененном периоде `Стало`.

## Измененные файлы

- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/styles.css`
- `frontend/README.md`
- `.ai/report.md`

## Что изменено

- `toolbar-abc` переведен на responsive `auto-fit` grid.
- ABC search занимает две колонки на широком экране и одну колонку на узком.
- ABC action buttons больше не требуют отдельной широкой строки и занимают
  ширину своей grid-ячейки.
- Checkbox label заменен с `Только изменения` на `Только изменившие ABC`.
- Checkbox disabled без примененного `Стало`.
- Если persisted state содержит `changedOnly=true`, single-period ABC request
  визуально не показывает checked state и не отправляет `changed_only=true`.
- При включенном `Стало` checkbox продолжает отправлять `changed_only=true` и
  фильтрует по `segment_changed`.

## Запущенные проверки

Before implementation:

- `git log --oneline -5`
- `git status --short --branch`

Frontend:

- `cd frontend && npm run build` — passed.

Safety:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only existing negative test `crm.deal.update`; no Bitrix write
  method was added.

## Факты

- Backend ABC calculation logic не менялся.
- Contacts и Deals behavior намеренно не менялся.
- Frontend по-прежнему вызывает локальный backend endpoint
  `/api/reports/abc/analytics`.
- Region filters/columns не добавлялись.
- `ui-kits/` не изменялся.
- Bitrix calls не добавлялись.

## Предположения

- Responsive grid с minimum control width `150px` покрывает типичные desktop
  widths с sidebar enabled и позволяет toolbar переноситься на несколько строк.

## Неизвестное

- Browser visual verification was not run. The ABC toolbar renders only with an
  active dataset, and this task did not run a local data refresh or live
  browser flow. The responsive behavior is covered by CSS changes and frontend
  build.

## Риски или следующий шаг

Review should verify in browser at the reported viewport width that `Стало с`,
`Стало по`, `Применить стало`, and `Сбросить` stay inside the ABC report
workspace.
