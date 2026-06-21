# Task: TASK-2026-06-21-02

Status: planned
Created from commit: 028f10bddf3485003b8218389a8a37578be169de

## Title

Verify scaffold checks and dev setup docs

## Goal

Close the verification gap from `TASK-2026-06-21-01` by documenting the exact development dependency installation flow and running the relevant scaffold checks in an environment that has the required tooling available.

This is a narrow follow-up task. Do not add product functionality.

## Facts

- `TASK-2026-06-21-01` created the initial scaffold and documentation backbone.
- The latest implementation commit is `codex: TASK-2026-06-21-01 Initialize project scaffold and documentation backbone`.
- `.ai/report.md` for `TASK-2026-06-21-01` says `python3 -m py_compile backend/app/main.py backend/app/core/config.py backend/tests/test_health.py` passed.
- `.ai/report.md` also says `cd backend && pytest` was not run because `pytest`, `fastapi`, and `pip` were unavailable in that environment.
- `.ai/report.md` says `docker compose config` was not run because Docker was unavailable in that environment.
- `backend/pyproject.toml` already defines dev dependencies under `[project.optional-dependencies].dev`.
- Current docs mention `pytest`, but do not clearly document installing dev dependencies first.
- Frontend implementation is still blocked until the design system is approved.

## Assumptions

- The intended local backend dev setup is an editable install with dev extras:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

- Docker Compose should be validated from the repository root with:

```bash
docker compose config
```

## Unknowns

- Whether the current Codex runtime has `pip` and network access for package installation.
- Whether the current Codex runtime has Docker available.
- Whether the scaffold has hidden dependency/configuration issues that only appear after installing dependencies and running tests.

## Scope

Make only the smallest documentation and verification changes needed to make the scaffold checkable.

Required work:

1. Update developer-facing documentation to include the dev dependency installation step before running pytest:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

2. Update any relevant command sections in:

- `README.md`
- `backend/README.md`
- `docs/development.md`
- `docs/testing.md`

3. If the existing code or packaging has a small issue that prevents `pytest` from passing after installing documented dependencies, fix only that issue.

4. Run the relevant checks:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

5. From the repository root, run if Docker is available:

```bash
docker compose config
```

6. Update `.ai/report.md` for this task using the report format from `WORKFLOW.md`.

## Out Of Scope

- New backend endpoints.
- Bitrix integration.
- NBRB currency integration.
- DuckDB schemas.
- Parquet snapshots.
- Analytics calculations.
- Authentication.
- Frontend implementation.
- Design-system implementation.
- CI setup.
- Production deployment.
- Broad refactoring.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Keep the diff minimal and focused on documentation/check verification.
- Do not change `.ai/task.md` during implementation.
- Do not add real secrets, real Bitrix data, raw exports, local databases, Parquet snapshots, or CSV exports.
- Do not use `git add .` unless explicitly allowed by the user.
- If a check cannot be run, explain the exact reason in `.ai/report.md`.
- If package installation fails due to runtime/network/tooling limits, document the failure and do not invent a successful result.

## Acceptance Criteria

- Docs clearly tell a developer how to install backend dev dependencies before running pytest.
- `README.md`, `backend/README.md`, `docs/development.md`, and `docs/testing.md` are consistent about backend test commands.
- `pytest` is run after installing dev dependencies, or the exact blocker is documented in `.ai/report.md`.
- `docker compose config` is run if Docker is available, or the exact blocker is documented in `.ai/report.md`.
- Any code/package fix, if needed, is narrowly scoped to making the existing health endpoint test pass.
- `.ai/report.md` lists changed files, checks run, acceptance status, remaining unknowns, and next step.
- The implementation commit uses the required prefix:

```text
codex: TASK-2026-06-21-02 Verify scaffold checks and dev setup docs
```

## Checks

Required:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

Required if Docker is available:

```bash
docker compose config
```

Before committing:

```bash
git status --short
git diff --stat HEAD
```

## Notes

Before starting implementation, Codex must run:

```bash
git log --oneline -5
git status --short
```

Codex must stop if the latest relevant commit is not a planner commit for this task.

After implementation, Codex must stage only files related to this task and `.ai/report.md`; do not use `git add .` unless explicitly allowed by the user.
