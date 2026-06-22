# Отчет: TASK-2026-06-22-09

Статус: done

## Кратко

Добавлена backend-only диагностика связей contact-deal и targeted read-only
Bitrix verification/correction path для одного contact ID.

Для `contact_id=661` локальная диагностика показала:

- contact type raw: `[61]`;
- normalized type: `Дизайнер`;
- region: `Беларусь`;
- priority: `1`;
- local raw linked deals: `14773`, `19149`, `23989`, `24761`;
- local analytical deals: `14773`, `19149`, `23989`, `24761`.

Это подтверждает, что 4 локальные raw-связи полностью совпадают с 4
аналитическими сделками. Приоритет `Дизайнер` не является причиной потери.

Targeted live Bitrix verification через `crm.deal.list` с
`filter: {"CONTACT_ID": 661}` вернула те же 4 deal IDs:

```text
14773, 19149, 23989, 24761
```

Через этот read-only API заявленные 7 сделок не воспроизводятся. Следовательно,
найденная точка расхождения для текущего безопасного extraction path:
локальная база соответствует Bitrix `crm.deal.list CONTACT_ID`, а
пользовательский UI-счетчик 7 относится к другой Bitrix card/relationship
семантике или состоянию, не раскрытому этим list-фильтром. Broad per-deal
`crm.deal.contact.items.get` scan по всем сделкам не запускался.

## Root Cause

Потери в local normalization для `661` не найдено:

- raw contact exists;
- rule `61 -> Дизайнер / priority 1` active;
- raw links count equals analytical deals count;
- every linked local deal exists in `raw_deals`;
- each linked deal selects `661` as analytical contact.

Для текущего normal sync source (`crm.deal.list` fields `CONTACT_ID` /
`CONTACT_IDS`) live Bitrix также возвращает 4 сделки. Поэтому конкретная
разница "Bitrix UI 7 vs local 4" не объясняется missing raw links, parsing, or
normalization. Она остается Bitrix UI/card relation semantics mismatch against
the read-only list API used by this MVP.

## Измененные файлы

- `backend/app/bitrix/client.py` — добавлен read-only
  `list_deals_for_contact(contact_id)` через `crm.deal.list` с safe select.
- `backend/app/bitrix/transform.py` — `CONTACT_IDS` теперь парсится из list,
  tuple, dict/object-shaped values, and bracketed/comma/semicolon strings.
- `backend/app/reports/contact_deal_diagnostics.py` — новый backend diagnostic
  and targeted verification/correction helper.
- `backend/app/api/models.py` — response models для diagnostics.
- `backend/app/main.py` — добавлены internal diagnostics endpoints.
- `backend/tests/test_contact_deal_diagnostics.py` — regression for targeted
  correction and renormalization.
- `backend/tests/test_bitrix_client.py` — проверка single-contact read-only
  deal list call.
- `backend/tests/test_bitrix_ingestion.py` — покрытие дополнительных
  `CONTACT_IDS` response shapes.
- `backend/tests/test_contact_selection.py` — проверка, что `Дизайнер`
  priority `1` wins over lower-priority primary contact.
- `docs/development.md` — documented diagnostic endpoints and safe use.
- `docs/data-model.md` — documented targeted diagnostic/correction path.
- `.ai/report.md` — текущий отчет.

Pre-existing unstaged local changes in `.ai/task.md`, `AGENTS.md`, and
`WORKFLOW.md` were not made by Codex for this task and were not intentionally
modified.

## Diagnostic Endpoints

Local-only diagnostic:

```text
GET /api/internal/diagnostics/contacts/{contact_id}/deal-links
```

Targeted live Bitrix verification:

```text
POST /api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-deals
```

By default the live endpoint only compares counts/IDs. With
`apply_local_correction=true`, it inserts missing local links for that supplied
contact, inserts returned safe deal rows if absent locally, and reruns local
normalization. It is not called during Docker startup, page load, or normal
manual refresh.

## Bitrix Calls

Live Bitrix was called during this task.

Read-only methods used:

```text
crm.deal.list
```

Targeted calls:

- `crm.deal.list` with `filter: {"CONTACT_ID": 661}` — returned 4 deals:
  `14773`, `19149`, `23989`, `24761`.
- `crm.deal.list` with `filter: {"=CONTACT_ID": 661}` — returned the same
  4 deals during a bounded filter probe.
- A probe using `CONTACT_IDS` as a filter was stopped because it did not remain
  bounded and began a long list request. No broad sync or full per-deal contact
  scan was completed.
- A final targeted shape check for the 4 returned deals showed
  `CONTACT_ID=661` and `CONTACT_IDS=None` for those deals.

No Bitrix write methods were added or called.

## Проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit:
  `9698fd4 planner: TASK-2026-06-22-09 Fix contact-deal link completeness`.
- `git status --short` — passed. Showed pre-existing modified `.ai/task.md`,
  `AGENTS.md`, and `WORKFLOW.md`.

Focused backend checks:

- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m py_compile ...` —
  passed.
- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m pytest tests/test_contact_deal_diagnostics.py tests/test_bitrix_ingestion.py::test_deal_contact_links_are_built_from_downloaded_deal_rows tests/test_contact_selection.py::test_designer_priority_one_wins_over_primary_lower_priority_contact`
  — passed, `3 passed`.

Full backend:

- `cd backend && /tmp/bitrix-backend-venv/bin/python3 -m pytest` — passed,
  `61 passed`.

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

- Not run. Docker/operator startup flow was not changed; only backend
  diagnostic endpoints and docs were added.

## Факты

- `contact_id=661` exists locally with raw type `[61]`.
- The active local rule maps `61` to `Дизайнер`, priority `1`, active.
- Local raw links and normalized analytical deal assignment for `661` both
  contain exactly 4 deals.
- Live targeted `crm.deal.list CONTACT_ID=661` also contains exactly 4 deals.
- Current documented/safe Bitrix source for this MVP does not expose the
  reported three additional UI deals through the tested single-contact
  read-only list filters.

## Предположения

- If the Bitrix contact card still shows 7 deals, those 3 extra items likely
  come from a Bitrix UI/card relation semantic outside `crm.deal.list
  CONTACT_ID`, from stale UI state, from permissions/category visibility
  differences, or from another relation path not included in MVP extraction.

## Неизвестное

- Exact IDs of the three extra UI-visible deals were not available in the
  repository or local data.
- A broad `crm.deal.contact.items.get` scan across all local deals was not run
  because it is the slow/heavy path explicitly removed from normal sync.

## Риски или следующий шаг

If the user can provide the three Bitrix UI deal IDs, the new diagnostic path
can compare those specific IDs safely against local raw deals, raw links, and
analytical assignment without a broad live scan.
