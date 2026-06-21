# Task: TASK-2026-06-21-05

Status: planned
Created from commit: 46e3961dd336b6ba7ff072837a89e8faef266e93

## Title

Stabilize backend test runtime

## Goal

Make the backend test run complete reliably instead of hanging on the health endpoint test. The desired outcome is a passing `python3 -m pytest` run for the current backend scaffold. If the current host environment still prevents a durable full run, prove the exact remaining blocker and make sure checks fail or skip explicitly rather than hanging.

This task is test/runtime stabilization only. Do not add product analytics, Bitrix integration, storage, frontend, authentication, or deployment features.

## Facts

- `TASK-2026-06-21-04` diagnosed the local verification environment.
- The current environment is WSL2 Ubuntu 24.04.3.
- System Python exists: `/usr/bin/python3`, Python 3.12.3.
- System `pip`, `ensurepip`, and `pytest` are absent.
- `sudo` requires an interactive password, so Codex cannot install `python3-pip` or `python3-venv` system-wide.
- Codex was able to temporarily bootstrap `pip` from official Ubuntu `.deb` packages into `/tmp` without root.
- Codex was able to install backend dev dependencies into a temporary `/tmp` target.
- `python3 -m pytest` collected 6 tests.
- `backend/tests/test_contact_selection.py` passed 5 tests.
- `backend/tests/test_health.py` hung at `fastapi.testclient.TestClient(app).get("/health")`.
- A `faulthandler` probe confirmed the hang occurs inside Starlette/FastAPI TestClient request handling.
- A temporary check with FastAPI 0.128.0 and `httpx2` did not fix the hang; no dependency pin was kept.
- `python3 -m py_compile backend/app/domain/*.py backend/tests/test_*.py` passed.
- Docker Desktop WSL integration is not enabled for this distro, so `docker compose config` still cannot run in this environment.
- Current health endpoint code is in `backend/app/main.py`.
- Current health test is in `backend/tests/test_health.py`.
- Current backend dependencies are in `backend/pyproject.toml`.

## Assumptions

- The health endpoint itself is simple and should be testable without starting a real server.
- The hang is likely caused by the test runtime, dependency interaction, or WSL/temp-target installation behavior rather than product logic.
- It is acceptable to change the health test approach if it still verifies the intended API behavior and avoids hanging.
- It is acceptable to add small test-time safeguards, such as a timeout or explicit skip with a documented reason, if required.
- It is acceptable to adjust backend dev dependencies only if there is a verified compatibility reason.

## Unknowns

- Whether the same `TestClient` hang occurs in a normal venv after host/admin installs `python3-pip` and `python3-venv`.
- Whether the hang is caused by Starlette/FastAPI/httpx compatibility, temporary `/tmp` target installs, WSL filesystem behavior, or another runtime interaction.
- Whether Docker Compose validation will pass after Docker Desktop WSL integration is enabled.

## Scope

1. Inspect the current backend test/runtime files:

```text
backend/app/main.py
backend/app/core/config.py
backend/tests/test_health.py
backend/tests/test_contact_selection.py
backend/pyproject.toml
docs/development.md
.ai/report.md
```

2. Reproduce the current test behavior using the safest available tooling path.

If system `python3 -m pip` is still unavailable, Codex may reuse the documented temporary `/tmp` bootstrap approach from `TASK-2026-06-21-04`, but must not commit temporary dependency folders, caches, `.egg-info`, virtual environments, or generated files.

3. Diagnose why `backend/tests/test_health.py` hangs.

At minimum, check whether the hang is specific to `fastapi.testclient.TestClient` by trying one or more minimal alternatives, for example:

- direct call of the endpoint function if imported safely;
- direct inspection of the FastAPI route registration;
- an alternative ASGI request path if dependencies support it;
- a small isolated TestClient reproduction outside the project app.

Choose the smallest reliable fix that preserves useful coverage.

4. Update tests and/or minimal backend code so that the backend test suite completes.

Preferred outcomes in order:

- `python3 -m pytest` passes all current tests without hanging;
- if full pass is impossible due to host tooling, `python3 -m pytest` completes with a clear failure/skip and no hang;
- if dependency installation itself is impossible, the exact blocker is documented and py_compile still runs.

5. Add a guard against future silent hangs if practical and low-risk.

Examples: a pytest timeout dependency, a local test pattern that avoids the hanging path, or a documented test helper. Do not add heavy infrastructure.

6. Update documentation if commands or test strategy change:

- `docs/development.md` for local test commands/troubleshooting;
- `docs/testing.md` if test strategy or health endpoint test approach changes;
- `backend/README.md` if backend commands change.

7. Update `.ai/report.md` using the `WORKFLOW.md` report format.

## Out Of Scope

- Bitrix integration.
- NBRB currency integration.
- DuckDB schema or Parquet implementation.
- Analytics calculations.
- Report API endpoints beyond existing health endpoint behavior.
- Frontend implementation.
- Design system work.
- Authentication implementation.
- Docker Desktop or host WSL configuration changes.
- CI/GitHub Actions setup.
- Broad dependency modernization without a verified need.
- Committing real secrets, raw Bitrix data, local databases, Parquet snapshots, CSV exports, dependency folders, or virtual environments.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Keep changes narrowly focused on making backend tests reliable.
- Do not change `.ai/task.md` during implementation.
- Do not use `git add .` unless explicitly allowed by the user.
- Do not hide failing checks.
- Do not claim `pytest` passes unless it actually completes and passes.
- Do not leave commands that can hang indefinitely as the recommended verification path.
- Prefer explicit, minimal fixes over broad dependency churn.
- If changing dependencies, explain the reason in `.ai/report.md` and relevant docs.
- Do not implement product functionality in this task.

## Acceptance Criteria

- The health endpoint test no longer hangs silently.
- `python3 -m pytest` either passes all current tests or completes with a clearly documented blocker that is outside Codex control.
- Existing contact selection tests remain intact and pass when tests can run.
- Any dependency or test strategy change is minimal and documented.
- Docs are updated if the backend verification command or troubleshooting guidance changes.
- `.ai/report.md` lists changed files, checks, results, facts, assumptions, unknowns, and next step.
- No real secrets, raw Bitrix data, local databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, or generated artifacts are committed.
- The implementation commit uses the required prefix:

```text
codex: TASK-2026-06-21-05 Stabilize backend test runtime
```

## Checks

Primary desired check from `backend/`:

```bash
python3 -m pytest
```

If dependencies are not installed and system `pip` is unavailable, use the previously documented temporary bootstrap only as needed, then run the equivalent:

```bash
PYTHONPATH=<temporary dependency paths> python3 -m pytest
```

Also run syntax/import-level checks when useful:

```bash
python3 -m py_compile backend/app/**/*.py backend/tests/test_*.py
```

Before committing:

```bash
git status --short
git diff --stat HEAD
```

If Docker is available after host setup, run from repository root:

```bash
docker compose config
```

If Docker remains unavailable because WSL integration is disabled, document that exact blocker; do not block this task on Docker.

## Notes

Before starting implementation, Codex must run:

```bash
git log --oneline -5
git status --short
```

Codex must stop if the latest relevant commit is not a planner commit for this task.

After implementation, Codex must stage only files related to this task and `.ai/report.md`; do not use `git add .` unless explicitly allowed by the user.
