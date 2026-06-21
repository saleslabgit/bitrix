# Task: TASK-2026-06-21-06

Status: planned
Created from commit: 1400ba4269be6fe7e3b1b64c37eb05ac47404517

## Title

Add storage schema and synthetic fixture scaffold

## Goal

Add the first local data-layer scaffold for the backend: a minimal DuckDB schema initializer for allowed MVP data tables and a fully synthetic integration fixture dataset that future normalization and analytics tests can reuse.

This task should make the project ready for the next step: implementing normalization rules and storage-backed pipeline tests. Do not connect to Bitrix, fetch real data, write Parquet snapshots, or implement analytics calculations in this task.

## Facts

- `TASK-2026-06-21-05` stabilized backend tests.
- Backend tests now complete: 7 tests passed in the latest report.
- Docker Compose config also passed after host tooling was enabled.
- Current backend domain scaffold exists under `backend/app/domain/`.
- Current domain models include:
  - `ContactSnapshot`;
  - `DealSnapshot`;
  - `DealContactLink`;
  - `StageSnapshot`;
  - `ContactTypeRule`;
  - `CurrencyRateSnapshot`.
- Current pure domain logic includes analytical contact selection in `backend/app/domain/contact_selection.py`.
- `docs/fixtures.md` defines the future synthetic integration fixture requirements.
- `docs/project-status.md` says the next likely steps are local storage schema, synthetic integration fixture data, and first normalization tests.
- `SPEC.md` requires local storage of raw and normalized data, but real Bitrix integration is not implemented yet.
- `SPEC.md` forbids downloading or storing phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.
- No real Bitrix field codes, contact type values, priorities, region mapping, pipelines, stages, or real currencies have been confirmed from production data yet.

## Assumptions

- DuckDB is already a backend dependency and can be used for the first storage schema scaffold.
- The first schema can be minimal and focused on allowed MVP entities, without final migration tooling.
- Synthetic fixture values may use invented contact names, deal names, stage IDs, currencies, type raw values, priorities, and regions as long as they are clearly fake and documented as test-only.
- Raw data tables should represent allowed Bitrix-shaped snapshots, not forbidden personal/contact fields.
- Normalized and analytics tables can be documented as future work unless a very small placeholder is needed for schema clarity.

## Unknowns

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual Bitrix contact type values, priorities, and region mapping.
- Actual pipelines, stages, and currencies in Bitrix.
- Final production storage layout, migration strategy, and dataset activation mechanics.
- Whether future Parquet raw snapshots will mirror the DuckDB table names exactly.

## Scope

1. Add a storage package under `backend/app/storage/`.

Suggested structure:

```text
backend/app/storage/
  __init__.py
  schema.py
```

The package should expose a minimal, explicit API such as:

```python
initialize_schema(connection: duckdb.DuckDBPyConnection) -> None
list_expected_tables() -> tuple[str, ...]
```

Use the existing project style and keep the API small.

2. Implement DuckDB schema creation for allowed MVP data tables.

At minimum, create tables for:

- raw contacts;
- raw deals;
- raw deal-contact links;
- raw stages;
- contact type rules;
- currency rates.

Use clear table names and column names that match the existing domain models where practical. Include only allowed MVP fields.

Do not create columns for phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.

3. Add storage tests.

Create focused tests that verify:

- schema initialization runs on an in-memory DuckDB connection;
- all expected tables are created;
- expected columns exist for each table;
- forbidden field names are not present in any created table;
- schema initialization is idempotent when called more than once.

4. Add a synthetic integration fixture dataset.

Suggested location:

```text
backend/tests/fixtures/synthetic_dataset.py
```

The fixture should be pure Python test data using existing domain models or simple helper functions returning existing domain models.

It must include at least:

- 10 contacts;
- 30 deals;
- won, open, and lost deals;
- several currencies;
- at least one deal linked to multiple contacts;
- equal contact type priorities;
- at least one deal without any contact;
- one would-be A-segment contact without sales in the last 12 months;
- one contact with a single won deal;
- one long-open deal.

The dataset must be synthetic and must not contain real Bitrix data or personal contact fields.

5. Add fixture validation tests.

Create tests that verify the synthetic fixture satisfies the minimum shape requirements above and uses only allowed domain fields. These tests should not calculate ABC, RFM, currency conversion, or stale-deal analytics yet.

6. Keep documentation current.

Update concise documentation where relevant:

- `docs/data-model.md` for the new storage schema scaffold;
- `docs/fixtures.md` for the now-implemented synthetic fixture location and coverage;
- `docs/project-status.md` for current stage and next likely steps;
- `docs/testing.md` for new test coverage;
- `backend/README.md` for the new storage package map if useful.

7. Update `.ai/report.md` using the `WORKFLOW.md` report format.

## Out Of Scope

- Real Bitrix integration.
- Bitrix API clients, webhooks, pagination, retries, or field allowlist discovery.
- NBRB currency API integration.
- Real currency conversion logic.
- Parquet snapshot writing.
- Dataset activation/swap mechanics.
- Normalization implementation beyond table/fixture preparation.
- ABC, ABC migration, RFM, reactivation, type/region analytics, deal-cycle, stale-deal, or concentration calculations.
- Report API endpoints.
- Authentication.
- Frontend implementation.
- Design system work.
- CI/GitHub Actions setup.
- Production deployment, HTTPS, or backups.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Keep changes focused on storage schema and synthetic fixture scaffold.
- Do not change `.ai/task.md` during implementation.
- Do not use `git add .` unless explicitly allowed by the user.
- Do not invent real Bitrix field codes or present synthetic values as real values.
- Do not hardcode future production contact type priorities or region rules outside synthetic test data.
- Do not include forbidden personal fields anywhere in schema, fixtures, docs, tests, logs, or reports.
- Do not commit real secrets, raw Bitrix data, local databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, or generated artifacts.
- Prefer explicit table and column definitions over clever dynamic schema generation.
- Keep documentation concise and operational.

## Acceptance Criteria

- `backend/app/storage/` exists and exposes a small schema initialization API.
- DuckDB schema initialization creates all required MVP scaffold tables.
- Schema initialization is idempotent.
- Tests verify expected table names and columns.
- Tests verify forbidden field names are absent from schema columns.
- A synthetic integration fixture exists and satisfies the minimum dataset shape from `SPEC.md`/`docs/fixtures.md`.
- Fixture validation tests pass without real Bitrix data or forbidden personal fields.
- Existing health and contact selection tests still pass.
- Documentation reflects the new storage schema and fixture scaffold.
- `.ai/report.md` lists changed files, checks, results, facts, assumptions, unknowns, and next step.
- No real secrets, raw data, databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, or generated artifacts are committed.
- The implementation commit uses the required prefix:

```text
codex: TASK-2026-06-21-06 Add storage schema and synthetic fixture scaffold
```

## Checks

Run from `backend/`:

```bash
python3 -m pytest
```

Run syntax/import-level checks if useful:

```bash
python3 -m py_compile app/**/*.py tests/**/*.py
```

Run from repository root:

```bash
docker compose config
```

Before committing:

```bash
git status --short
git diff --stat HEAD
```

If any check cannot be run, document the exact reason in `.ai/report.md`.

## Notes

Before starting implementation, Codex must run:

```bash
git log --oneline -5
git status --short
```

Codex must stop if the latest relevant commit is not a planner commit for this task.

After implementation, Codex must stage only files related to this task and `.ai/report.md`; do not use `git add .` unless explicitly allowed by the user.
