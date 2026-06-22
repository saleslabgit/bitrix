# Task: TASK-2026-06-22-02

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-01`

## Title

Extract contact type enum labels

## Goal

Prepare the exact business mapping input table that the user needs before the next large backend/data readiness milestone.

Read Bitrix metadata for the contact type field `UF_CRM_1595304971232` and extract the human-readable enum labels for the raw option IDs observed in the active local dataset. Then write a safe mapping template into `.ai/report.md` so the user can fill the business decisions: normalized type, region, priority, and active/inactive rule.

This task is metadata-only. It must not call CRM row-listing methods, must not rerun sync, and must not create/update/delete anything in Bitrix CRM.

## Context

- The active live local dataset was profiled in `TASK-2026-06-22-01`.
- The contact type field is `UF_CRM_1595304971232`.
- Local profiling found `54` distinct non-empty `contact_type_raw` combinations, built from these unique option IDs:

```text
59
61
65
67
151
245
247
249
251
253
255
469
1943
1945
2341
2343
2345
2785
2829
```

- There are currently `0` active `contact_type_rules`, so normalized type and region are still `Не определено` for the live dataset.
- The next large backend/data readiness milestone must not start until the user has a clear mapping table to fill.

## Required Output For The User

In `.ai/report.md`, include a table with one row per observed Bitrix enum option ID.

Codex must fill these factual columns:

- `bitrix_option_id` — numeric enum option ID from Bitrix, e.g. `65`.
- `bitrix_option_label` — human-readable enum option label from Bitrix metadata.
- `contacts_count` — aggregate count of contacts whose raw type contains this option ID, calculated from the local DuckDB dataset.
- `observed_raw_combinations` — safe aggregate list/count summary of raw combinations containing this option ID. Do not include contact IDs, contact names, deal IDs, deal names, or row samples.

Codex must leave these decision columns blank or marked `TODO_USER`:

- `normalized_type` — the analytics group name the user wants in reports, e.g. `Клиент`, `Дилер`, `Партнер`, `Поставщик`, `Не определено`, or another business-approved value.
- `region` — the analytics region group the user wants in reports, e.g. `РБ`, `РФ`, `СНГ`, `Европа`, `Другое`, `Не определено`, or another business-approved value.
- `priority` — integer priority for choosing the analytical contact when a deal has multiple contacts. Smaller number wins. Use `1` for the most important contact type, then `2`, `3`, etc. If a type should never win analytical-contact selection, mark it clearly for user decision.
- `is_active` — whether this enum option should become an active normalization rule: `true` / `false` / `TODO_USER`.

Also include a short explanation in `.ai/report.md` that the user only needs to fill the decision columns, not the factual columns.

## Scope

### 1. Read Workflow And Current State

Before implementation, read:

- `AGENTS.md`;
- `docs/workflow.md`;
- `docs/crm_analytics_system_tz.md`;
- `.ai/task.md`;
- `.ai/report.md`;
- recent `git log` / `git status`.

### 2. Extract Bitrix Metadata Safely

Use only read-only metadata access for `UF_CRM_1595304971232`.

Allowed Bitrix method class:

- metadata/fields method needed to inspect contact field enum items, expected path through existing discovery/client code such as `crm.contact.fields`.

Forbidden Bitrix method classes in this task:

- `crm.contact.list`;
- `crm.deal.list`;
- `crm.deal.contact.items.get`;
- any method ending in `.add`, `.update`, `.delete`;
- any method that returns contact/deal row data instead of field metadata.

If existing discovery code does not expose enum labels, add the smallest reusable helper/API/script that keeps this metadata-only boundary explicit and covered by tests.

### 3. Combine With Local Aggregate Counts

Use the active local DuckDB dataset only for aggregate counts:

- contacts count by option ID;
- raw combination counts that contain each option ID.

Do not output local absolute paths, raw rows, row samples, contact/deal IDs, contact/deal names, phone, email, address, messenger, comments, files, activity data, webhook URLs, tokens, or generated file contents.

### 4. Report And Docs

Update `.ai/report.md` with:

- changed files;
- exact Bitrix metadata methods called and call counts;
- confirmation that no forbidden CRM methods were called;
- mapping template table;
- checks run;
- assumptions and blockers.

Update concise docs only if new reusable helper/API behavior is added.

## Out Of Scope

- Filling the business mapping decisions.
- Creating active `contact_type_rules`.
- Re-running local normalization.
- Re-running Bitrix sync.
- Fetching contacts/deals from Bitrix.
- Any write method in Bitrix.
- NBRB currency integration.
- Frontend work.
- UI kits work.
- Authentication, deployment, scheduler, or production migration work.

## Acceptance Criteria

- `.ai/report.md` contains a user-fillable mapping table for all observed option IDs listed above.
- The table includes Bitrix enum labels from metadata and local aggregate counts.
- User decision columns are clearly marked and left for the user.
- Bitrix calls are metadata-only and read-only.
- `.ai/report.md` explicitly lists the methods called and confirms forbidden methods were not called.
- No contact/deal row data, IDs, names, personal fields, secrets, local absolute paths, or generated data are reported.
- If code is added, tests cover metadata enum extraction and safe output behavior using mocks/local fixtures.
- Generated local data artifacts are not staged or committed.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-02 Extract contact type enum labels
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run targeted backend tests from `backend/` if code changes are made:

```bash
python -m pytest
```

If system Python lacks pytest, use the existing backend dev environment and document the exact command used.

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
- `.ai/report.md` explicitly states which Bitrix methods were called;
- `.ai/report.md` explicitly states that no forbidden CRM methods were called;
- staged files are only files intentionally changed for `TASK-2026-06-22-02` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
