# Task: TASK-2026-06-21-13

Status: planned
Created from commit: 615fb73e8d3ff49d75b9b8e9fa0f45304e6363c0

## Title

Run first live Bitrix read-only sync

## Goal

Use the user-confirmed Bitrix contact type field to perform the first live read-only manual Bitrix sync into the local persistent dataset, then verify that the active dataset and analytics endpoints can read the synced data.

This is a live read-only validation and first-export milestone. It must not call any Bitrix write method and must not print, commit, or report raw CRM rows or secrets.

## User Confirmation

The user confirmed that the correct Bitrix contact type field is:

```text
BITRIX_CONTACT_TYPE_FIELD=UF_CRM_1595304971232
```

This value may be written only to the local ignored `.env` if it is missing there. Do not commit `.env`.

## Hard Safety Rule

Do not call live write methods. Do not test write-method rejection on the production webhook.

Forbidden live examples include, but are not limited to:

- `crm.deal.add`
- `crm.deal.update`
- `crm.deal.delete`
- `crm.contact.add`
- `crm.contact.update`
- `crm.contact.delete`
- any other create/update/delete/write-capable CRM method.

Mocked/unit tests may continue to prove write methods are rejected without live calls.

## Allowed Live Bitrix Methods

Only these currently implemented read-only methods may be called live:

- `crm.contact.fields`
- `crm.deal.fields`
- `crm.contact.list`
- `crm.deal.list`
- `crm.deal.contact.items.get`
- `crm.status.list`

If any other live Bitrix method seems necessary, stop and report instead of calling it.

## Scope

### 1. Local Environment Preparation

- Confirm `.env` is ignored and not staged.
- Confirm `BITRIX_WEBHOOK_URL` is configured without printing its value.
- Ensure local `.env` contains `BITRIX_CONTACT_TYPE_FIELD=UF_CRM_1595304971232`.
- If updating local `.env` is needed, do it without committing it and mention only that the field was set, not any secret.

### 2. Guardrails Before Live Sync

- Inspect/confirm the read-only method allowlist before live calls.
- Run mocked guardrail tests for Bitrix client write-method rejection.
- Do not perform live negative tests against write methods.
- Confirm the manual sync path still uses only the read-only client methods listed above.

### 3. Repeat Live Discovery With Configured Field

Run live discovery again after setting `BITRIX_CONTACT_TYPE_FIELD`.

Report only safe metadata:

- discovery state;
- contact fields count;
- deal fields count;
- `contact_type_field_exists` for `UF_CRM_1595304971232`;
- missing required fields counts/names if any;
- safe API/permission errors if discovery fails.

If discovery fails or `contact_type_field_exists` is not `true`, stop before sync and report the blocker.

### 4. Run First Manual Read-Only Sync

If discovery succeeds and the configured field exists:

- run the existing manual Bitrix sync path;
- allow only counts/status reporting;
- do not print or commit raw contacts, raw deals, row values, personal fields, webhook URL, token, local DB, snapshots, or generated files;
- verify local dataset status and active dataset status after sync;
- verify at least one existing report/read endpoint can read the active synced dataset without exposing raw rows in `.ai/report.md`.

Safe report facts may include:

- sync state;
- raw contacts count;
- raw deals count;
- raw links count;
- normalized contacts count;
- normalized deals count;
- active dataset kind/name/state;
- snapshot count and relative snapshot identifiers count only, not file contents;
- high-level endpoint health such as total rows returned/counts only.

### 5. Documentation/Report

Update `.ai/report.md` with:

- changed files;
- checks run;
- local env preparation outcome without secrets;
- all live Bitrix methods actually called;
- explicit statement that no live write methods were called;
- discovery result with configured field;
- sync counts/status or blocker;
- generated artifacts status: not staged/committed;
- recommended next task.

Update docs only if the operator flow changed or existing docs are inaccurate. Keep docs changes minimal.

## Out Of Scope

- Calling any live write method.
- Testing write-method rejection against the production webhook.
- Reporting raw CRM rows or field values from contacts/deals.
- Committing `.env`, webhook URLs, tokens, raw Bitrix data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, or generated data.
- NBRB integration.
- Authentication.
- Frontend or `ui-kits/` work.
- Scheduler/automatic sync.
- Production deployment.
- Refactoring ingestion architecture unless a small fix is required to complete the safe read-only sync.

## Constraints

- Follow `AGENTS.md`, `docs/workflow.md`, and current `.ai/task.md`.
- Bitrix remains strictly read-only.
- Live validation must use only allowed read-only methods.
- Do not print or commit secrets.
- Do not include raw CRM records or personal fields in `.ai/report.md`.
- Do not use `git add .`.
- Do not modify `ui-kits/`.
- Do not stage `.env` or generated data under `data/`.
- If live sync returns a safe error, report it and stop; do not broaden field allowlists or call unapproved methods without a new planner task.

## Acceptance Criteria

- `.env` remains ignored/untracked and no secret is committed.
- `BITRIX_CONTACT_TYPE_FIELD=UF_CRM_1595304971232` is configured locally or a safe reason is reported if it cannot be configured.
- Live discovery confirms `contact_type_field_exists=true`, or sync is not run and the blocker is reported.
- Live Bitrix calls use only read-only allowlisted methods.
- No live write-method test is performed.
- First manual read-only sync runs successfully, or a safe blocker/error is reported without raw rows or secrets.
- Active dataset status reflects the sync if it succeeds.
- At least one read/report endpoint is verified after a successful sync using counts/status only.
- `.ai/report.md` contains safe counts/status and no webhook/token/raw CRM data.
- Generated local data artifacts are not staged or committed.
- Any repo changes are minimal and directly related to safe first sync validation.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-21-13 Run first live Bitrix read-only sync
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run targeted guardrail tests from `backend/` in the configured dev environment:

```bash
python -m pytest tests/test_bitrix_client.py tests/test_bitrix_discovery.py tests/test_api_bitrix.py
```

Run full backend tests if changes affect code:

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

If any required check or live sync step cannot be run, document the exact safe reason in `.ai/report.md`.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- the latest relevant commit is this planner commit;
- `.ai/report.md` is updated;
- every required check is either run and reported, or explicitly documented as not run with reason;
- all live Bitrix methods actually called are listed in `.ai/report.md`;
- `.ai/report.md` explicitly states that no live write methods were called;
- sync counts/status are reported without raw CRM rows or secrets, or a safe blocker is reported;
- staged files are only files intentionally changed for TASK-13 plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
