# Task: TASK-2026-06-22-01

Status: planned
Created from commit: 7a17ae182669a61cbd48f666a38be6e88f2b3a66

## Title

Profile live dataset quality

## Goal

Inspect the first active live Bitrix dataset locally, without calling Bitrix, and produce a safe aggregate quality/profile report that prepares the next product decision: how to configure contact type, priority, and region rules.

This task must not invent business mappings. It should surface safe aggregate facts and blockers so the user can confirm the mapping rules in a later task.

## Context

- TASK-14 completed the first successful live read-only sync.
- Active dataset should be `bitrix-manual`.
- Reported live sync counts were:
  - raw contacts: `14216`;
  - raw deals: `9142`;
  - raw links: `8830`;
  - normalized contacts: `14216`;
  - normalized deals: `9142`.
- Deal-contact links are now built locally from deal fields `CONTACT_ID` and `CONTACT_IDS`; normal sync does not mass-call `crm.deal.contact.items.get`.
- Contact type field is `UF_CRM_1595304971232`, stored locally as `contact_type_raw`.
- Current contact type/region normalization rules are not yet configured from real data.

## Scope

### 1. Read Local Active Dataset Status

Use only the configured local DuckDB database. Do not call Bitrix.

Confirm and report safe status facts:

- active dataset name/kind/state;
- latest run state;
- raw/normalized counts;
- snapshot count only;
- whether expected tables exist.

Do not print local absolute paths, raw rows, contact names, deal names, webhook URLs, tokens, or generated file contents.

### 2. Add Safe Dataset Profiling Helpers If Useful

If the current code lacks a clean way to compute these aggregates, add a small backend service/helper module and tests. Keep it local-only and deterministic.

Useful safe aggregates:

- counts by `contact_type_raw`, including null/empty bucket;
- number of distinct `contact_type_raw` values;
- contacts missing type;
- deals without analytical contact;
- deals without any local link;
- links whose contact/deal is missing from raw tables;
- status group counts: won/open/lost;
- currency counts;
- category/stage counts by IDs only;
- date min/max for created/closed dates;
- normalized contacts still mapped to `Не определено`;
- normalized deals by `contact_type_normalized` and `region_normalized`.

Contact type raw values are configuration/domain values, not contact row values; they may be reported as aggregate labels with counts. Do not report contact names, deal names, IDs in samples, phone/email/address/comment/file/activity data, or any row-level personal data.

### 3. Check Current Normalization Rules

Inspect local `contact_type_rules` only as aggregate/config data:

- number of active rules;
- which real `contact_type_raw` values currently have no active rule;
- whether current normalized type/region outputs are mostly `Не определено`.

Do not invent priorities or regions. If rules are missing, report exactly what user/business input is needed.

### 4. Optional API Surface

If implementation cost is small and fits existing patterns, add a typed local endpoint such as:

```text
GET /api/datasets/profile
```

It must return only safe aggregate data. If adding an endpoint would be larger than needed, keep this as a service/helper and report output in `.ai/report.md` only.

### 5. Documentation And Report

Update concise docs only if new service/API/profile behavior is added:

- `docs/data-model.md` — mention safe dataset profiling if added;
- `docs/development.md` — mention local-only profile endpoint/helper if added;
- `docs/project-status.md` — update current next step;
- `.ai/report.md` — include safe aggregate results, changed files, checks, assumptions, unknowns, and next recommendation.

## Out Of Scope

- Calling Bitrix live API.
- Re-running sync.
- Any write methods.
- Creating or committing `.env`, DuckDB files, Parquet snapshots, CSV exports, logs, caches, raw exports, or generated data.
- Reporting raw contact/deal rows, contact names, deal names, row IDs as samples, phones, emails, addresses, comments, files, activities, webhook URLs, or tokens.
- Inventing contact type priorities, normalized regions, or business mapping rules.
- NBRB integration.
- Authentication.
- Frontend or `ui-kits/` work.
- Scheduler/automatic sync.
- Production deployment.

## Constraints

- Follow `AGENTS.md`, `docs/workflow.md`, current `.ai/task.md`, and the latest user instruction.
- Work only from local persisted data for profiling.
- Do not call Bitrix in this task.
- Keep output aggregate-only and safe.
- Do not use `git add .`.
- Do not modify `ui-kits/`.
- Do not stage `.env` or generated data under `data/` or `backend/data/`.
- If local active dataset is missing, report the blocker and do not fabricate profile results.

## Acceptance Criteria

- No Bitrix live calls are made.
- Active local dataset status is inspected safely.
- `.ai/report.md` includes safe aggregate profile results or a safe blocker if the dataset is unavailable.
- Contact type raw distribution is summarized as aggregate labels/counts.
- Missing/undefined normalization state is summarized.
- Deal/link integrity is summarized.
- No raw rows, personal fields, secrets, local absolute paths, or generated file contents are reported.
- If code is added, tests cover the profiling logic using synthetic/local fixture data.
- Documentation is updated if a reusable profile helper/API is added.
- Generated local data artifacts are not staged or committed.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-01 Profile live dataset quality
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run targeted backend tests from `backend/` in the configured dev environment if code changes are made:

```bash
python -m pytest
```

Use the existing backend dev environment if system Python lacks pytest, and document the exact command used.

Run from repository root:

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
- `.ai/report.md` explicitly states that no Bitrix live calls were made;
- `.ai/report.md` contains only aggregate safe profile data or a safe blocker;
- staged files are only files intentionally changed for TASK-2026-06-22-01 plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
