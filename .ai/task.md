# Task: TASK-2026-06-21-11

Status: planned
Created from commit: 51faa0e810b620133334f91d42437f848222f715

## Title

Implement persistent dataset storage milestone

## Goal

Move the backend from process-local/in-memory data toward a real local analytics store that can survive restarts and safely hold manually loaded Bitrix datasets.

This is a backend/data milestone before frontend work. It should make the existing synthetic and Bitrix pipelines use a configurable DuckDB storage boundary, add safe dataset activation semantics for manual Bitrix ingestion, and write allowlisted raw snapshots to Parquet for traceability without committing data files.

Do not implement NBRB integration, authentication, frontend, scheduler, live Bitrix smoke tests, CI, deployment, or write-back to Bitrix in this task.

## Context

- TASK-07 added local synthetic raw loading, normalization, status, and minimal read API endpoints.
- TASK-08 added local analytics endpoints over normalized DuckDB data.
- TASK-09 added a read-only Bitrix client, allowlists, discovery, and manual mocked Bitrix ingestion into existing raw tables.
- TASK-10 corrected the TASK-09 workflow report gate.
- Current docs still mark production dataset activation and Parquet snapshots as not done.
- Current API/data behavior is still too close to in-memory scaffolding for a real first export.

## Product Intent

After this task, the backend should be ready for a real operator flow in a local environment:

```text
configure env -> start backend -> run discovery -> configure contact type field -> run manual Bitrix sync -> data persists locally -> analytics endpoints read the active local dataset
```

Tests must still run without live Bitrix credentials and without writing real raw data into git.

## Scope

Build this as one coherent storage milestone. Prefer explicit, boring storage code over broad abstractions.

### 1. Persistent DuckDB Storage Boundary

Add configurable local storage settings and a connection boundary.

Minimum expected behavior:

- Add settings for a local data directory and DuckDB database path, for example `APP_DATA_DIR` and/or `APP_DUCKDB_PATH`.
- Default local runtime should use a persistent path under a gitignored local data directory.
- Tests must still be able to use isolated in-memory or temporary DuckDB databases.
- Backend startup/API code should initialize the schema before reading or writing.
- Existing API endpoints should continue to use the shared configured connection unless tests inject isolated connections.
- Do not commit local database files.

### 2. Dataset Run And Activation Semantics

Make manual Bitrix ingestion safer than direct destructive replacement of the active dataset.

Minimum expected behavior:

- Represent each pipeline run with a clear dataset/run identity, state, timestamps, counts, and safe message.
- A failed manual Bitrix run must not leave the active normalized dataset half-replaced.
- A successful manual Bitrix run should become the active local dataset for read/report endpoints.
- Existing synthetic pipeline may remain available as a local fixture/dev dataset, but active dataset semantics must be documented.
- The current `local_dataset_status` approach may be extended or replaced if needed, but keep migrations/simple schema changes testable.
- If full staging-table swap is too large for one task, implement a minimal transaction-backed approach that guarantees no committed partial raw/normalized replacement on handled failures.

### 3. Raw Parquet Snapshots For Allowed Data

Add raw snapshot writing for successfully loaded local datasets.

Minimum expected behavior:

- Write Parquet snapshots for allowlisted raw tables after successful synthetic or Bitrix ingestion.
- Snapshot output must include only allowed local raw tables and columns already in the schema.
- Snapshot paths must live under the configured local data directory.
- Snapshot filenames/directories should be deterministic enough to inspect but unique enough per run, for example by dataset/run id and timestamp.
- Never write or commit forbidden Bitrix fields, secrets, local DB files, CSV exports, dependency folders, caches, or frontend builds.
- Tests must verify snapshot files are created for mocked data and contain only expected columns.

### 4. API/Status Surface

Expose enough typed backend status for operator and future frontend use.

Minimum expected behavior:

- Existing sync status endpoints continue to work.
- Add or extend a typed endpoint/service that reports the active dataset and latest run status, including dataset kind, state, counts, timestamps, and safe message.
- Status responses must not expose secrets, raw rows, webhook URLs, file contents, or local absolute paths if those paths could leak environment details. Relative/logical snapshot identifiers are acceptable.
- Existing analytics/report endpoints should read from the active configured local store.

### 5. Tests

Add focused tests that prove the storage milestone works without live credentials.

Minimum coverage:

- Configured DuckDB storage can use a temporary file path and persists data across new connections.
- Tests can still use isolated in-memory/temp stores without cross-test contamination.
- Schema initialization is idempotent for persistent storage.
- Synthetic pipeline still works.
- Mocked Bitrix ingestion still works.
- Failed mocked Bitrix ingestion does not activate a partial dataset or destroy the previous successful active dataset.
- Successful mocked Bitrix ingestion activates the dataset and existing analytics/read endpoints can read it.
- Raw Parquet snapshots are created only for allowed raw tables/columns.
- Status endpoint/service returns active dataset/latest run metadata without secrets or raw rows.

### 6. Documentation And AGENTS.md

Update project documentation so the next agent can orient quickly.

Minimum documentation updates:

- `docs/data-model.md` — describe persistent DuckDB storage, dataset activation, and raw snapshot boundaries.
- `docs/development.md` and/or `backend/README.md` — document local data env vars, safe local run flow, and where generated data lives.
- `docs/project-status.md` — update done/not done/next steps.
- `docs/testing.md` — document persistent storage and snapshot tests.
- `.ai/report.md` — full implementation report with changed files, checks, facts, assumptions, unknowns, and next step.
- `AGENTS.md` — update only if needed so Codex has accurate instructions about current storage, generated files, and workflow. Keep it concise; do not churn unrelated sections.

## Out Of Scope

- Live Bitrix smoke test against a real account.
- NBRB currency integration and production missing-rate policy.
- Authentication and roles.
- Frontend implementation or `ui-kits/` usage.
- Scheduler/automatic sync.
- Persisted analytics output tables unless a tiny metadata table is needed for activation.
- Complex migration framework if simple idempotent schema updates are enough.
- CSV export.
- Companies, leads, products, activities, comments, calls, emails, files, Roistat.
- Writing back to Bitrix.
- CI/GitHub Actions setup.
- Production deployment, HTTPS, backups.

## Constraints

- Follow `AGENTS.md`, `docs/workflow.md`, and current `.ai/task.md`.
- Bitrix access remains strictly read-only.
- Do not run live Bitrix calls in tests.
- Do not invent real Bitrix field codes or contact type mappings.
- Do not commit generated local data: DuckDB files, Parquet snapshots, CSV files, raw exports, env files, caches, virtual environments, dependency folders, or frontend builds.
- Do not include forbidden Bitrix fields in storage, snapshots, API responses, docs, logs, or tests except as negative test input proving they are ignored.
- Do not modify `ui-kits/`.
- Keep existing endpoints backward-compatible unless the docs and tests clearly justify a compatible extension.
- If a design choice affects product semantics, data safety, or future frontend contract and is not clear from docs, stop and ask before committing.

## Acceptance Criteria

- Backend has configurable persistent DuckDB storage for local runtime.
- Tests can use isolated in-memory/temp storage.
- Schema initialization is idempotent for persistent storage.
- Existing synthetic pipeline still passes tests.
- Mocked Bitrix ingestion still passes tests.
- Successful Bitrix ingestion activates a local dataset for read/report endpoints.
- Failed Bitrix ingestion does not leave a partial active dataset or destroy the previous active dataset.
- Raw Parquet snapshots are written for allowed raw tables/columns after successful ingestion.
- Generated storage/snapshot artifacts are gitignored and not committed.
- Typed status surface reports active/latest dataset metadata without secrets/raw rows/local sensitive paths.
- Documentation and `.ai/report.md` accurately describe persistent storage, snapshots, activation, checks, assumptions, and next step.
- `AGENTS.md` is updated if current agent instructions would otherwise be stale or misleading.
- No frontend, `ui-kits/`, live Bitrix, NBRB, auth, scheduler, or deployment work is included.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-21-11 Implement persistent dataset storage milestone
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

If dependencies are not installed in the current environment, install/use the existing backend dev environment and document the exact command used.

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
- staged files are only files intentionally changed for TASK-11 plus `.ai/report.md`;
- `ui-kits/` is not staged;
- generated local data artifacts are not staged;
- `.ai/task.md` is not staged unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
