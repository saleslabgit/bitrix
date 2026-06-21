
Coding agent guidelines for this repository.

These rules describe how to write and change code in this project.

For collaboration protocol with the user, task planning, Codex handoff, reports, and acceptance flow, see: WORKFLOW.md

The workflow is a separate process document. This file defines coding behavior.

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
    
- claim verification that was not performed.
    

---

# Default Behavior

When working on a task:

1. Read the task.
    
2. Inspect relevant files.
    
3. Identify facts, assumptions, and unknowns.
    
4. Make the smallest correct change.
    
5. Run relevant checks.
    
6. Report changes and verification.
    

Bias toward caution over speed for non-trivial work.

For trivial one-line fixes, use judgment and keep the process lightweight.