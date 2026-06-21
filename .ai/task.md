# Task: TASK-2026-06-21-04

Status: planned
Created from commit: b7725fee5ce9e838c93e38ae0dc8e728e700d357

## Title

Bootstrap verification tooling

## Goal

Diagnose and fix the missing local verification tooling that prevented previous backend checks from running. The goal is to make the Codex execution environment capable of running backend tests, or to prove exactly which parts require host/admin setup outside Codex control.

This task is infrastructure-only. Do not add product functionality.

## Facts

- Previous tasks repeatedly could not run full checks.
- `.ai/report.md` for `TASK-2026-06-21-03` says:
  - `pip` is missing.
  - `pytest` is missing.
  - `python3 -m pip --version` failed with `No module named pip`.
  - `python3 -m ensurepip --version` failed with `No module named ensurepip`.
  - `docker compose config` failed because `docker` is unavailable in the current WSL 2 distro.
- `python3 -m py_compile ...` did run successfully, so Python exists but lacks package tooling.
- `backend/pyproject.toml` defines runtime and dev dependencies.
- Docs say backend checks should run with:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

- Docker Compose validation should run from repository root with:

```bash
docker compose config
```

## Assumptions

- Python package tooling can likely be installed or bootstrapped without changing product code.
- Docker may require host-level installation or Docker Desktop/daemon access and may not be installable from inside Codex without admin privileges.
- If a tool cannot be installed, the exact command, error, and required external action must be documented.

## Unknowns

- Current OS/distribution and package manager availability.
- Whether `sudo` can be used without an interactive password.
- Whether `apt`, `python3-venv`, `python3-pip`, `pipx`, `uv`, or another safe Python installer is available.
- Whether network access is available for installing Python dependencies.
- Whether Docker CLI or Docker daemon can be installed/accessed from the current runtime.

## Scope

1. Diagnose the execution environment. Check and report:

```bash
pwd
uname -a
cat /etc/os-release || true
python3 --version
which python3 || true
which pip || true
python3 -m pip --version || true
python3 -m ensurepip --version || true
which pytest || true
which docker || true
docker --version || true
docker compose version || true
which apt || true
which sudo || true
```

2. Try to enable Python package tooling using safe, minimal steps appropriate to the environment.

Recommended order:

- If `python3 -m pip` works, use it.
- If `pip` is missing but `ensurepip` works, run `python3 -m ensurepip --upgrade`.
- If `ensurepip` is missing and `apt`/`sudo` can run non-interactively, install the minimal required packages such as `python3-pip` and, if needed, `python3-venv`.
- If neither is possible, look for an already available tool such as `uv` or `pipx`.
- Do not use unsafe shell download/install scripts unless there is no better option; if considering one, stop and document the tradeoff in `.ai/report.md` rather than silently doing it.

3. Once Python package tooling exists, install backend dev dependencies:

```bash
cd backend
python3 -m pip install -e ".[dev]"
```

If the environment requires `pip` instead of `python3 -m pip`, use the working equivalent and report it.

4. Run backend tests:

```bash
cd backend
pytest
```

or:

```bash
cd backend
python3 -m pytest
```

5. Diagnose Docker/Compose. If Docker is available, run:

```bash
docker compose config
```

If Docker is unavailable or the daemon is inaccessible, do not fake success. Document whether the missing part is:

- Docker CLI missing;
- Docker Compose plugin missing;
- Docker daemon inaccessible;
- permissions issue;
- host-level Docker/Desktop not installed or not connected to WSL.

6. Update `.ai/report.md` with:

- environment facts;
- installation steps attempted;
- exact commands that passed/failed;
- whether backend tests now pass;
- Docker/Compose status;
- any host/admin action still required.

7. If useful, update `docs/development.md` with a short troubleshooting section for missing `pip`/Docker, but keep it concise.

## Out Of Scope

- Product code changes.
- Backend domain, analytics, storage, or API changes.
- Frontend changes.
- Bitrix integration.
- CI/GitHub Actions setup.
- Installing or committing real secrets or data.
- Broad refactoring.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Keep repository changes minimal: likely only `.ai/report.md` and optionally `docs/development.md`.
- Do not change `.ai/task.md` during implementation.
- Do not use `git add .` unless explicitly allowed by the user.
- Do not commit generated dependency folders, virtual environments, caches, databases, Parquet files, CSV files, raw data, or secrets.
- Do not claim checks passed unless they actually passed.
- If host/admin privileges are required, document the exact requirement instead of working around it unsafely.

## Acceptance Criteria

- Environment diagnostics are captured in `.ai/report.md`.
- Python package tooling is installed or the exact blocker is documented.
- Backend dependencies are installed and `pytest` is run, or the exact blocker is documented.
- Docker Compose validation is run, or the exact Docker/host blocker is documented.
- No product functionality is added.
- No real secrets, raw Bitrix data, local databases, Parquet snapshots, CSV exports, dependency folders, or virtual environments are committed.
- The implementation commit uses the required prefix:

```text
codex: TASK-2026-06-21-04 Bootstrap verification tooling
```

## Checks

Primary desired checks:

```bash
cd backend
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

From repository root, if Docker is available:

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
