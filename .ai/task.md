# Task: TASK-2026-06-21-14

Status: planned
Created from commit: 5b25735dc8a88e4584d2a17cdae8bcaa30d1a9c3

## Title

Build deal-contact links locally

## Goal

Correct the live Bitrix sync architecture so the first real export does not perform one `crm.deal.contact.items.get` API call per deal. The system must fetch contacts and deals through read-only list APIs, then build deal-contact links locally from already downloaded deal/contact data whenever Bitrix exposes the needed link field(s) in deal metadata/list responses.

This task exists because TASK-13 showed the current per-deal link fetching path is operationally wrong for the real account size. The user's latest instruction is the source of truth: do not mass-load links through per-deal API calls; derive links locally from the downloaded dataset.

## Important Requirement Correction

The current `SPEC.md` still mentions `crm.deal.contact.items.get` as a preferred method. For this project workflow, update the repo documentation to reflect the corrected rule:

- contacts and deals are loaded via read-only API;
- deal-contact links are built locally from fields already present in downloaded deal/contact data;
- `crm.deal.contact.items.get` must not be used as the mass sync path;
- if a future exceptional diagnostic use is ever needed, it requires a separate explicit planner task and must not be part of the normal sync.

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

## Live API Rule For This Task

The live sync path must not call `crm.deal.contact.items.get`.

Allowed live methods for this task are limited to read-only metadata/list/status methods:

- `crm.contact.fields`
- `crm.deal.fields`
- `crm.contact.list`
- `crm.deal.list`
- `crm.status.list`

If local link reconstruction cannot be done from safe deal fields, stop and report the blocker instead of falling back to per-deal `crm.deal.contact.items.get`.

## Scope

### 1. Inspect Current Deal Metadata Safely

Use live metadata only as needed to identify safe deal field(s) that can represent contact linkage, for example `CONTACT_ID` or an equivalent Bitrix deal field.

Report only safe metadata:

- whether a deal contact-link field exists;
- field code(s) considered;
- no raw deal/contact row values;
- no webhook/token/personal data.

If no safe field exists in deal metadata/list responses, stop after documenting the blocker and do not run full sync.

### 2. Update Bitrix Allowlist And Transform

If a safe deal contact field exists:

- add the required field(s) to the deal select allowlist;
- transform downloaded deal rows into local `raw_deal_contact_links` without per-deal API calls;
- for a primary contact ID from a deal row, store:
  - `deal_id`;
  - `contact_id`;
  - `is_primary=true`;
  - `sort_order` as `NULL` unless safely available;
  - `role_id` as `NULL` unless safely available.
- skip empty/null contact IDs safely;
- keep one row per `deal_id + contact_id`.

Do not add phones, email, addresses, comments, files, activities, arbitrary custom fields, or any forbidden data.

### 3. Remove Per-Deal Link Fetching From Normal Sync

- The normal manual Bitrix ingestion path must not call `client.get_deal_contact_links(deal_id)`.
- Consider removing the method from the normal path entirely, or keeping it unused with tests proving the sync path does not call it.
- The live methods reported by the sync must not include `crm.deal.contact.items.get`.
- Update tests so a fake client without `get_deal_contact_links` can complete ingestion.

### 4. Retry First Live Read-Only Sync

After the implementation and tests pass:

- confirm `.env` is ignored and not staged;
- confirm `BITRIX_WEBHOOK_URL` is configured without printing it;
- confirm `BITRIX_CONTACT_TYPE_FIELD=UF_CRM_1595304971232` is configured locally;
- run live discovery and verify `contact_type_field_exists=true`;
- run the first manual read-only sync using the corrected local-link path;
- report only counts/status, not raw rows.

Safe report facts may include:

- sync state;
- raw contacts count;
- raw deals count;
- raw links count;
- normalized contacts count;
- normalized deals count;
- active dataset kind/name/state;
- snapshot count only;
- high-level report endpoint count/health only.

### 5. Documentation And Report

Update documentation concisely:

- `SPEC.md` — correct the Bitrix extraction method section so it no longer says normal sync should use per-deal `crm.deal.contact.items.get`.
- `docs/data-model.md` and/or `docs/development.md` — document that links are built locally from downloaded deal/contact data and that per-deal link API is not used for normal sync.
- `docs/project-status.md` — update current state/next steps after successful sync or blocker.
- `.ai/report.md` — full safe report with changed files, checks, live methods called, explicit no-write statement, sync counts/status or blocker, assumptions, unknowns, and next step.

## Out Of Scope

- Calling any live write method.
- Testing write-method rejection against the production webhook.
- Mass calling `crm.deal.contact.items.get`.
- Reporting raw CRM rows or contact/deal field values.
- Committing `.env`, webhook URLs, tokens, raw Bitrix data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, or generated data.
- NBRB integration.
- Authentication.
- Frontend or `ui-kits/` work.
- Scheduler/automatic sync.
- Production deployment.
- Complex staging-table architecture beyond what is needed for this corrected sync path.

## Constraints

- Follow `AGENTS.md`, `docs/workflow.md`, current `.ai/task.md`, and the user's latest correction.
- Bitrix remains strictly read-only.
- Live validation must use only allowed read-only methods listed for this task.
- Do not print or commit secrets.
- Do not include raw CRM records or personal fields in `.ai/report.md`.
- Do not use `git add .`.
- Do not modify `ui-kits/`.
- Do not stage `.env` or generated data under `data/` or `backend/data/`.
- If live sync returns a safe error, report it and stop; do not broaden field allowlists or call unapproved methods without a new planner task.

## Acceptance Criteria

- Normal manual Bitrix sync no longer calls `crm.deal.contact.items.get`.
- Deal-contact links are built locally from downloaded deal/contact data if the required safe field exists.
- If no safe deal contact-link field exists, sync is not run and `.ai/report.md` explains the blocker without raw rows or secrets.
- Tests cover local link construction and prove ingestion can complete without `get_deal_contact_links`.
- Existing mocked read-only/write-guard tests still pass.
- Live methods actually called are listed in `.ai/report.md` and exclude write methods.
- Live methods actually called for sync exclude `crm.deal.contact.items.get`.
- First corrected manual read-only sync runs successfully, or a safe blocker/error is reported.
- Active dataset status reflects the sync if it succeeds.
- At least one read/report endpoint is verified after successful sync using counts/status only.
- `.ai/report.md` contains safe counts/status and no webhook/token/raw CRM data.
- Generated local data artifacts are not staged or committed.
- Documentation is corrected so future agents do not reintroduce per-deal link API mass sync.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-21-14 Build deal-contact links locally
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run targeted backend tests from `backend/` in the configured dev environment:

```bash
python -m pytest tests/test_bitrix_client.py tests/test_bitrix_discovery.py tests/test_bitrix_ingestion.py tests/test_api_bitrix.py
```

Run full backend tests if code changes affect shared behavior:

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
- `.ai/report.md` explicitly states whether `crm.deal.contact.items.get` was avoided for sync;
- sync counts/status are reported without raw CRM rows or secrets, or a safe blocker is reported;
- staged files are only files intentionally changed for TASK-14 plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
