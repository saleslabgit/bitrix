# Отчет: TASK-2026-06-22-10

Статус: done

## Кратко

Расследование завершено по точному списку сделок для `contact_id=661`:

```text
123, 343, 1239, 14773, 19149, 23989, 24761
```

Root cause: обычный local sync строил `raw_deal_contact_links` только из
`crm.deal.list` полей `CONTACT_ID` / `CONTACT_IDS`. Для сделок `123`, `343`,
`1239` локально были raw deals и ссылки на других контактов, но не было ссылки
на `661`. Bitrix per-deal relation API `crm.deal.contact.items.get` подтвердил,
что `661` действительно связан с этими тремя сделками как secondary contact.
Поэтому сделки назначались другим аналитическим контактам и не считались в
аналитике `661`.

Добавлен bounded explicit-ID diagnostic/verification/reconciliation flow.
Diagnostics read-only by default. Мутирующий `apply_local_correction` из
TASK-09 удален из verification endpoint; reconciliation вынесен в отдельный
explicit operator endpoint and records a local dataset run/status.

## Local Status Before Reconciliation

Для `contact_id=661`:

| Deal ID | raw_deal | local link to 661 | local linked contacts | analytical contact | counted for 661 | reason |
|---:|---|---|---|---:|---|---|
| 123 | yes | no | 1145 | 1145 | no | missing contact link |
| 343 | yes | no | 1425 | 1425 | no | missing contact link |
| 1239 | yes | no | 1145 | 1145 | no | missing contact link |
| 14773 | yes | yes | 661 | 661 | yes | counts |
| 19149 | yes | yes | 661 | 661 | yes | counts |
| 23989 | yes | yes | 661 | 661 | yes | counts |
| 24761 | yes | yes | 661 | 661 | yes | counts |

## Live Bitrix Verification

Live Bitrix was called.

Read-only methods used, bounded to the seven supplied deal IDs:

```text
crm.deal.list
crm.deal.contact.items.get
```

`crm.deal.list` with safe `@ID` filter returned all seven supplied deal IDs.
`crm.deal.contact.items.get` was called exactly once per supplied deal ID.

Bitrix confirmed `661` in relation data for all seven deals:

| Deal ID | Bitrix deal exists | Bitrix linked contact IDs | has 661 | primary 661 |
|---:|---|---|---|---|
| 123 | yes | 661, 1005, 1145, 2123, 30105 | yes | no |
| 343 | yes | 661, 1425, 4607 | yes | no |
| 1239 | yes | 661, 1005, 1145, 2123, 30105 | yes | no |
| 14773 | yes | 661, 19497 | yes | yes |
| 19149 | yes | 661, 23973, 27875, 30313 | yes | yes |
| 23989 | yes | 661, 29471 | yes | yes |
| 24761 | yes | 661, 30313, 30315, 30317, 30319 | yes | yes |

No raw Bitrix payloads, secrets, webhook values, phones, emails, addresses,
comments, files, requisites, or arbitrary custom fields were printed, stored in
the report, or committed.

## Reconciliation Applied

Explicit reconciliation was run for contact `661` and the seven supplied deal
IDs.

Changed local generated DuckDB data only:

- inserted raw deal rows: none;
- inserted `raw_deal_contact_links`: `(123, 661)`, `(343, 661)`, `(1239, 661)`;
- reran normalization;
- recorded successful local dataset run/status:
  `bitrix-explicit-reconciliation`.

After reconciliation:

```text
normalized_deals analytical_contact_id=661 count: 7
```

Rows now assigned to `661`:

```text
123 won
343 won
1239 won
14773 lost
19149 won
23989 won
24761 open
```

`Дизайнер` priority `1` wins over the lower-priority linked contacts, so each
deal is still counted only once and now belongs to contact `661`.

## Измененные файлы

- `backend/app/bitrix/client.py` — added bounded `list_deals_by_ids()` and
  robust parsing for `crm.deal.contact.items.get` object rows or plain IDs.
- `backend/app/reports/contact_deal_diagnostics.py` — added exact-ID local
  diagnostics, exact-ID Bitrix verification, and explicit reconciliation with
  dataset run/status recording; removed the TASK-09 mutating verification path.
- `backend/app/api/models.py` — added response models for exact-ID diagnostics,
  verification, and reconciliation.
- `backend/app/main.py` — added exact-ID diagnostic, verification, and separate
  reconciliation endpoints; removed `apply_local_correction` from verification.
- `backend/tests/test_contact_deal_diagnostics.py` — added focused tests for
  local categories, bounded verification, reconciliation, no-confirmation no-op,
  and safe diagnostic output.
- `backend/tests/test_bitrix_client.py` — added tests for safe explicit ID deal
  list and plain contact IDs from deal-contact relation responses.
- `docs/development.md` — documented read-only diagnostics and separate
  explicit reconciliation endpoint.
- `docs/data-model.md` — documented explicit bounded reconciliation semantics.
- `.ai/report.md` — this report.

Pre-existing unstaged local changes in `.ai/task.md`, `AGENTS.md`, and
`WORKFLOW.md` were not made by Codex for this task and were not intentionally
modified.

## Diagnostic And Reconciliation Endpoints

Local exact-ID diagnostic:

```text
GET /api/internal/diagnostics/contacts/{contact_id}/explicit-deals?deal_ids=123&deal_ids=343
```

Read-only live exact-ID verification:

```text
POST /api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-explicit-deals?deal_ids=123&deal_ids=343
```

Explicit bounded reconciliation:

```text
POST /api/internal/reconciliation/contacts/{contact_id}/explicit-deals?deal_ids=123&deal_ids=343
```

The reconciliation endpoint is the only mutating endpoint in this flow. It is
bounded to the supplied IDs, verifies read-only Bitrix relation data first,
inserts only confirmed missing links/safe deal rows, reruns normalization, and
records a dataset run/status.

## Проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit:
  `acdba54 planner: TASK-2026-06-22-10 Reconcile contact 661 explicit deal IDs`.
- `git status --short --branch` — passed. Showed pre-existing modified
  `.ai/task.md`, `AGENTS.md`, and `WORKFLOW.md`.

Documentation lookup:

- Context7 Bitrix24 REST API docs checked for `crm.deal.list` and
  `crm.deal.contact.items.get`.

Focused backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m py_compile app/reports/contact_deal_diagnostics.py app/api/models.py app/main.py app/bitrix/client.py`
  — passed.
- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m pytest tests/test_contact_deal_diagnostics.py tests/test_bitrix_client.py tests/test_api_bitrix.py`
  — passed, `18 passed`.

Full backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m pytest` — passed,
  `67 passed`.

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

- Not run. Docker/operator startup behavior was not changed. New behavior is
  internal backend diagnostics/reconciliation only and is never automatic.

## Факты

- Deals `123`, `343`, and `1239` existed locally before reconciliation.
- They were linked locally to contacts `1145`, `1425`, and `1145`
  respectively, not to `661`.
- Bitrix per-deal relation data confirmed contact `661` for all three missing
  deals.
- Local reconciliation inserted exactly three missing links and no raw deal
  rows.
- After normalization, all seven supplied deal IDs count for `661`.

## Предположения

- The regular `crm.deal.list` row fields are incomplete for secondary
  historical contact links in this case; per-deal relation data is the more
  complete source for explicit reconciliation.

## Неизвестное

- Whether other contacts have similar historical secondary-link gaps. A broad
  scan remains out of scope because it would require the heavy per-deal relation
  path that was intentionally removed from normal sync.

## Риски или следующий шаг

The implemented path fixes explicit supplied IDs safely. A broader strategy for
finding all missing secondary links would need a separate product/ops decision
because it may require a bounded batch job over many deals and explicit progress
handling.
