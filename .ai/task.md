# Task: TASK-2026-06-21-12

Status: planned
Created from commit: d75899d5835452b3032fd4ece19947873f582c53

## Title

Validate live Bitrix read-only discovery

## Goal

Use the locally configured Bitrix webhook to perform the first live read-only validation of the Bitrix boundary: confirm credentials are loaded correctly, run metadata discovery, identify the configured contact type field candidate, and determine whether a first manual read-only sync is safe to run next.

This is a live validation/reporting milestone. It must not call any Bitrix write method. It must not test write-method rejection on the production webhook.

## User Context

- The user has added the Bitrix webhook locally.
- The webhook must never be committed, printed, logged, or copied into `.ai/report.md`.
- Tests of forbidden write methods must remain mocked/unit-only.
- Do not call live methods such as:
  - `crm.deal.add`
  - `crm.deal.update`
  - `crm.deal.delete`
  - any other create/update/delete/write-capable CRM method.

## Allowed Live Bitrix Methods

Before any live call, verify that the code path can call only the current read-only allowlist:

- `crm.contact.fields`
- `crm.deal.fields`
- `crm.contact.list`
- `crm.deal.list`
- `crm.deal.contact.items.get`
- `crm.status.list`

For this task, prefer live discovery first. Do not run manual sync until discovery succeeds and the report explains the observed metadata shape.

If you decide a tiny smoke read is needed beyond discovery, it must use only allowlisted read-only list/status methods already implemented by the client and must avoid printing raw rows.

## Scope

### 1. Confirm Secret Handling And Runtime Wiring

- Confirm `.env` is not tracked and remains ignored.
- Confirm the app can load `BITRIX_WEBHOOK_URL` from the local environment without exposing its value.
- If Docker Compose currently does not load the user's `.env` into the backend container, make the smallest safe repo change needed to support local `.env` runtime loading without committing secrets.
- Do not modify `.env.example` with real values.

### 2. Verify Read-Only Guardrails Before Live Calls

- Inspect/confirm the Bitrix client allowlist before making live calls.
- Run existing mocked/unit tests that prove write methods are rejected without touching the live webhook.
- Do not perform live negative tests against write methods.
- If tests are missing or insufficient, add/adjust mocked tests only.

### 3. Run Live Discovery

Run the minimal live discovery path against the configured webhook:

- `GET /api/bitrix/discovery`, or the equivalent service call if easier in this environment.

Capture only safe metadata in `.ai/report.md`:

- discovery state;
- contact fields count;
- deal fields count;
- whether required fields are missing;
- candidate safe custom contact fields for choosing `BITRIX_CONTACT_TYPE_FIELD`;
- whether current `BITRIX_CONTACT_TYPE_FIELD` is configured and exists;
- any permission/API error code or safe message without webhook URL, tokens, raw values, or personal data.

Do not include raw contact/deal rows, webhook URLs, tokens, phones, emails, addresses, comments, files, or arbitrary field values in the report.

### 4. Decide Next Step

Based on discovery, report one of these outcomes:

- contact type field is identified and can be configured next;
- discovery succeeded but contact type field remains ambiguous and user decision is needed;
- discovery failed due to permissions/configuration and the exact safe next action is needed;
- manual read-only sync appears safe to run next after setting `BITRIX_CONTACT_TYPE_FIELD`.

Do not run the full manual sync in this task unless discovery succeeds, credentials are read-only, no contact type ambiguity blocks the run, and the report can safely summarize counts only. If unsure, stop after discovery and report.

### 5. Documentation/Report

Update `.ai/report.md` with:

- changed files;
- checks run;
- live methods actually called;
- explicit statement that no live write methods were called;
- safe discovery facts;
- whether any repo code/config changes were needed;
- recommended next task.

Update docs only if a repo/runtime issue is fixed and docs would otherwise be misleading. Keep docs changes minimal.

## Out Of Scope

- Calling any live write method.
- Testing write-method rejection against the production webhook.
- Committing `.env`, webhook URLs, tokens, raw Bitrix data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, or generated data.
- Running full sync if discovery is ambiguous or unsafe.
- NBRB integration.
- Authentication.
- Frontend or `ui-kits/` work.
- Scheduler/automatic sync.
- Production deployment.

## Constraints

- Follow `AGENTS.md`, `docs/workflow.md`, and current `.ai/task.md`.
- Bitrix is strictly read-only.
- Live validation must use only allowed read-only methods.
- Do not print or commit secrets.
- Do not include raw CRM records or personal fields in `.ai/report.md`.
- Do not use `git add .`.
- Do not modify `ui-kits/`.
- Do not stage `.env` or generated data under `data/`.
- If the live environment is unavailable or the webhook is not visible to the process, document the exact safe reason and stop without inventing results.

## Acceptance Criteria

- `.env` remains untracked/ignored and no secret is committed.
- Live Bitrix validation uses only read-only allowlisted methods.
- No live write-method test is performed.
- Existing mocked write-method rejection tests pass or are strengthened without live calls.
- Discovery is run, or the exact safe reason it could not be run is reported.
- `.ai/report.md` contains safe discovery metadata and no webhook/token/raw CRM data.
- The report clearly recommends the next task: set `BITRIX_CONTACT_TYPE_FIELD`, run first read-only manual sync, fix permissions/config, or ask user to choose among candidates.
- Any repo changes are minimal and directly related to safe local runtime loading or mocked guardrail tests.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-21-12 Validate live Bitrix read-only discovery
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run from `backend/` in the configured dev environment:

```bash
python -m pytest
```

If dependencies are not installed in the current environment, use the existing backend dev environment and document the exact command.

Run targeted guardrail tests if useful, for example:

```bash
python -m pytest tests/test_bitrix_client.py tests/test_bitrix_discovery.py tests/test_api_bitrix.py
```

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

If any required check or live discovery cannot be run, document the exact reason in `.ai/report.md`.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- the latest relevant commit is this planner commit;
- `.ai/report.md` is updated;
- every required check is either run and reported, or explicitly documented as not run with reason;
- all live Bitrix methods actually called are listed in `.ai/report.md`;
- `.ai/report.md` explicitly states that no live write methods were called;
- staged files are only files intentionally changed for TASK-12 plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
