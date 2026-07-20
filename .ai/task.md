# Task: TASK-2026-07-20-06

Status: planned
Created from: `91e536d6a7d229c2f623d62681d1e2062bc4c67f`

## Title

Recompute factual close history and full approved state during explicit reconciliation

## Goal

Complete the factual-close correction in explicit contact-deal reconciliation.

The normal manual refresh and most reconciliation behavior are already correct. Preserve the existing read-only stage-history client, resolver, storage migration, analytics, rollback behavior, and completed tests.

The remaining defect is that reconciliation currently decides whether to fetch history before it knows whether an existing closed deal has been reopened and closed again. A closed deal with a non-null but stale `actual_closed_at` can therefore keep an old close timestamp when its current category, stage, status, planned date, and KEV are unchanged.

Reconciliation must also compare and update the complete approved deal state, not only stage/status/date/KEV fields.

## Review Status

The following implementation commit was reviewed and rejected:

```text
91e536d6a7d229c2f623d62681d1e2062bc4c67f
```

Do not revert its valid work:

- factual-close resolution for new and missing-factual deals;
- batched `crm.stagehistory.list` use;
- transactional history/deal/link writes;
- rollback and active-dataset preservation;
- planned/factual close separation;
- KEV persistence;
- existing reconciliation tests and documentation.

## Verified Remaining Defects

### 1. Existing reclosed deals can keep a stale factual close

Current logic builds `closed_ids_to_resolve` only from `deal_ids_to_write`.

`deal_ids_to_write` is selected before stage history is fetched. `_deal_requires_reconciliation()` currently treats a local closed deal with non-null `actual_closed_at` as unchanged when these values remain equal:

- planned close;
- stage;
- category;
- status;
- KEV.

It does not know about a newer exact final-stage history record. Therefore this valid scenario is missed:

1. local `actual_closed_at` is in May;
2. the deal is reopened;
3. the deal is closed again in June into the same final stage;
4. current stage/category/status/planned date/KEV remain equal;
5. reconciliation skips history and leaves May instead of June.

### 2. Full approved remote state is not compared

The current reconciliation-state comparison omits at least:

- `deal_name`;
- `amount_original`;
- `currency_original`;
- `created_at`.

The upsert can write those fields, but it is never invoked when only those approved fields changed.

### 3. Existing reclose coverage is insufficient

The current reclose test covers a newly inserted deal with multiple history records. It does not cover an existing local deal whose factual close is already populated but stale.

## Facts

- Bitrix remains strictly read-only.
- `CLOSEDATE` / `closedTime` is planned information only.
- `actual_closed_at` is the factual timestamp used by close-dependent analytics.
- Open deals always have `actual_closed_at = NULL`.
- Won/lost deals resolve factual close from the latest exact current final-stage history record.
- Exact match includes deal ID, current category, current stage, `TYPE_ID = 3`, and semantic `S` for won or `F` for lost.
- `movedTime` is the only fallback when exact history is unavailable.
- `CLOSEDATE` is never a factual fallback.
- Explicit reconciliation is bounded to at most the existing approved number of operator-supplied deal IDs.
- The previous active dataset must remain unchanged after a handled failure.
- Docker startup must not call Bitrix or refresh data automatically.

## Required Implementation

### 1. Inspect the current repository

Read and follow:

- `AGENTS.md`;
- `WORKFLOW.md`;
- `SPEC.md`;
- `.ai/task.md`;
- `.ai/report.md`;
- `backend/README.md`;
- `frontend/README.md`;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/deployment.md`;
- `docs/project-status.md`.

Inspect at minimum:

- `reconcile_explicit_contact_deals()`;
- `_deal_requires_reconciliation()`;
- `_raw_deal_state()`;
- `_upsert_raw_deals()`;
- `_upsert_raw_stage_history()`;
- `BitrixClient.list_deal_stage_history()`;
- `transform_deals()`;
- `transform_deal_stage_history()`;
- `apply_actual_close_times()`;
- reconciliation endpoint behavior;
- reconciliation tests.

Before editing:

```bash
git log --oneline -8
git status --short
```

Do not overwrite unknown local changes.

### 2. Resolve all confirmed current closed deals before deciding writes

Do not use the pre-history local comparison to decide which current closed deals need factual resolution.

Required sequence:

1. Fetch and validate the bounded current Bitrix rows and contact relations using the existing explicit flow.
2. Transform all confirmed deal rows using the existing exact local stage/category directory.
3. Build the set of **all confirmed current won/lost deal IDs**, regardless of whether local `actual_closed_at` is null or non-null.
4. Call `client.list_deal_stage_history()` once for that bounded closed-deal set. Do not call it once per deal.
5. Transform the approved history rows.
6. Call `apply_actual_close_times()` for all confirmed transformed deals:
   - won/lost deals receive the latest exact current closure or `movedTime` fallback;
   - open deals receive `NULL` and must not reuse old final history.
7. Only after factual resolution, compare the resolved remote state with the local approved state.
8. Upsert only rows whose complete approved state differs or that are missing locally.
9. Store the fetched approved history transactionally for the bounded affected IDs.
10. Insert missing confirmed contact links, normalize, store status, and activate in the same transaction.

The history fetch must occur for an existing confirmed closed deal even when its local `actual_closed_at` is already non-null. This is required to detect a later reclose into the same stage.

### 3. Compare the complete approved deal state

The local-state loader and comparison must include all approved persisted deal fields:

- `deal_id`;
- `deal_name`;
- `amount_original`;
- `currency_original`;
- `created_at`;
- `planned_close_at`;
- `actual_closed_at` after factual resolution;
- `stage_id`;
- `category_id`;
- `status_group`;
- `kev_held`.

The deprecated physical `closed_at` column must remain `NULL` and must not participate as a source of truth.

Comparison requirements:

- normalize timestamps consistently to UTC before comparison;
- compare decimal amounts deterministically without float conversion;
- detect changes when only name, amount, currency, or creation time changed;
- detect a new factual close even when stage/category/status/planned date/KEV are unchanged;
- avoid a local upsert when the fully resolved remote state is truly identical;
- never copy legacy `closed_at` into `actual_closed_at`.

### 4. Preserve factual-close semantics

For every confirmed deal:

- current `open` -> `actual_closed_at = NULL`;
- current `won` -> latest exact `S` final transition;
- current `lost` -> latest exact `F` final transition;
- category and stage must match the current deal;
- latest `CREATED_TIME` wins; history ID remains the deterministic tie-breaker;
- exact history wins over `movedTime`;
- valid `movedTime` is the only fallback;
- missing both exact history and `movedTime` for a current closed deal is a handled safe failure;
- factual close before creation is invalid.

### 5. Preserve transactional safety

Remote facts and factual-close resolution should be completed before local writes where practical.

The following must succeed or fail together:

- raw deal upserts;
- raw approved history upserts;
- contact-link inserts;
- normalization;
- reconciliation run status and activation.

On handled failure:

- no partial deal/history/link change remains;
- normalized rows remain unchanged;
- previous active dataset remains active;
- error text remains safe and does not expose webhook URL, token, or private payloads.

Do not delete unrelated history rows. Repeated reconciliation must remain idempotent.

## Required Tests

Add or update focused tests proving all of the following.

### Existing stale reclose: mandatory regression

Prepare an existing local won deal with:

- created date in January;
- planned close in February;
- local `actual_closed_at` in May;
- current Bitrix stage/category/status/planned date/KEV unchanged;
- exact final-stage history containing a later matching closure in June.

After reconciliation:

- history was fetched despite the non-null local factual date;
- `actual_closed_at` is June;
- Deals API `closed_date` is June;
- cycle is calculated through June;
- May is not retained.

This test must be for an existing local row, not a newly inserted deal.

### Full approved state comparison

Use an existing confirmed deal where only approved non-status fields change. Verify the local raw and normalized state is updated when one or more of these differ:

- deal name;
- amount;
- currency;
- creation time.

A single focused scenario may change all four, but assertions must prove each persisted value changed.

### Truly unchanged closed deal

For an existing closed deal whose resolved remote state and latest exact factual close equal the local state:

- history is still fetched to detect reclose;
- no destructive or unnecessary deal rewrite occurs;
- reconciliation remains successful and idempotent.

### Existing missing factual close

Keep the existing test that repairs a closed local deal with `actual_closed_at = NULL`.

### Open deal

Current open deal clears or preserves `actual_closed_at = NULL`, even when old final history exists.

### Batching

Multiple confirmed closed deals use one bounded stage-history client call for the set, not one call per deal.

### Fallback and safe failure

- exact history missing plus valid `movedTime` succeeds;
- history and `movedTime` both missing fails safely;
- previous active dataset and raw/normalized state remain unchanged.

### Transaction rollback

Forced storage or normalization failure rolls back deal, history, link, normalized, and activation changes.

### Existing regression suite

Preserve and run tests for:

- new January/February/June deal;
- multiple exact history records;
- KEV persistence;
- approved seven-column history;
- idempotency;
- normal manual refresh;
- Contacts/Deals/ABC/KEV/RFM/cycle/revenue-series factual-date behavior;
- contact `661` assignment;
- funnel semantics;
- read-only allowlist and no wildcard selects;
- auth and frontend compatibility.

Do not weaken or remove tests to make the suite pass.

## Documentation And Report

Update only the documentation needed for the corrected reconciliation semantics:

- `backend/README.md`;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/project-status.md`;
- `.ai/report.md`.

Document explicitly that explicit reconciliation:

- fetches current final-stage history for every confirmed current closed deal, even when a local factual date already exists;
- detects reopen/reclose into the same stage;
- compares the complete approved remote deal state after factual resolution;
- uses one bounded history request flow and remains read-only;
- preserves the previous active dataset on failure.

Replace `.ai/report.md` with an accurate report for this correction only. Do not keep `Status: done` unless every acceptance criterion and check passes.

## Out Of Scope

- Changing the factual-close business rule.
- Displaying planned close date in the frontend.
- New UI screens or history timelines.
- Time-in-stage analytics.
- Historical as-of reporting.
- Automatic or scheduled refresh.
- Broad reconciliation redesign unrelated to these defects.
- Bitrix write methods.
- Live Bitrix inspection during implementation.
- Production deployment.

## Constraints

- Keep Bitrix strictly read-only.
- Reuse the existing approved `crm.stagehistory.list` client.
- Never add or call:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Never use wildcard selects.
- Do not make live Bitrix calls.
- Do not modify `.ai/task.md` during implementation.
- Do not use `git add .`.
- Do not expose or commit secrets, real `.env`, databases, real snapshots, CSV, raw private rows, logs, caches, `node_modules`, `frontend/dist`, browser artifacts, or temporary tooling.
- Preserve normal manual refresh and all completed TASK-06 behavior.
- Docker startup must continue to start services only.

## Acceptance Criteria

1. Every confirmed current won/lost deal participates in one bounded stage-history loading flow, including deals with an existing non-null factual date.
2. No per-deal history N+1 pattern is introduced.
3. An existing deal reclosed into the same final stage updates from the old factual date to the latest exact closure.
4. Open deals always have `actual_closed_at = NULL`.
5. Exact current category/stage/semantic history wins; `movedTime` is the only fallback.
6. `CLOSEDATE` remains planned-only.
7. Full approved deal state is compared after factual resolution.
8. Changes to name, amount, currency, or creation time trigger the correct upsert.
9. Truly unchanged resolved rows are not rewritten unnecessarily.
10. Deprecated physical `closed_at` remains `NULL` and unused as factual data.
11. Approved history remains bounded, seven-column, transactional, and idempotent.
12. Failed history/resolution/storage/normalization preserves raw, normalized, and previous active state.
13. Deals API close date and cycle use the newly resolved latest closure.
14. Existing normal refresh and all close-dependent analytics remain correct.
15. Full backend suite passes.
16. Python compilation passes.
17. Frontend build passes.
18. Local and production Compose configurations pass.
19. Documentation and `.ai/report.md` are accurate.
20. No live Bitrix calls, writes, wildcard selects, secrets, databases, or generated private data are committed.
21. Docker startup remains unchanged.

## Checks

Before implementation:

```bash
git log --oneline -8
git status --short
```

Focused tests:

```bash
cd backend
python -m pytest tests/test_contact_deal_diagnostics.py tests/test_bitrix_client.py tests/test_bitrix_ingestion.py tests/test_analytics.py tests/test_api_bitrix.py tests/test_api_local.py
```

Use the actual existing filenames and record the exact command.

Complete backend suite:

```bash
cd backend
python -m pytest
```

Python compilation:

```bash
python -m compileall backend/app backend/tests
```

Frontend compatibility:

```bash
cd frontend
npm run build
```

Compose validation:

```bash
docker compose config
docker compose -f docker-compose.prod.yml config
```

Local operator flow must use synthetic or fully mocked data with live Bitrix disabled:

```bash
BITRIX_WEBHOOK_URL="" docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
```

Do not invoke live refresh or reconciliation with real credentials.

After verification:

```bash
docker compose down -v
```

Safety and diff review:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src docs
rg 'select[^\n]*\*' backend/app backend/tests
git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'
git status --short --branch
git diff --name-only --cached
```

## Hard Workflow Gate

Before commit:

- existing-local May-to-June reclose regression passes;
- every current closed confirmed deal is included in bounded history resolution;
- complete approved state comparison tests pass;
- unchanged resolved row behavior is verified;
- open, missing-factual, fallback, safe-failure, batching, idempotency, and rollback tests pass;
- complete backend suite passes;
- Python compileall passes;
- frontend build passes;
- both Compose configurations pass;
- synthetic/mocked operator flow passes without live Bitrix access;
- `.ai/report.md` contains exact current correction results only;
- only task-related files and `.ai/report.md` are staged;
- no secrets, databases, private/generated data, caches, build output, browser artifacts, or temporary tooling are staged;
- no Bitrix write method or wildcard select is added;
- Docker startup behavior remains unchanged.

Set `.ai/report.md` status to `done` only after every acceptance criterion and hard gate passes.

Commit message:

```text
codex: TASK-2026-07-20-06 Fix reclose and full-state reconciliation
```
