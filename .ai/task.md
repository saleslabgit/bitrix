# Task: TASK-2026-06-22-03

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-02`

## Title

Apply live data rules and rates

## Goal

Complete one large backend/data-readiness milestone for the active live Bitrix dataset before frontend work:

- apply the user-approved contact type, region, and priority mapping;
- update normalization so rules are based on Bitrix enum option IDs inside `contact_type_raw`, not only exact raw combinations;
- treat missing contact type as `Конечный клиент / Без региона / priority 4 / active`;
- rerun local normalization from the already persisted active dataset without a new Bitrix sync;
- add real currency-rate loading needed for USD analytics on the active dataset;
- verify existing analytics endpoints on the live local dataset;
- update documentation and `.ai/report.md` with useful current status.

This task must not call Bitrix sync or Bitrix row-listing methods. Bitrix remains read-only and no CRM write methods are allowed.

## User-Approved Contact Type Mapping

Use this exact mapping.

Priority semantics:

- `1` is the highest priority.
- Smaller numeric priority wins over larger numeric priority.
- `4` is lower than `1`, `2`, and `3`.
- `99` means effectively does not participate in analytical contact selection.
- `is_active=false` means the option is stored/known but must not be used for active normalization or analytical contact selection.

| bitrix_option_id | bitrix_option_label | normalized_type | region | priority | is_active |
|---:|---|---|---|---:|---|
| 59 | Подрядчик | Подрядчик | Беларусь | 3 | true |
| 61 | Дизайнер / архитектор | Дизайнер | Беларусь | 1 | true |
| 65 | Конечный клиент | Конечный клиент | Без региона | 4 | true |
| 67 | Поставщик | Поставщик | Без региона | 99 | false |
| 151 | Дилер | Дилер | Беларусь | 2 | true |
| 245 | Другое | Другое | Без региона | 99 | false |
| 247 | Проектировщик | Проектировщик | Беларусь | 3 | true |
| 249 | Конкурент | Другое | Без региона | 99 | false |
| 251 | Дилер РБ | Дилер | Беларусь | 2 | true |
| 253 | Мастер-класс | Другое | Без региона | 99 | false |
| 255 | РФ Дизайнер/Архитектор | Дизайнер | Россия | 1 | true |
| 469 | Перевозчик | Другое | Без региона | 99 | false |
| 1943 | Партнер | Партнер | Без региона | 99 | false |
| 1945 | маркетинг | Другое | Без региона | 99 | false |
| 2341 | Дилер РФ | Дилер | Россия | 2 | true |
| 2343 | Подрядчик РФ | Подрядчик | Россия | 3 | true |
| 2345 | Проектировщик РФ | Подрядчик | Россия | 3 | true |
| 2785 | Строители РФ | Подрядчик | Россия | 3 | true |
| 2829 | Прораб РБ | Подрядчик | Беларусь | 3 | true |

Missing/empty type rule:

| source | normalized_type | region | priority | is_active |
|---|---|---|---:|---|
| no ID / empty field / `NULL` / empty string / `False` / `[]` | Конечный клиент | Без региона | 4 | true |

Important business notes:

- End clients have no region tracking in source data, so all end clients must be `Без региона`.
- Contacts without contact type must also be normalized as end clients.

## Required Behavior

### 1. Rule Storage And Configuration

Implement the mapping as configuration/data, not scattered business logic.

Acceptable approaches:

- source-controlled configuration file plus a loader that upserts local `contact_type_rules` into DuckDB; or
- a revised local config table schema plus a deterministic seed/apply helper.

Keep the system reproducible after a fresh checkout and local DB initialization. Do not commit generated DuckDB files, Parquet snapshots, `.env`, CSV exports, or local data artifacts.

If the current `contact_type_rules` table shape is too exact-raw-value oriented, migrate/extend it carefully. The new behavior must support rules by individual enum option ID because live raw values can be combinations such as `[59, 65]` and `[61, 59, 65]`.

### 2. Contact Normalization

For each contact:

- parse `contact_type_raw` into option IDs when present;
- ignore inactive options for active normalization;
- choose the active option with highest priority, where priority `1` wins over `2`, `3`, `4`;
- if multiple active options have the same priority, use deterministic tie-breakers and document them;
- if `contact_type_raw` is missing/empty/`False`/`[]`, apply the missing-type rule: `Конечный клиент / Без региона / priority 4`;
- if a non-empty raw value contains only inactive/unknown options, normalize to the existing undefined value and do not treat it as an end client.

### 3. Analytical Contact Selection

For each deal with linked contacts:

- select the analytical contact using only active normalized contacts/rules;
- priority `1` is highest and must win over `2`, `3`, and `4`;
- contacts based only on inactive/unknown options must not win analytical selection;
- if priorities tie, keep or introduce deterministic tie-breakers consistent with the existing domain rules, such as Bitrix primary flag and then contact ID;
- a deal with no eligible active contact should remain without analytical contact rather than selecting an inactive type.

### 4. Local Re-Normalization Without Bitrix Sync

Add a safe local operation/helper/API/CLI path, following existing patterns, that:

- applies/upserts the approved rules;
- reruns normalization for the current active local dataset from existing DuckDB raw tables;
- updates normalized tables and safe local status/reporting as needed;
- does not call Bitrix at all;
- does not overwrite raw Bitrix tables;
- is covered by tests with local/synthetic data.

If an API endpoint is added, it must be clearly local-only and safe. If a CLI/helper is more consistent with the current codebase, use that instead.

### 5. Currency Rates For USD Analytics

The current live data contains multiple currencies. Add the first real currency-rate loading path required for USD analytics.

Requirements:

- use a read-only external rate source consistent with the project spec, expected NBRB where applicable;
- persist rates locally in `currency_rates`;
- cover currencies observed in the active dataset, currently including at least `BYN`, `EUR`, `RUB`, and `USD`;
- support historical report calculations by choosing the latest local rate on or before the deal date, consistent with existing report behavior;
- keep tests deterministic by mocking the external rate source or using local fixtures;
- do not call Bitrix for currency work;
- document any limitation if a currency/rate/date cannot be resolved.

If full historical backfill is too large for one implementation pass, implement a bounded but correct loader for the date range present in local deals and clearly report what was loaded and what remains.

### 6. Live Dataset Verification

After applying rules and rates locally, run safe verification against the active live local dataset and include aggregate results in `.ai/report.md`:

- active dataset name/kind/state;
- raw and normalized counts;
- count of active contact type rules;
- normalized contacts/deals by type and region;
- count of contacts still undefined by type/region;
- count of deals without analytical contact;
- analytics endpoints smoke results for contacts, ABC, RFM, stale deals, deal cycle, concentration, and type/region reports;
- currency rates loaded by currency/date range/source;
- no row-level contact/deal data, no names, no IDs in samples, no local absolute paths, no secrets.

## Out Of Scope

- Any Bitrix CRM write method.
- New Bitrix sync or row listing from Bitrix.
- `crm.contact.list`, `crm.deal.list`, `crm.deal.contact.items.get`.
- Companies, leads, products, activities, comments, files, phones, emails, addresses, messengers, requisites.
- Frontend screens or `ui-kits/` work.
- Authentication.
- Scheduler/automatic sync.
- Production deployment.
- CSV export.

## Acceptance Criteria

- User mapping above is implemented exactly.
- Missing contact type normalizes as `Конечный клиент / Без региона / priority 4`.
- Option-ID combinations are handled correctly, not as unrelated exact strings.
- Priority semantics are correct: `1` is highest and `99` does not participate.
- Inactive options do not win active normalization or analytical contact selection.
- Local re-normalization runs from persisted raw tables without a Bitrix sync.
- USD analytics use persisted local rates loaded through the new real-rate path, with deterministic tests.
- Existing analytics endpoints work after live local re-normalization.
- `.ai/report.md` includes safe aggregate before/after or after-only verification results.
- `.ai/report.md` explicitly states that no Bitrix sync/row-listing/write methods were called.
- Documentation is updated for rule semantics, local re-normalization, and currency-rate loading.
- Generated local data artifacts are not staged or committed.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-03 Apply live data rules and rates
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run backend tests from `backend/`:

```bash
python -m pytest
```

If system Python lacks pytest, use the existing backend dev environment and document the exact command used.

Run syntax/compile checks if consistent with the previous tasks.

Run from repository root if Docker is available:

```bash
docker compose config
```

Before committing:

```bash
git status --short --branch
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

If any required check cannot be run, document the exact reason in `.ai/report.md`.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- the latest relevant commit is this planner commit;
- `.ai/report.md` is updated;
- every required check is either run and reported, or explicitly documented as not run with reason;
- `.ai/report.md` explicitly states that no Bitrix sync, Bitrix row-listing, or Bitrix write methods were called;
- staged files are only files intentionally changed for `TASK-2026-06-22-03` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
