# AGENTS.md

Coding agent guidelines for this repository.

For collaboration protocol, task planning, Codex handoff, reports, review, and acceptance flow, see `WORKFLOW.md`. This file defines coding behavior, repository orientation rules, and project-specific safety constraints.

## Project Context

This project is an internal sales analytics system based on Bitrix CRM data.

Core MVP facts:

- Bitrix is a read-only data source.
- All filtering, normalization, calculations, and reports run locally.
- The main analytics entity is the contact.
- Companies, leads, product lines, activities, calls, emails, comments, phone numbers, email addresses, postal addresses, messengers, files, requisites, and arbitrary non-allowlisted Bitrix fields are out of MVP scope.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
- All financial analytics are normalized to USD.
- A deal must be counted only once in contact analytics.
- Contact types, priorities, and regions must be configuration/data, not scattered business constants.
- Docker Compose starts services only. It must not automatically call Bitrix or refresh local data without explicit user action.
- Local databases and generated data are intentionally not committed.

## Sources Of Truth

Before any non-trivial work, read the relevant sources in this order:

1. The latest user instruction.
2. Current repository files on GitHub.
3. `.ai/task.md` for the current task, when present.
4. `.ai/report.md` for the previous implementation report, when present.
5. `WORKFLOW.md` for collaboration and task protocol.
6. `SPEC.md` for product and technical requirements.
7. Project documentation under `docs/`.
8. Git history and diffs, when available.

Memory and guesses are not facts. If something is not verified from repository files, task files, documentation, tests, or explicit user instructions, mark it as unknown.

## Current Project Orientation

The current project includes:

- FastAPI backend under `backend/`.
- DuckDB local storage under runtime `data/`.
- React/Vite/TypeScript frontend under `frontend/`.
- Design-system source under `ui-kits/`.
- First frontend screen: Contacts.
- Manual UI-triggered local data refresh through `POST /api/local/refresh-data`.

The Contacts screen uses USD analytics metrics from `/api/reports/contacts/analytics`, not original-currency totals as primary financial metrics.

## Documentation Discipline

Documentation is part of the product infrastructure.

When creating or changing architecture, data models, commands, environment variables, testing approach, Docker behavior, frontend behavior, operator flow, or project workflow, update the relevant documentation in the same task.

Documentation must help both:

- ChatGPT quickly understand current project stage and make planning/review decisions;
- Codex quickly orient inside the repository and implement the next task without rediscovering basic context.

Keep documentation concise, current, and operational. Do not document secrets, raw Bitrix data, local databases, Parquet snapshots, CSV exports, personal contact fields, or webhook values.

Key docs:

- `WORKFLOW.md` — collaboration and task protocol.
- `SPEC.md` — product and technical requirements.
- `docs/project-status.md` — current stage and next likely steps.
- `docs/development.md` — setup, Docker, frontend/backend commands, operator flow.
- `docs/data-model.md` — core entities, storage, and safety rules.
- `frontend/README.md` — frontend status and commands.
- `backend/README.md`, when present — backend structure and commands.

## Core Principles

### Think First

Before changing code:

- understand the actual goal;
- inspect relevant files;
- identify facts, assumptions, and unknowns;
- avoid guessing.

If the requirement is unclear or product-impacting, stop and ask.

### Keep It Simple

Prefer the simplest solution that satisfies the requirement.

Do not over-engineer, introduce abstractions without need, generalize for hypothetical future cases, or create frameworks around small changes.

### Make Surgical Changes

Change only what is necessary.

Do not refactor unrelated code, rename unrelated symbols, reformat unrelated files, move code without need, or change public behavior outside the task.

### Preserve Existing Style

Follow current project style. Before adding new patterns, look for existing conventions in naming, file organization, error handling, and tests.

### Work Backwards From Acceptance

Every change must have a clear success condition.

Before finishing, verify:

- requested behavior is implemented;
- unrelated behavior is preserved;
- relevant checks were run;
- operator flow was checked when relevant;
- docs reflect the new state;
- remaining risks are documented.

If checks cannot be run, explain why in `.ai/report.md`.

## Task Size And Scope

Tasks should usually be large enough to close one meaningful, testable milestone:

- backend/data readiness;
- one frontend screen;
- one report;
- one operator flow;
- one infrastructure capability;
- one documentation/workflow update.

Do not split work into micro-tasks unless a real product, data, security, or architectural decision requires user review between steps.

Do not add adjacent improvements, extra screens, or unrelated refactors without explicit user request.

## Backend Rules

- Keep Bitrix access read-only.
- Use allowlisted Bitrix methods only.
- Do not add CRM write methods.
- Do not expose webhook URLs, tokens, secrets, local paths, raw rows, row samples, or forbidden personal fields.
- Keep business mappings and priorities in configuration/data, not scattered logic.
- Preserve transaction safety around raw load, normalization, rates, and activation.
- If a task changes analytics, check the metric semantics, not only code execution.

Forbidden Bitrix write patterns include:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

## Frontend Rules

- Use `ui-kits/` as the design-system source.
- Do not invent an unrelated visual style.
- Keep screens focused and operational.
- Show clear loading, error, empty, and success states.
- For long operations, show explicit progress text and disable duplicate actions.
- Do not display forbidden personal fields.
- Do not show misleading metrics. If a value is original currency, label it as such. USD metrics must come from USD analytics fields.
- For frontend tasks, verify the browser-facing/operator flow where practical, not only `npm run build`.

## Operator Flow Rules

If a task affects local startup, Docker, frontend, or user-visible behavior, check the real flow when possible:

```bash
docker compose config
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
docker compose down -v
```

For data-preparation flows, Docker must start services only. Bitrix refresh must require explicit user action, such as clicking `Обновить из Bitrix`.

If Docker, network, or live access is unavailable, document the exact limitation in `.ai/report.md`.

## Tests And Verification

Use the smallest relevant verification set for the task.

When changing backend behavior, run backend tests. If system Python lacks pytest, use the existing project/dev environment and document the exact command.

When changing frontend behavior, run:

```bash
cd frontend
npm run build
```

When changing Docker/runtime behavior, run Compose checks if Docker is available.

Do not claim something is tested unless it was actually tested.

## Git Discipline

Before changing files:

```bash
git log --oneline -5
git status --short
```

Do not overwrite unknown local changes.

Do not use:

```bash
git add .
```

unless explicitly allowed.

Stage only files related to the current task and `.ai/report.md`.

When committing under the repository workflow, use commit prefixes defined in `WORKFLOW.md`:

```text
planner: TASK-... <task>
codex: TASK-... <task>
```

`accept:` commits are not used by default. Acceptance is recorded in chat unless the user explicitly asks for acceptance commits.

## Security And Data Safety

Never commit or expose:

- Bitrix webhook URLs or tokens;
- credentials;
- `.env` files with real values;
- raw Bitrix exports;
- local DuckDB databases;
- Parquet snapshots with real data;
- CSV exports with real data;
- logs containing secrets or raw private data;
- personal contact fields outside the approved allowlist;
- `node_modules`, frontend build output, or caches.

Environment examples must use placeholders only.

API responses, UI messages, logs, reports, and documentation must not reveal secrets, webhook values, raw private data, local absolute paths, or generated file contents.

Time must be stored in UTC. Display timezone defaults to `Europe/Minsk` unless project requirements explicitly change.

## What Not To Do

Do not:

- add unrelated cleanup;
- modernize code without request;
- introduce new dependencies without need;
- change formatting globally;
- rewrite working code for style reasons;
- expand scope;
- hide uncertainty;
- claim verification that was not performed;
- add frontend screens beyond the task;
- add analytics explicitly out of MVP scope;
- automatically refresh Bitrix data on Docker startup.

## Default Task Behavior

When working on a task:

1. Read `.ai/task.md`.
2. Read relevant documentation and code.
3. Check git status and recent commits.
4. Identify facts, assumptions, and unknowns.
5. Make the smallest correct change for the requested milestone.
6. Update documentation if project behavior changed.
7. Run relevant automated and operator-flow checks.
8. Update `.ai/report.md` with changes, checks, facts, unknowns, and risks.
9. Stage only task files and `.ai/report.md`.
10. Commit with the required `codex:` message.

Bias toward correctness and clarity over speed for non-trivial work.
