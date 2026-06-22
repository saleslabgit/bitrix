# Отчет: TASK-2026-06-22-11

Статус: done

## Кратко

Проверил `crm.item.list` как быстрый read-only источник полных связей
deal-contact для normal manual refresh.

Решение: normal manual Bitrix sync switched from `crm.deal.list` deal rows to
`crm.item.fields` + `crm.item.list` deal items. Связи строятся из `contactId`
and `contactIds`, поэтому secondary contacts вроде `661` для сделок `123`,
`343`, `1239` больше не теряются без explicit reconciliation.

Docker startup and frontend flow не изменены: refresh по-прежнему запускается
только вручную оператором.

## Official Docs Checked

Context7 official Bitrix24 REST API docs were checked for:

- `crm.item.fields` — fields for CRM entity type;
- `crm.item.list` — list items with `entityTypeId=2`, explicit `select`, and
  `filter`;
- `crm.deal.list` — legacy/deprecated context from task;
- `batch` — up to 50 requests per batch, fallback only.

Docs also confirmed `contactId`, `contactIds`, and `fm` fields exist in the
universal item model. The implementation never requests `*` or `fm`.

## Live Bitrix Test

Live Bitrix was called.

Read-only methods used, bounded to exactly these deal IDs:

```text
crm.item.fields
crm.item.list
```

Supplied deal IDs:

```text
123, 343, 1239, 14773, 19149, 23989, 24761
```

Safe selected fields discovered and used:

```text
id
title
opportunity
currencyId
createdTime
closedate
stageId
categoryId
contactId
contactIds
```

Contact-related fields discovered and selected:

```text
contactId
contactIds
```

`crm.item.list` returned all seven supplied deal IDs and included contact `661`
for every deal:

| Deal ID | returned linked contact IDs | has 661 |
|---:|---|---|
| 123 | 661, 1005, 1145, 2123, 30105 | yes |
| 343 | 661, 1425, 4607 | yes |
| 1239 | 661, 1005, 1145, 2123, 30105 | yes |
| 14773 | 661, 19497 | yes |
| 19149 | 661, 23973, 27875, 30313 | yes |
| 23989 | 661, 29471 | yes |
| 24761 | 661, 30313, 30315, 30317, 30319 | yes |

This agrees with the TASK-10 `crm.deal.contact.items.get` result for the known
case. Therefore `crm.item.list` is sufficient for normal refresh link
extraction for this decision point.

No raw Bitrix payloads, webhook values, tokens, phone, email, address,
messengers, comments, files, requisites, activities, local paths, or generated
data contents were printed or documented.

## Implementation

Changed normal manual ingestion:

- `run_bitrix_manual_ingestion()` now calls `client.list_deal_items()` instead
  of `client.list_deals()`.
- `list_deal_items()` first calls `crm.item.fields` for `entityTypeId=2`, builds
  an explicit safe select list, then calls `crm.item.list`.
- Deal raw fields are still transformed into the same local `raw_deals`
  columns.
- Deal-contact links are still reconstructed locally, but now from item
  `contactId` / `contactIds`.
- `closedate` from item fields is now mapped to local `closed_at`.
- `crm.deal.contact.items.get` is still not used in normal sync.

Added internal bounded diagnostic:

```text
POST /api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-item-deals?deal_ids=...
```

It calls only `crm.item.fields` and `crm.item.list`, returns safe ID-level facts
only, and does not mutate local data.

## Changed Files

- `backend/app/bitrix/allowlist.py` — added safe item field candidates and
  `build_deal_item_select()`; fixed `IM` forbidden check so `createdTime` is not
  falsely rejected.
- `backend/app/bitrix/client.py` — added read-only `crm.item.fields` /
  `crm.item.list` support.
- `backend/app/bitrix/ingestion.py` — normal manual ingestion now loads deal
  items via `crm.item.list`.
- `backend/app/bitrix/transform.py` — added `closedate` fallback.
- `backend/app/reports/contact_deal_diagnostics.py` — added bounded
  `crm.item.list` verification helper.
- `backend/app/api/models.py` — added item-list diagnostic response models.
- `backend/app/main.py` — added internal item-list diagnostic endpoint.
- `backend/tests/test_bitrix_client.py` — tests safe item select, read-only
  item methods, and no `*`/`fm`.
- `backend/tests/test_bitrix_ingestion.py` — tests normal ingestion preserves
  secondary `contactIds` and designer priority wins.
- `backend/tests/test_contact_deal_diagnostics.py` — tests bounded item-list
  diagnostic and safe output.
- `backend/tests/test_api_bitrix.py` — updated mocked refresh client to item
  row shape.
- `docs/data-model.md` — normal sync now documented as `crm.item.list` item
  rows with `contactId` / `contactIds`.
- `docs/development.md` — documented item-list diagnostic and normal sync
  behavior.
- `.ai/report.md` — this report.

Pre-existing unstaged local changes in `.ai/task.md`, `AGENTS.md`, and
`WORKFLOW.md` were not made by Codex for this task and were not intentionally
modified.

## Checks

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit:
  `a540fdf planner: TASK-2026-06-22-11 Test crm.item.list deal contact links`.
- `git status --short --branch` — passed. Showed pre-existing modified
  `.ai/task.md`, `AGENTS.md`, and `WORKFLOW.md`.

Focused backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m py_compile app/bitrix/allowlist.py app/bitrix/client.py app/bitrix/ingestion.py app/reports/contact_deal_diagnostics.py app/api/models.py app/main.py`
  — passed.
- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m pytest tests/test_bitrix_client.py tests/test_bitrix_ingestion.py tests/test_contact_deal_diagnostics.py`
  — passed, `23 passed`.

Full backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m pytest` — passed,
  `71 passed`.

Safety:

- `rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests`
  — passed for implementation scope. It found only the existing negative test
  `crm.deal.update`.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — not clean because of
  pre-existing unstaged `WORKFLOW.md` whitespace/line-ending diff not made by
  Codex in this task.
- `git diff --check -- .ai/report.md backend/app backend/tests docs/data-model.md docs/development.md`
  — passed for task files.

Frontend:

- Not run. No frontend code changed.

Compose:

- Not run. Docker/operator startup behavior was not changed. Manual refresh
  internals changed, but Docker Compose still starts services only and does not
  call Bitrix automatically.

## Facts

- `crm.item.list` returned all seven known deals.
- `crm.item.list` returned complete `contactIds` including `661` for every known
  deal.
- The selected item fields are safe and explicit; `*` and `fm` are not selected.
- Normal manual sync now uses item list contact IDs for links and preserves
  secondary contacts.
- Designer priority `1` still wins when `661` is secondary and a lower-priority
  contact is primary.

## Unknowns

- Whether every historical edge case in the portal is covered by `crm.item.list`.
  The known `661` case that motivated this task is covered.

## Risks Or Next Step

If future data quality checks find more relation gaps, the fallback design is a
separate deep relation sync using Bitrix `batch` with up to 50
`crm.deal.contact.items.get` sub-requests per HTTP call, explicit operator
triggering, progress/status, and no Docker startup automation. That fallback was
not implemented or run in this task because `crm.item.list` passed the bounded
known-case test.

No Bitrix write methods were added or called.
