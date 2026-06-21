# Task: TASK-2026-06-21-07

Status: planned
Created from commit: f45754eb3f7abfb7a63fb9e60a860f7792ed25e0

## Title

Implement local normalized pipeline and read API milestone

## Goal

Implement the first meaningful local backend pipeline milestone using only the synthetic fixture and local DuckDB storage:

1. load the synthetic allowed raw data into DuckDB;
2. normalize contact type/region, stage status, and analytical contact assignment;
3. expose minimal read-only API endpoints for health, sync/status-like local dataset status, filters, and contact/deal summaries;
4. cover the milestone with storage-backed tests.

This is a larger backend milestone. It should move the project from static schema/fixtures to a working local data pipeline without real Bitrix integration, without NBRB integration, and without frontend work.

## Facts

- `TASK-2026-06-21-06` added the first DuckDB storage schema scaffold and synthetic fixture dataset.
- Current storage schema tables are:
  - `raw_contacts`;
  - `raw_deals`;
  - `raw_deal_contact_links`;
  - `raw_stages`;
  - `contact_type_rules`;
  - `currency_rates`.
- Current fixture is `backend/tests/fixtures/synthetic_dataset.py`.
- Current fixture contains 10 contacts, 30 deals, won/open/lost statuses, several currencies, multi-contact deal, deal without contact, equal type priorities, old high-value contact scenario, single-won-deal contact, and long-open deal.
- Current domain logic includes `select_analytical_contact()`.
- `SPEC.md` requires periods and reports to be calculated from local data, not by querying Bitrix.
- `SPEC.md` requires one analytical contact per deal for contact analytics.
- `SPEC.md` requires contact type and region to be driven by configuration/local data, not hardcoded production constants.
- `SPEC.md` requires deals without contacts to be preserved and shown as `Без контакта` or `Не определено` depending on report context.
- `SPEC.md` forbids phones, emails, addresses, messengers, requisites, comments, files, activity fields, and arbitrary non-allowlisted Bitrix fields.
- Real Bitrix integration, real field codes, real stages, real currencies, and real type/region mapping are still unknown.

## Assumptions

- The synthetic fixture is the source of truth for this milestone.
- It is acceptable to add normalized DuckDB tables to the current schema because normalization is now in scope.
- It is acceptable to keep API endpoints minimal and read-only, focused on proving the local pipeline shape.
- It is acceptable to use direct DuckDB queries or small repository/service functions before designing final production repository abstractions.
- It is acceptable to implement a manual local fixture load function for tests and development, but it must not pretend to be real Bitrix sync.
- Currency conversion can remain out of scope except preserving original currency/rate tables and documenting that USD conversion comes later.

## Unknowns

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual contact type values, priorities, and region mapping.
- Actual pipelines, stages, and currencies in Bitrix.
- Final production storage layout, migration strategy, dataset activation mechanics, and Parquet snapshot format.
- Final frontend response-shape needs beyond the API contract in `SPEC.md`.

## Scope

Implement this as a coherent backend milestone. Prefer small modules with clear names over one large file. Follow existing style.

### 1. Extend Storage Schema

Extend `backend/app/storage/schema.py` to include normalized/local pipeline tables needed for this milestone.

At minimum, add tables that can represent:

- normalized contacts with `contact_id`, `contact_name`, `contact_type_raw`, `contact_type_normalized`, `region_normalized`;
- normalized deals with original deal fields plus `status_group`, `analytical_contact_id`, `analytical_contact_name`, `contact_type_normalized`, `region_normalized`;
- a small local dataset status table or equivalent storing status information for the current local fixture dataset.

Keep raw tables from `TASK-06` intact. Do not add forbidden personal fields.

### 2. Add Storage Load Helpers

Add a storage module that can load the synthetic fixture into the raw tables and clear/reload current local test data idempotently.

Suggested API shape, adjust if a better local pattern emerges:

```python
load_synthetic_dataset(connection, dataset) -> None
```

Requirements:

- insert contacts, deals, deal-contact links, stages, contact type rules, and currency rates;
- be deterministic and idempotent for tests;
- avoid generated files and avoid local DB files in git;
- avoid broad abstractions that are not needed yet.

### 3. Add Normalization Pipeline

Add a backend normalization module that transforms raw tables into normalized tables.

Minimum behavior:

- normalize contact type and region using active `contact_type_rules`;
- use `Не определено` for unknown/missing contact type or region;
- derive/verify deal `status_group` using `raw_stages` with `stage_id` and `category_id` where available;
- select one `analytical_contact_id` per deal using the existing `select_analytical_contact()` rules;
- preserve deals without contacts with `analytical_contact_id = NULL`, `analytical_contact_name = 'Без контакта'`, and normalized type/region as `Не определено`;
- ensure each deal appears exactly once in the normalized deals table;
- do not calculate currency conversion, ABC, RFM, reactivation, stale-deal thresholds, or concentration yet.

### 4. Add Local Pipeline Orchestration

Add a small orchestration function for tests/dev that initializes schema, loads the synthetic dataset, runs normalization, and returns useful status counts.

Suggested API shape, adjust if useful:

```python
run_synthetic_pipeline(connection) -> PipelineStatus
```

The status should include at least counts for contacts, deals, links, normalized contacts, normalized deals, and a `success`/`error`-like state appropriate for local fixture execution.

Do not name this real Bitrix sync. It is a local synthetic pipeline.

### 5. Add Minimal Read API Endpoints

Implement read-only FastAPI endpoints backed by the local synthetic pipeline, with no external calls.

Required endpoints for this milestone:

- `GET /api/sync/status` — return current local pipeline status. It may report fixture status until real Bitrix sync exists.
- `POST /api/sync/run` — for now, run the local synthetic pipeline only. The response and docs must clearly indicate it is synthetic/local, not Bitrix.
- `GET /api/meta/filters` — return available contact types, regions, statuses, and simple period metadata from normalized/local data.
- `GET /api/reports/contacts` — return paginated normalized contact summary rows with local filters/search where practical.
- `GET /api/reports/stale-deals` or `GET /api/reports/deal-cycle` may remain unimplemented if doing both would bloat the task; if omitted, return a documented 501-style response only if an endpoint stub already exists. Do not create broad report stubs just for appearance.

API constraints:

- endpoints must use local DuckDB data only;
- no Bitrix calls;
- no forbidden fields in responses;
- responses should be Pydantic-typed where practical;
- keep response shapes simple and documented in code/docs.

Storage for the API can be in-memory for this milestone if that keeps the implementation reliable. If using a file path, it must be configurable and ignored by git.

### 6. Add Tests

Add storage-backed tests for the whole milestone.

Minimum coverage:

- synthetic pipeline initializes, loads, normalizes, and returns expected counts;
- normalized contacts contain expected type/region mappings and `Не определено` fallback;
- normalized deals contain exactly one row per deal;
- deal with multiple contacts resolves to the expected analytical contact by type priority / primary / id tie-break rules;
- deal without contact is preserved as `Без контакта` with `Не определено` type/region;
- won/open/lost statuses are represented correctly from stages;
- API status, filters, and contacts endpoints return local data without forbidden fields;
- existing health, contact selection, storage schema, and fixture tests still pass.

### 7. Documentation

Update documentation concisely:

- `docs/data-model.md` — normalized tables and local synthetic pipeline state;
- `docs/project-status.md` — current phase and next real milestone;
- `docs/testing.md` — storage-backed pipeline/API tests;
- `docs/development.md` or `backend/README.md` — how to run the local synthetic pipeline/API if commands change;
- `.ai/report.md` — full implementation report.

## Out Of Scope

- Real Bitrix integration.
- Bitrix API clients, real webhook calls, pagination, retries, or allowlist discovery.
- NBRB API integration and real currency conversion.
- Parquet snapshot writing.
- Production dataset activation/swap mechanics.
- ABC, ABC migration, RFM, reactivation, stale-deal thresholds, concentration analytics, and financial reports beyond simple local contact/deal summaries.
- Frontend implementation.
- Design system work.
- Authentication implementation.
- CI/GitHub Actions setup.
- Production deployment, HTTPS, backups.
- Complex repository/migration framework unless required by the implementation.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Keep all data synthetic and local.
- Do not query Bitrix or external APIs.
- Do not invent real Bitrix field codes or present synthetic values as real production config.
- Do not add forbidden personal fields anywhere in schema, fixtures, API responses, docs, logs, or tests.
- Do not commit local DuckDB database files, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, generated artifacts, raw data, or secrets.
- Do not implement frontend screens before design system approval.
- Prefer explicit code over broad frameworks.
- Keep the milestone coherent: raw load -> normalize -> read API -> tests -> docs.

## Acceptance Criteria

- Raw fixture data can be loaded into DuckDB idempotently.
- Normalized contacts and deals are generated from local raw tables.
- Contact type and region normalization works with active rules and `Не определено` fallback.
- Analytical contact assignment works and each deal appears once in normalized deals.
- Deal without contact is preserved as `Без контакта` and `Не определено`.
- Status groups are represented correctly for won/open/lost synthetic deals.
- Minimal local read API endpoints work against local DuckDB data and return no forbidden fields.
- Storage-backed tests cover pipeline and API behavior.
- Existing tests continue to pass.
- Documentation and `.ai/report.md` reflect the new milestone.
- No real secrets, raw data, databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, or generated artifacts are committed.
- The implementation commit uses the required prefix:

```text
codex: TASK-2026-06-21-07 Implement local normalized pipeline and read API milestone
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
