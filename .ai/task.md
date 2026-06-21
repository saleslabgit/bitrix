# Task: TASK-2026-06-21-09

Status: planned
Created from commit: 1e78985bc728644eb539946f3cfb72903dd90da2

## Title

Implement Bitrix read-only ingestion and allowlist discovery milestone

## Goal

Implement the first real Bitrix data boundary for the MVP: a safe read-only Bitrix client, explicit field allowlists, metadata discovery for required CRM fields, and a manual ingestion pipeline that can load allowed Bitrix contacts, deals, deal-contact links, and stage dictionaries into local raw DuckDB tables.

This is a backend/data milestone before frontend work. It must not implement UI, authentication, NBRB integration, Parquet snapshots, production dataset activation, or scheduled sync.

## Facts

- TASK-07 added local synthetic raw loading, normalization, status, and minimal read API endpoints.
- TASK-08 added local analytics over normalized DuckDB data and typed report endpoints.
- Current real Bitrix access method and webhook URL are unknown.
- Bitrix must be read-only for this project.
- The MVP main analytics entity is the contact.
- The current local schema has raw tables for contacts, deals, deal-contact links, stages, contact type rules, and currency rates.
- The current normalized and analytics layers run from local tables, not from Bitrix directly.
- `SPEC.md` and `docs/data-model.md` forbid phones, emails, addresses, messengers, requisites, comments, files, activities, and arbitrary non-allowlisted fields.
- The contact type field code is unknown and must be discoverable/configurable, not invented.
- `ui-kits/` exists for future frontend implementation, but it is not in scope for this backend task.

## Assumptions

- Bitrix webhook will be provided through environment variables, never committed.
- Tests must not require live Bitrix access; they should mock the Bitrix API boundary.
- If live Bitrix environment variables are absent, commands/tests must still pass using mocked or synthetic data.
- A manual live ingestion command/function may be added, but it must fail safely when credentials are missing.
- The first real ingestion may store only allowlisted raw fields into DuckDB raw tables; normalization can reuse existing code where possible.
- Parquet snapshots and production dataset activation are a later milestone unless a tiny interface is needed to keep the ingestion code clean.

## Unknowns

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual production contact type values, priorities, and region mapping.
- Actual production pipelines, stage IDs, category IDs, currencies, and deal-contact link behavior.
- Whether Bitrix account permissions allow all required read-only methods.
- Final production storage layout, migration strategy, dataset activation mechanics, and Parquet snapshot format.

## Scope

Build this as one coherent backend/data milestone. Prefer explicit modules and narrow tests over broad abstractions.

### 1. Add Bitrix Settings

Extend backend settings safely.

Minimum expected settings:

- `BITRIX_WEBHOOK_URL` or equivalent secret-backed webhook base URL;
- optional `BITRIX_CONTACT_TYPE_FIELD` for the configured contact type field code;
- optional page size/batch size if needed;
- no secret values in docs, tests, logs, API responses, or committed files.

Settings must allow tests to run without live credentials.

### 2. Add Read-Only Bitrix Client

Add a backend Bitrix client module for read-only REST access.

Minimum behavior:

- call Bitrix methods by name through the webhook base URL;
- support pagination for list methods;
- support deterministic request construction and response parsing;
- expose narrow methods for this milestone rather than a generic write-capable API;
- never implement create/update/delete Bitrix calls;
- avoid logging full webhook URLs or secrets;
- raise explicit safe errors for missing credentials, HTTP errors, Bitrix response errors, and unexpected response shapes.

Suggested read methods, adjust to actual Bitrix API shape if needed:

- CRM contact fields discovery;
- CRM deal fields discovery;
- contact list with allowlisted select fields;
- deal list with allowlisted select fields;
- deal-contact links for loaded deals;
- deal category/stage dictionaries or status lists needed to derive `won/open/lost`.

### 3. Define Field Allowlists

Add a single source of truth for allowed Bitrix fields.

Minimum behavior:

- contacts allow only ID, display-name pieces, and configured contact type field when explicitly configured;
- deals allow only ID, title/name, amount, currency, created/closed dates, stage, category/status fields needed by the MVP;
- links allow only deal ID, contact ID, primary/sort/role fields if Bitrix returns them;
- stages allow only IDs, category, names/status semantics needed for `won/open/lost` derivation;
- forbid phones, emails, addresses, messengers, requisites, comments, files, activities, timeline, product rows, arbitrary UF fields outside the configured contact type field;
- tests must prove forbidden fields are not requested or stored.

### 4. Add Discovery Output

Add a small discovery function/report for Bitrix metadata.

Minimum behavior:

- discover available contact fields and deal fields through read-only metadata calls;
- identify whether configured `BITRIX_CONTACT_TYPE_FIELD` exists;
- report missing/unknown required fields without failing destructively;
- return a safe structured result that does not include secret values or forbidden field values;
- document how to use discovery to choose the contact type field.

This can be a Python service function and/or a backend endpoint/CLI-style helper. Keep it minimal.

### 5. Add Manual Raw Ingestion Pipeline

Add a manual ingestion orchestration function that loads allowed Bitrix data into local raw DuckDB tables.

Minimum behavior:

- initialize local schema;
- fetch allowed contacts;
- fetch allowed deals;
- fetch deal-contact links for fetched deals;
- fetch stage/category dictionaries needed for status grouping;
- transform Bitrix payloads into existing raw table shapes;
- clear/reload raw tables idempotently for the current manual dataset;
- run existing normalization after raw load if safe;
- store/update a sync status row or equivalent status object with counts, timestamps, state, and safe error message;
- never store forbidden fields;
- never commit raw data or local database files.

If schema changes are needed, keep them minimal and documented. Do not break existing synthetic pipeline tests.

### 6. Add API/Command Surface For Backend Use

Expose a minimal backend-accessible surface for manual operations.

Options:

- service functions only plus tests; or
- typed FastAPI endpoints such as `GET /api/bitrix/discovery`, `POST /api/bitrix/sync/run`, `GET /api/bitrix/sync/status`.

If endpoints are added:

- they must be typed with Pydantic models;
- they must not expose secrets;
- they must fail safely when `BITRIX_WEBHOOK_URL` is missing;
- they must not replace the existing local synthetic endpoints unless clearly documented.

### 7. Tests

Add focused tests for the real Bitrix boundary using mocked responses.

Minimum coverage:

- Bitrix client constructs read-only method URLs/requests without exposing secrets;
- pagination is handled correctly;
- Bitrix API errors produce safe exceptions/statuses;
- allowlist select fields do not include forbidden field names;
- configured contact type field is included only when explicitly configured;
- discovery reports present/missing contact type field correctly;
- mocked contact/deal/link/stage payloads load into raw tables correctly;
- forbidden fields in mocked Bitrix responses are ignored and not stored;
- manual ingestion is idempotent;
- normalization still produces normalized contacts/deals from mocked Bitrix raw load where possible;
- missing credentials do not break the regular test suite;
- existing synthetic pipeline, analytics, and API tests continue to pass.

### 8. Documentation

Update documentation concisely:

- `docs/data-model.md` — document real Bitrix raw ingestion boundary and allowlisted fields;
- `docs/development.md` or `backend/README.md` — document environment variables and manual discovery/sync commands/endpoints;
- `docs/project-status.md` — update current phase, done/not done, and next likely milestone;
- `docs/testing.md` — document mocked Bitrix boundary tests and live-access expectations;
- `.ai/report.md` — full implementation report with changed files, checks, facts, assumptions, unknowns, and next step.

Do not edit `ui-kits/` in this task.

## Out Of Scope

- Frontend implementation.
- Using `ui-kits/` in production UI.
- Writing back to Bitrix.
- Leads, companies, products, activities, comments, calls, emails, files, product rows, Roistat, CSV export.
- NBRB integration and production currency update logic.
- Parquet snapshot writing unless strictly necessary as a tiny placeholder interface.
- Production dataset activation/swap mechanics.
- Automatic scheduled sync.
- Authentication and roles.
- CI/GitHub Actions setup.
- Production deployment, HTTPS, backups.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Bitrix access is strictly read-only.
- Do not query Bitrix from tests; use mocked responses.
- Live Bitrix calls may only happen through explicit manual functions/endpoints and only when credentials are present.
- Do not invent real Bitrix field codes.
- Do not include secrets, raw Bitrix data, local DB files, Parquet snapshots, CSV files, dependency folders, virtual environments, caches, generated artifacts, or frontend builds in git.
- Do not include forbidden personal/out-of-scope fields in schema, fixtures, API responses, docs, logs, or tests except as negative test input proving they are ignored.
- Do not modify `ui-kits/`.
- Keep implementation explicit and testable.

## Acceptance Criteria

- Bitrix settings are added safely and tests run without live credentials.
- Read-only Bitrix client supports the required mocked metadata/list/link/stage flows.
- Field allowlists are centralized and tested.
- Forbidden fields are not requested and are ignored if present in mocked responses.
- Discovery can report configured contact type field presence/missing status safely.
- Manual mocked ingestion loads contacts, deals, links, and stages into raw DuckDB tables idempotently.
- Existing normalization can run after mocked Bitrix raw ingestion where possible.
- Sync/discovery status surfaces expose counts/errors without secrets.
- Existing synthetic pipeline, analytics, and API tests continue to pass.
- Documentation and `.ai/report.md` reflect the new real Bitrix boundary milestone.
- No real secrets, raw Bitrix data, databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, generated artifacts, frontend builds, or `ui-kits/` changes are committed.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-21-09 Implement Bitrix read-only ingestion and allowlist discovery milestone
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

If dependencies are not installed in the current environment, install the backend dev package first:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Run syntax/import-level checks if useful:

```bash
python -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py
```

Run from repository root:

```bash
docker compose config
```

Before committing:

```bash
git status --short
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

If `docker compose config` or any required check cannot be run, document the exact reason in `.ai/report.md`.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- the latest relevant commit is this planner commit;
- `.ai/report.md` is updated;
- every required check is either run and reported, or explicitly documented as not run with reason;
- staged files are only files intentionally changed for TASK-09 plus `.ai/report.md`;
- `AGENTS.md`, `.ai/task.md`, and `ui-kits/` are not staged unless the task explicitly required changing them;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
