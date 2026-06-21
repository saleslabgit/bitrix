# AGENTS.md

Coding agent guidelines for this repository.

These rules describe how to write and change code in this project. For collaboration protocol with the user, task planning, Codex handoff, reports, and acceptance flow, see `WORKFLOW.md`.

The workflow is a separate process document. This file defines coding behavior and repository orientation rules.

---

# Project Context

This project is an internal sales analytics system based on Bitrix CRM data.

Core MVP facts:

- Bitrix is a read-only data source.
- All filtering, normalization, calculations, and reports run locally.
- The main analytics entity is the contact.
- Companies, leads, product lines, activities, calls, emails, comments, phone numbers, email addresses, postal addresses, messengers, files, and arbitrary non-allowlisted Bitrix fields are out of MVP scope.
- Revenue is calculated only from won deals.
- Estimated profit is always `revenue_usd * 0.50`.
- All financial analytics are normalized to USD.
- A deal must be counted only once in contact analytics.
- Contact types, priorities, and regions must be configuration/data, not hardcoded business constants.

---

# Sources Of Truth

Before any non-trivial work, read the relevant sources in this order:

1. The latest user instruction.
2. Current repository files on GitHub.
3. `.ai/task.md` for the current task, when present.
4. `.ai/report.md` for the previous implementation report, when present.
5. `WORKFLOW.md` for collaboration and task protocol.
6. `SPEC.md` for product and technical requirements.
7. Project documentation under `docs/`, once created.
8. Git history and diffs, when available.

Memory and guesses are not facts. If something is not verified from repository files, task files, documentation, tests, or explicit user instructions, mark it as unknown.

---

# Documentation Discipline

Documentation is part of the product infrastructure, not an afterthought.

When creating or changing architecture, data models, commands, environment variables, testing approach, deployment behavior, or project workflow, update the relevant documentation in the same task.

The documentation must help both:

- ChatGPT quickly understand the current project stage and make planning or acceptance decisions;
- Codex quickly orient inside the repository and implement the next task without rediscovering basic context.

The documentation should stay concise, current, and operational. Prefer short files with clear responsibility over long narrative documents.

Expected documentation backbone after project scaffold:

- `README.md` — project overview, local start, main commands, and documentation map.
- `docs/project-status.md` — current stage, completed work, active task, known blockers, next likely steps.
- `docs/architecture.md` — high-level architecture, module boundaries, data layers, and important constraints.
- `docs/development.md` — setup, commands, environment variables, Docker, and local workflow.
- `docs/data-model.md` — core entities, fields, storage layers, and data safety rules.
- `docs/testing.md` — test strategy, required checks, fixtures, and commands.
- `design-system/README.md` — status and integration notes for the externally prepared design system.
- `frontend/README.md` — frontend status; frontend implementation must wait for the approved design system.
- `backend/README.md` — backend structure, commands, and module map.

When a documentation file is intentionally incomplete, state what is unknown and what future task should fill it.

Do not document secrets, raw Bitrix data, local databases, Parquet snapshots, CSV exports, personal contact fields, or webhook values.

---

# Core Principles

## 1. Think First

Before changing code:

- understand the actual goal;
- inspect the relevant files;
- identify assumptions;
- identify unknowns;
- avoid guessing.

If the requirement is unclear, stop and ask.

Do not write code before understanding the problem.

---

## 2. Keep It Simple

Prefer the simplest solution that satisfies the requirement.

Do not:

- over-engineer;
- introduce abstractions without need;
- add configuration without need;
- generalize for hypothetical future cases;
- create frameworks around small changes.

Simple code is preferred over clever code.

---

## 3. Make Surgical Changes

Change only what is necessary.

Do not:

- refactor unrelated code;
- rename unrelated symbols;
- reformat unrelated files;
- move code without need;
- change public behavior outside the task;
- add features not requested.

Minimize the diff.

---

## 4. Preserve Existing Style

Follow the current project style.

Before adding new patterns:

- look for existing conventions;
- match naming style;
- match file organization;
- match error handling style;
- match testing style.

Prefer consistency over personal preference.

---

## 5. Do Not Invent Facts

Do not assume APIs, schemas, environment variables, commands, or project structure.

Verify from:

- repository files;
- tests;
- documentation;
- existing code;
- task instructions.

If something is not verified, state it as unknown.

---

## 6. Work Backwards From Acceptance

Every change should have a clear success condition.

Before finishing, verify:

- the requested behavior is implemented;
- unrelated behavior is preserved;
- relevant checks were run;
- documentation reflects the new state;
- remaining risks are documented.

If checks cannot be run, explain why.

---

# Code Quality Rules

## Prefer Explicit Code

Use clear, direct code.

Avoid:

- clever one-liners;
- hidden side effects;
- unnecessary indirection;
- magic behavior;
- premature optimization.

Readable code is better than compact code.

---

## Preserve Boundaries

Respect existing architecture.

Do not cross module boundaries casually.

Do not move responsibilities between layers unless the task requires it.

If the correct fix appears to require architectural change, stop and explain the tradeoff.

---

## Handle Errors Deliberately

Do not swallow errors silently.

Follow existing project conventions for:

- validation;
- exceptions;
- logging;
- user-facing errors;
- retries;
- fallback behavior.

Do not add noisy logging unless needed.

---

## Tests and Verification

Use the smallest relevant verification set.

Prefer existing test commands and project scripts.

When changing behavior:

- add or update tests when appropriate;
- run relevant tests;
- report what was run;
- report what was not run.

Do not claim something is tested unless it was actually tested.

---

# Git Discipline

Before changing files:

```bash
git status --short
```

Do not overwrite unknown local changes.

Do not use:

```bash
git add .
```

unless explicitly allowed.

Stage only files related to the current task.

When committing under the repository workflow, use the commit prefixes defined in `WORKFLOW.md`:

```text
planner: TASK-... <task>
codex: TASK-... <task>
accept: TASK-... <task>
```

---

# Security And Data Safety

Never commit or expose:

- Bitrix webhook URLs or tokens;
- credentials;
- `.env` files with real values;
- raw Bitrix exports;
- local DuckDB databases;
- Parquet snapshots with real data;
- CSV exports with real data;
- personal contact fields that are outside the approved allowlist.

Environment examples must use placeholders only.

API responses, UI messages, logs, reports, and documentation must not reveal secrets or raw private data.

Time must be stored in UTC. Display timezone defaults to `Europe/Minsk` unless explicitly changed by the project requirements.

---

# What Not To Do

Do not:

- add unrelated cleanup;
- modernize code without request;
- introduce new dependencies without need;
- change formatting globally;
- rewrite working code for style reasons;
- expand scope;
- hide uncertainty;
- claim verification that was not performed;
- implement frontend screens before the design system is approved;
- add analytics that are explicitly out of MVP scope.

---

# Default Behavior

When working on a task:

1. Read the task.
2. Inspect relevant files.
3. Read the relevant documentation.
4. Identify facts, assumptions, and unknowns.
5. Make the smallest correct change.
6. Update documentation when the project state changes.
7. Run relevant checks.
8. Report changes and verification in `.ai/report.md`.

Bias toward caution over speed for non-trivial work.

For trivial one-line fixes, use judgment and keep the process lightweight.
