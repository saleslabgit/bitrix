# Task: TASK-2026-06-21-03

Status: planned
Created from commit: 7bf4e79b9b0c8c847ff37abad4be1b4aa9a7528c

## Title

Add backend domain model scaffold and fixture plan

## Goal

Create the first backend domain layer scaffold for the MVP data entities and add a documented fixture strategy for future analytics tests.

This task should prepare the project for Bitrix extraction, normalization, and analytics work without implementing real Bitrix integration or report calculations yet.

## Facts

- `SPEC.md` is the approved product and technical specification.
- The main analytics entity is the contact.
- Bitrix is read-only.
- MVP data entities include contacts, deals, deal-contact links, stages, currency rates, contact type/region config, and analytics outputs.
- Phones, emails, addresses, messengers, requisites, comments, files, activity fields, and arbitrary non-allowlisted Bitrix fields are forbidden.
- A deal must be counted only once in contact analytics.
- The analytical contact for a deal is selected by contact type priority, then Bitrix primary flag, then minimum contact ID.
- Contact type priorities and region mapping must be configurable/data-driven, not hardcoded business constants.
- Frontend implementation remains blocked until the design system is approved.
- The current scaffold has minimal FastAPI `/health` only.
- `TASK-2026-06-21-02` documented the dev dependency installation command, but pytest and Docker checks could not run in the Codex runtime because `pip`, `pytest`, and Docker were unavailable.

## Assumptions

- Use Pydantic v2 for domain/data transfer models.
- Keep pure domain logic independent from FastAPI routes and external APIs.
- Use pytest unit tests for domain behavior.
- It is acceptable to add small Python modules under `backend/app/domain/` and tests under `backend/tests/`.
- The integration fixture can be represented as static JSON test data for now, because real Bitrix access and schemas are not known yet.

## Unknowns

- Actual Bitrix field code for contact type.
- Actual contact type values, priorities, and region mapping.
- Actual Bitrix pipelines, stages, and currencies.
- Whether the current runtime can install dependencies and run pytest.
- Whether Docker is available in the current runtime.

## Scope

Create a minimal but useful backend domain model scaffold and fixture documentation.

Required work:

1. Add a backend domain package, for example:

```text
backend/app/domain/
  __init__.py
  models.py
  contact_selection.py
```

2. Define Pydantic models for allowed MVP data shapes only. Include at minimum:

- `ContactSnapshot`
- `DealSnapshot`
- `DealContactLink`
- `StageSnapshot`
- `ContactTypeRule`
- `CurrencyRateSnapshot`

3. Models must use explicit fields from `SPEC.md` and must not include forbidden personal/contact fields.

4. Add a small pure function for analytical contact selection from deal-contact candidates and contact type rules.

Expected selection order:

1. Contact with the best configured type priority.
2. If priority ties, contact with `is_primary = true`.
3. If still tied, minimum `contact_id`.
4. If a deal has no contacts, return `None` rather than creating a fake contact.

5. Add focused unit tests for analytical contact selection:

- best type priority wins;
- primary flag breaks equal priority ties;
- minimum contact ID breaks remaining ties;
- deal without contacts returns `None`;
- unknown/missing contact type uses a neutral fallback that does not hardcode business-specific type values.

6. Add an integration fixture plan document, for example:

```text
docs/fixtures.md
```

It must describe the future minimum fixture required by `SPEC.md`:

- at least 10 contacts;
- at least 30 deals;
- won, open, and lost deals;
- several currencies;
- a deal with multiple contacts;
- equal contact type priorities;
- a deal without contact;
- A contact without sales in the last 12 months;
- a one-deal contact;
- a long-open deal.

7. Optionally add a small placeholder test fixture file under `backend/tests/fixtures/` only if it is useful for the new tests. Keep it synthetic and free of real Bitrix data.

8. Update relevant documentation:

- `docs/data-model.md` with the new domain model scaffold.
- `docs/testing.md` with the new domain tests and fixture plan.
- `backend/README.md` with the new domain package map.
- `docs/project-status.md` with current progress and next likely steps.

9. Update `.ai/report.md` for this task using the format from `WORKFLOW.md`.

## Out Of Scope

- Real Bitrix API calls.
- Real Bitrix field code mapping.
- Real contact type/region configuration values.
- DuckDB schema creation.
- Parquet snapshot writing.
- Currency conversion implementation.
- ABC, RFM, reactivation, deal-cycle, stale-deal, or concentration calculations.
- Report API endpoints.
- Authentication.
- Frontend implementation.
- Design-system implementation.
- CI setup.
- Production deployment.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Keep the diff focused on backend domain models, analytical contact selection, tests, and documentation.
- Do not add forbidden Bitrix fields to models, fixtures, docs examples, logs, or reports.
- Do not hardcode business-specific contact type names, priorities, or region rules.
- Do not implement real external API clients.
- Do not change `.ai/task.md` during implementation.
- Do not use `git add .` unless explicitly allowed by the user.
- If tests cannot be run because tooling is unavailable, document the exact blocker in `.ai/report.md`.

## Acceptance Criteria

- Domain model package exists and is importable.
- Pydantic models cover the allowed MVP entity shapes listed in scope.
- Forbidden personal/contact fields are not introduced.
- Analytical contact selection is implemented as pure backend domain logic.
- Unit tests cover the required contact selection cases.
- `docs/fixtures.md` documents the future integration fixture strategy from `SPEC.md`.
- Relevant docs are updated and remain concise.
- No real secrets, real Bitrix data, local databases, Parquet snapshots, or CSV exports are added.
- `.ai/report.md` lists changed files, checks run, acceptance status, remaining unknowns, and next step.
- The implementation commit uses the required prefix:

```text
codex: TASK-2026-06-21-03 Add backend domain model scaffold and fixture plan
```

## Checks

Run if tooling is available:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

At minimum, if pytest cannot run because tooling is unavailable, run Python syntax checks if possible:

```bash
python3 -m py_compile backend/app/domain/*.py backend/tests/test_*.py
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
