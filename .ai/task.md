# Task: TASK-2026-06-21-01

Status: planned
Created from commit: 57369822c9362bceba2f2ffaaa4ee8bf203a0ce8

## Title

Initialize project scaffold and documentation backbone

## Goal

Create the initial repository scaffold for the Bitrix sales analytics MVP and establish concise operational documentation that helps ChatGPT and Codex quickly understand the current project stage, architecture, commands, and next steps.

This task starts the technical track while the design system is prepared externally. Do not implement frontend screens in this task.

## Facts

- The repository currently contains `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- `SPEC.md` is confirmed as the current approved technical specification.
- The project is an internal sales analytics system based on Bitrix CRM data.
- Bitrix must be used only as a read-only data source.
- The main analytics entity is the contact.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
- All financial analytics must be normalized to USD.
- The MVP must not download or store phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted Bitrix fields.
- The design system will be prepared separately by the user in Claude Design.
- Frontend implementation must wait for the approved design system.
- Simple internal authentication will be implemented later using environment-based credentials/secrets, with no complex roles in MVP.
- `AGENTS.md` now requires documentation to be kept useful for both ChatGPT planning/acceptance and Codex implementation.

## Assumptions

- Use the target backend stack from `SPEC.md`: Python 3.12, FastAPI, Pydantic v2, Polars, DuckDB, Parquet, pytest.
- Use Docker Compose as the default local runtime entry point.
- Create only a minimal backend skeleton in this task: enough to verify project wiring, not business analytics yet.
- Create placeholder documentation for `frontend/` and `design-system/` without implementing UI or Storybook.
- Use placeholder environment values only; no real secrets or Bitrix webhook values.

## Unknowns

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual contact type values, priorities, and region mapping.
- Actual Bitrix pipelines, stages, and currencies found in real data.
- Final design tokens and frontend component decisions from Claude Design.
- Deployment host details, HTTPS setup, and backup destination.

## Scope

Create the initial project scaffold with a small, verifiable backend and documentation backbone.

Required repository structure:

```text
.ai/
  task.md
  report.md
backend/
  README.md
  Dockerfile
  pyproject.toml
  app/
    __init__.py
    main.py
    core/
      __init__.py
      config.py
  tests/
    test_health.py
docs/
  project-status.md
  architecture.md
  development.md
  data-model.md
  testing.md
design-system/
  README.md
frontend/
  README.md
README.md
.gitignore
.env.example
docker-compose.yml
```

Backend requirements:

- Implement a minimal FastAPI application.
- Add `GET /health` returning a simple status payload.
- Add a small settings/config module based on environment variables.
- Include only non-secret defaults and placeholders.
- Add pytest coverage for the health endpoint.
- Keep the backend skeleton ready for future Bitrix sync, data normalization, analytics, and report API modules, but do not implement those modules yet unless needed as empty packages for structure.

Documentation requirements:

- `README.md` must explain the project purpose, current stage, quick start, key commands, and documentation map.
- `docs/project-status.md` must state the current phase, what is done in this task, what is intentionally not done, known unknowns, and next likely steps.
- `docs/architecture.md` must describe the target layers from `SPEC.md`: Bitrix read-only extraction, raw local layer, normalization, analytics tables, backend API, web interface.
- `docs/development.md` must document local setup, Docker Compose usage, backend test command, environment file policy, and current limitations.
- `docs/data-model.md` must document the core MVP entities and safety rules at a high level: contacts, deals, deal-contact links, stages, currency rates, normalized contact type/region config, analytics outputs.
- `docs/testing.md` must document the current test command and the broader required test areas from `SPEC.md`.
- `backend/README.md` must describe backend structure and commands.
- `design-system/README.md` must state that the design system is prepared externally and blocks frontend screen implementation.
- `frontend/README.md` must state that frontend implementation is pending approved design system and should later follow `SPEC.md`.
- `.ai/report.md` must be updated with the implementation result using the format from `WORKFLOW.md`.

Repository hygiene requirements:

- Add `.gitignore` entries for Python caches, virtual environments, env files, local databases, raw data, Parquet snapshots, CSV exports, logs, Node dependencies, build outputs, and OS/editor noise.
- Add `.env.example` with placeholder values only.
- Do not add real credentials, real Bitrix data, raw exports, local databases, Parquet snapshots, or CSV exports.

## Out Of Scope

- Real Bitrix integration.
- NBRB currency integration.
- DuckDB schema implementation.
- Parquet snapshot writing.
- Contact normalization logic.
- ABC/RFM/reactivation/deal-cycle/concentration analytics.
- Report API endpoints beyond `GET /health`.
- Frontend app implementation.
- Design tokens, UI components, Storybook, or screen layouts.
- Authentication implementation.
- CI configuration.
- Production deployment, HTTPS, and backup setup.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Keep changes focused on the initial scaffold and documentation backbone.
- Do not invent Bitrix field codes, real contact types, real regions, real stages, or real currencies.
- Do not hardcode future contact type priorities or region rules.
- Do not implement frontend screens before design-system approval.
- Use placeholders for secrets and real external values.
- Keep documentation concise and operational.
- If a dependency or command choice is made, document it.

## Acceptance Criteria

- The required repository structure exists.
- `GET /health` exists and has a passing pytest test.
- The project can be run locally through Docker Compose, or any limitation is clearly documented in `.ai/report.md` and `docs/development.md`.
- `README.md` and all required docs files exist and match the current project state.
- Documentation clearly separates facts, assumptions, unknowns, and future work where relevant.
- `design-system/README.md` and `frontend/README.md` clearly state that frontend implementation is blocked until the design system is approved.
- `.gitignore` protects secrets, raw Bitrix data, local databases, Parquet snapshots, CSV exports, logs, dependencies, and build outputs.
- `.env.example` contains placeholders only.
- `.ai/report.md` is updated with changed files, checks, acceptance criteria status, known unknowns, and next step.
- The implementation commit uses the required prefix:

```text
codex: TASK-2026-06-21-01 Initialize project scaffold and documentation backbone
```

## Checks

Run the smallest relevant checks for this scaffold:

```bash
cd backend
pytest
```

Also run repository status/diff checks before committing:

```bash
git status --short
git diff --stat HEAD
```

If Docker Compose is implemented, also verify at least configuration validity when feasible:

```bash
docker compose config
```

If any check cannot be run, explain the exact reason in `.ai/report.md`.

## Notes

Before starting implementation, Codex must:

```bash
git log --oneline -5
git status --short
```

Codex must stop if the latest relevant commit is not a planner commit for this task.

After implementation, Codex must stage only files related to this task and `.ai/report.md`; do not use `git add .` unless explicitly allowed by the user.
