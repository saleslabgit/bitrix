# Task: TASK-2026-06-21-10

Status: planned
Created from commit: 00399db9363fce1aef3d0c534b394266b5ff7367

## Title

Correct TASK-09 workflow report gate

## Goal

Fix the TASK-09 process gap found during review: the implementation report did not document all required hard-gate checks from TASK-09, especially `docker compose config` and the final pre-commit checks.

This is a corrective workflow/documentation task only. Do not change backend code, tests, docs, `AGENTS.md`, or `ui-kits/` unless a required check reveals a concrete defect that cannot be represented honestly in `.ai/report.md`.

## Review Finding To Fix

TASK-09 implementation is functionally acceptable, but `.ai/report.md` is incomplete against the TASK-09 hard gate:

- `docker compose config` was required but is not reported;
- `git diff --stat HEAD` was required but is not reported;
- `git diff --name-only --cached` was required but is not reported;
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` was required but is not reported;
- if any of these checks cannot run, the exact reason must be documented in `.ai/report.md`.

## Scope

1. Read the current repo state and the TASK-09 report.
2. Run the missing required checks where possible.
3. Update `.ai/report.md` so it accurately records:
   - the TASK-09 checks that were already reported;
   - the newly run missing checks and their results;
   - any check that could not be run, with a specific reason;
   - that no code/source/docs changes were made for this corrective task.
4. Commit only `.ai/report.md` for the corrective implementation.

## Out Of Scope

- Backend feature changes.
- Test changes.
- Documentation changes outside `.ai/report.md`.
- Editing `.ai/task.md` during implementation.
- Editing `AGENTS.md`.
- Editing `ui-kits/`.
- Reworking TASK-09 implementation.
- Running live Bitrix calls.
- Adding or changing dependencies.

## Constraints

- Follow `AGENTS.md`, `docs/workflow.md`, and current `.ai/task.md`.
- Do not hide failed checks. If a required check fails, record the exact command and result in `.ai/report.md`.
- If `docker compose config` cannot run because Docker/Compose is unavailable in the environment, document that exact environment limitation.
- Do not use `git add .`.
- Stage only `.ai/report.md`.
- If any file other than `.ai/report.md` changes, stop and report instead of committing, unless it is an unavoidable generated artifact that you remove before commit.

## Acceptance Criteria

- `.ai/report.md` contains the missing TASK-09 hard-gate check results or explicit not-run reasons.
- `.ai/report.md` clearly states that TASK-10 made no code changes.
- `docker compose config` is run and reported, or its exact not-run reason is reported.
- Final git checks are run and reported.
- No backend code, tests, product docs, `AGENTS.md`, `.ai/task.md`, or `ui-kits/` are changed by the implementation.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-21-10 Correct TASK-09 workflow report gate
```

## Checks

Run before edits:

```bash
git log --oneline -5
git status --short
```

Run from repository root:

```bash
docker compose config
git status --short --branch
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

Before committing, verify staged scope exactly:

```bash
git diff --name-only --cached
```

Expected staged file:

```text
.ai/report.md
```

If any required check cannot be run, document the exact reason in `.ai/report.md` before committing.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- the latest relevant commit is this planner commit;
- `.ai/report.md` is updated with the missing TASK-09 checks;
- every required check is either run and reported, or explicitly documented as not run with reason;
- staged files contain only `.ai/report.md`;
- `AGENTS.md`, `.ai/task.md`, backend source, tests, docs, and `ui-kits/` are not staged;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
