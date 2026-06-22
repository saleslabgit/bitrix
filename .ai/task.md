# Task: TASK-2026-06-22-12

Status: planned
Created from: current `main` after `80475ba codex: TASK-2026-06-22-11 Test crm.item.list deal contact links`

## Title

Fix empty refresh writes

## Goal

Fix the manual refresh failure reported by the user after switching normal sync to `crm.item.list`:

```text
Invalid Input Error: executemany requires a non-empty list of parameter sets to be provided
```

The refresh must not fail with a low-level DuckDB `executemany` error when an intermediate row list is empty. It must either safely skip an empty insert where empty data is acceptable, or return a clear user-safe error explaining which required data was absent.

## Facts

- Bitrix is read-only.
- Normal manual sync now uses `crm.item.fields` + `crm.item.list` for deal items and `contactId` / `contactIds` for links.
- The user hit the error from the UI manual refresh flow: `POST /api/local/refresh-data`.
- `backend/app/storage/loaders.py` already uses `_executemany_if_rows()` for raw Bitrix inserts.
- Other code paths still call `connection.executemany(...)` directly with possibly empty lists.
- Known direct `executemany` risk areas from current GitHub files:
  - `backend/app/pipeline/normalization.py` inserts `normalized_contacts` and `normalized_deals` without empty-row guards.
  - `backend/app/pipeline/currency_rates.py` inserts `currency_rates` without an empty-row guard and can produce an empty `rows` list if NBRB/source/common-date data resolves to no insertable rows.
  - `backend/app/pipeline/approved_contact_type_rules.py` inserts approved rules without an empty-row guard; default rules are non-empty, but the helper should still be robust for tests/custom calls.
- This is not a Bitrix write issue and must not add any Bitrix write methods.

## Assumptions

- The immediate user error likely comes from one of the unguarded `executemany` calls after Bitrix data was fetched: normalization or currency-rate loading.
- Empty raw links can be acceptable; empty contacts/deals/rates may or may not be acceptable depending on stage of the flow.
- The fix should make the failing step identifiable from the UI-safe status message without exposing raw rows, secrets, local paths, or stack traces.

## Unknowns

- Which exact direct `executemany` triggered the user's current failure.
- Whether the live refresh fetched zero deal items, zero contacts, or fetched deals but no insertable NBRB currency-rate rows.
- Whether `crm.item.list` full normal sync returned zero rows on this user's run due to Bitrix behavior, field selection, pagination, or a transient issue.

## Scope

### 1. Audit direct `executemany` usage

Search backend app/tests for direct `executemany` calls.

For production code, ensure no call can receive an empty parameter list unless it is guarded or intentionally raises a clear domain error before DuckDB is called.

Do not change unrelated test fixture setup unless needed for coverage.

### 2. Fix normalization empty-row handling

In `normalize_local_data()`:

- If there are zero raw contacts, skip normalized contact insert safely.
- If there are zero raw deals, skip normalized deal insert safely.
- Ensure this does not mask errors for malformed non-empty data.
- Keep deals without links supported: they should still normalize as `Без контакта` / `Не определено`.

### 3. Fix currency-rate empty-row handling

In `load_currency_rates_for_raw_deals()`:

- If there are no raw deals, continue returning `None` as today.
- If raw deals exist but computed currency-rate insert rows are empty, do not call DuckDB `executemany` with an empty list.
- Prefer a clear `ValueError` with a safe message, for example:

```text
No currency rate rows were loaded for observed deal currencies/date range.
```

- Preserve existing supported-currency checks and USD-required checks.
- Do not expose external response payloads or raw deal rows.

### 4. Fix approved rules helper robustness

In `replace_contact_type_rules()`:

- If called with an empty rule tuple, clear rules and return `0` without calling empty `executemany`.
- Preserve current behavior for the default approved rules.

### 5. Improve refresh failure message if needed

If the low-level DuckDB message can still surface from manual refresh, wrap or convert it to a clearer safe status message.

Do not expose stack traces, local paths, webhook values, raw Bitrix payloads, phone/email/address/messenger/comment/file/requisite/activity data, or arbitrary custom fields.

### 6. Tests

Add focused backend tests for:

- `normalize_local_data()` with zero raw contacts and zero raw deals does not raise `executemany requires...` and leaves normalized tables empty.
- `normalize_local_data()` with deals but no links still creates normalized deals with no analytical contact.
- `load_currency_rates_for_raw_deals()` with raw deals but no insertable rate rows returns/raises a clear safe error and does not call empty `executemany`.
- `replace_contact_type_rules(connection, rules=())` clears rules and returns `0` without raising.
- Manual refresh failure status for this class of issue is safe and understandable.
- Existing item-list ingestion tests still pass, including secondary designer contact `661`.
- CRM write methods remain rejected/not introduced.

### 7. Report

Update `.ai/report.md` with:

- exact root cause found in code;
- whether it was normalization, currency rates, approved rules, or multiple guarded sites;
- changed files;
- tests run;
- confirmation that no Bitrix write methods were added or called;
- whether frontend build was skipped and why.

## Out Of Scope

- New frontend UI.
- Changing the `crm.item.list` decision from TASK-11.
- Reverting to `crm.deal.list` for normal sync.
- Adding broad `crm.deal.contact.items.get` scans.
- Changing analytics formulas, contact priority rules, revenue/profit/ABC/RFM semantics.
- Automatic refresh, scheduler, queues, or background jobs.
- Bitrix write operations.
- Exporting raw data.

## Constraints

- Work only on current GitHub repository files.
- Bitrix remains read-only.
- Do not add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not request or expose forbidden personal fields.
- Do not print webhook URLs or tokens.
- Do not commit `.env`, local databases, Parquet snapshots, raw exports, logs, caches, build artifacts, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Keep changes backend-focused and minimal.

## Acceptance Criteria

- The reported `executemany requires a non-empty list of parameter sets` class of failure is fixed or converted into a clear safe domain error.
- Empty optional inserts are skipped safely.
- Required empty-data cases produce understandable safe messages.
- Normal refresh still uses `crm.item.list` for deal items.
- Multi-contact links from `contactIds` are still preserved.
- Designer `661` secondary-contact case remains covered by tests.
- No Bitrix write methods are added or called.
- Backend tests pass.
- `.ai/report.md` explains the fix and checks.
- Commit message exactly:

```text
codex: TASK-2026-06-22-12 Fix empty refresh writes
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run backend tests after backend changes:

```bash
cd backend
python -m pytest
```

Use the existing backend dev environment if system Python lacks pytest and document the exact command.

Run frontend build only if frontend code changes:

```bash
cd frontend
npm run build
```

Run safety search before committing:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests
```

Before committing:

```bash
git status --short --branch
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- latest relevant commit is this planner commit;
- direct production `executemany` calls have been audited;
- empty-row behavior is fixed or explicitly made a safe domain error;
- backend tests cover the reported class of failure;
- every required check is either run and reported, or explicitly documented as not run with reason;
- `.ai/report.md` states that no Bitrix write methods were added or called;
- staged files are only task files plus `.ai/report.md`;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
