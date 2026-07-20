# Task: TASK-2026-07-20-06

Status: planned
Created from: `2a1a7494906d72f64ea93fd599a3f8e41e188c8b`

## Title

Use actual final-stage transition timestamps for deal close analytics

## Goal

Correct the meaning of deal completion dates throughout the local dataset and analytics.

The current implementation maps Bitrix `CLOSEDATE` / `closedate` directly to local `closed_at`. In Bitrix this field is an editable planned/end date and can default to creation date plus seven days. It is not a reliable factual timestamp of closing the deal.

Use the actual transition time into the current final stage for closed deals. Preserve the Bitrix planned close date separately and ensure every close-dependent metric, filter, report, and displayed close date uses the factual timestamp.

This is a backend/data correctness task with compatible API behavior. It must remain strictly read-only and transaction-safe.

## Facts

- Official Bitrix documentation defines deal `CLOSEDATE` / `closedate` as the item end/completion date; imported items default it to creation date plus seven days. It is user-editable and is not an immutable factual close timestamp.
- Official Bitrix documentation defines `MOVED_TIME` / `movedTime` as the time the item was moved into its current stage.
- Official `crm.stagehistory.list` documentation states:
  - `entityTypeId = 2` means deal;
  - `TYPE_ID = 3` means transfer to a final stage;
  - `CREATED_TIME` is the time the item was transferred to that stage;
  - `STAGE_SEMANTIC_ID = S` means successful final stage;
  - `STAGE_SEMANTIC_ID = F` means failed final stage;
  - deal records include `OWNER_ID`, `CATEGORY_ID`, `STAGE_ID`, and `STAGE_SEMANTIC_ID`.
- The current project requests `CLOSEDATE` / `closedTime` and maps it directly to `DealSnapshot.closed_at`.
- Current close-dependent analytics include deal cycles, close-date filters, Contacts last-won dates and average cycles, ABC periods, KEV periods, won-revenue series, RFM/recency, deal-cycle reports, and historical currency-rate selection for closed deals.
- Funnel and stage resolution is exact on `(stage_id, category_id)` and must remain exact.
- Revenue remains won-only.
- Estimated profit remains `revenue_usd * 0.50`.
- Bitrix is strictly read-only.
- Docker startup must never call Bitrix or refresh data automatically.
- A manual `Обновить из Bitrix` action is required after deployment to populate the new factual close timestamps.

## Assumptions

- For a deal whose current local status is `open`, the factual close timestamp is always `null`, even if the history contains an older final-stage transition from a previous close/reopen cycle.
- For a deal whose current local status is `won` or `lost`, the primary factual close timestamp is the latest stage-history record that matches all of:
  - the deal ID;
  - `TYPE_ID = 3`;
  - the deal's current `category_id`;
  - the deal's current `stage_id`;
  - the semantic corresponding to the current status: `S` for `won`, `F` for `lost`.
- If several exact matching final-stage entries exist because the deal was reopened and closed again into the same stage, use the latest `CREATED_TIME`; use history record ID as the deterministic tie-breaker.
- If an exact history record is missing for a currently closed deal, `MOVED_TIME` / `movedTime` may be used as a row-level fallback because it is the factual entry time into the current stage.
- `CLOSEDATE` must never be used as a fallback for factual closing or cycle calculations.
- If a currently closed deal has neither an exact final-stage history timestamp nor a valid current-stage `MOVED_TIME`, fail the refresh safely rather than silently producing a false close date.
- The existing public API field names such as `closed_date` may remain unchanged, but their meaning becomes the factual close timestamp.

## Unknowns

- Whether every legacy deal in the live tenant has complete stage-history records.
- Whether the current webhook permissions include `crm.stagehistory.list`.
- The total live stage-history volume and optimal batch size.

Do not resolve these unknowns with live calls during implementation. Implement mocked coverage, bounded batching, pagination, safe fallback, and clear operator errors.

## Scope

### 1. Inspect current repository state

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

Before editing run:

```bash
git log --oneline -8
git status --short
```

Do not overwrite unknown local changes.

### 2. Add a read-only Bitrix stage-history boundary

Add an allowlisted client method for:

```text
crm.stagehistory.list
```

Requirements:

- Always pass `entityTypeId = 2`.
- Fetch history only for deals whose current resolved status is `won` or `lost`.
- Use bounded deal-ID batches instead of one request per deal.
- Use the documented list pagination mechanism and consume every page.
- Filter to final-stage transitions where practical:

```text
TYPE_ID = 3
```

- Select only approved fields:

```text
ID
TYPE_ID
OWNER_ID
CREATED_TIME
CATEGORY_ID
STAGE_ID
STAGE_SEMANTIC_ID
```

- Accept official response shape `result.items` and any already-supported connector normalization pattern without wildcard fields.
- Keep webhook/error redaction intact.
- Add `crm.stagehistory.list` to the explicit read-only method allowlist.
- Keep every `crm.*.add`, `crm.*.update`, `crm.*.delete`, and `crm.*.set` method forbidden.

### 3. Add typed stage-history transformation

Add a typed local snapshot/model for the approved history fields.

Transformation requirements:

- Parse numeric IDs safely.
- Parse `CREATED_TIME` into UTC.
- Normalize stage semantics strictly to `S`, `F`, or `P` where present.
- Preserve exact `category_id` and `stage_id`.
- Reject malformed rows required for factual close resolution.
- Do not store the full raw Bitrix payload.

Implement a pure resolver for factual close time with explicit inputs:

- current deal ID;
- current category ID;
- current stage ID;
- current status group;
- current-stage `movedTime` fallback;
- stage-history rows.

Resolver behavior:

- `open` -> `null`;
- `won` -> latest exact `TYPE_ID=3`, category/stage match, semantic `S`;
- `lost` -> latest exact `TYPE_ID=3`, category/stage match, semantic `F`;
- exact matching history wins over `movedTime`;
- valid `movedTime` is the only allowed fallback for currently closed deals;
- no `CLOSEDATE` fallback;
- no usable factual timestamp for a closed deal -> explicit safe error.

### 4. Separate planned and factual close dates in the domain and storage

Stop using one ambiguous field for two meanings.

Required semantic fields:

```text
planned_close_at
actual_closed_at
```

- `planned_close_at` comes from Bitrix `CLOSEDATE` / `closedate`.
- `actual_closed_at` comes from the resolver described above.

Use an additive migration compatible with existing DuckDB files.

Requirements:

- Existing databases remain openable after deployment.
- Preserve legacy data; do not drop tables or recreate the database.
- Add the new columns to both raw and normalized deal storage as needed.
- If the legacy `closed_at` column must remain temporarily for compatibility, document it as deprecated and stop using it for analytics.
- Do not treat legacy `closed_at` values as factual close timestamps.
- Before the first post-deployment manual refresh, missing `actual_closed_at` must produce null/unavailable close analytics rather than silently falling back to legacy planned values.
- New successful refreshes populate both planned and factual timestamps.
- Update typed domain models, loaders, normalization, synthetic fixture builders, snapshot allowlists, schema/profile expectations, and serialization tests.

Add an approved raw history table or equivalent auditable local representation containing only:

```text
history_id
deal_id
type_id
created_at
category_id
stage_id
stage_semantic_id
```

The stage-history data must participate in the same transactional dataset replacement and approved Parquet snapshot policy as the other raw tables.

### 5. Integrate stage history into manual ingestion safely

Update the manual read-only refresh flow:

1. load category directory;
2. load category-aware stages;
3. load deals and contacts using existing safe methods;
4. resolve current deal status;
5. fetch final-stage history in batches for current won/lost deals;
6. transform and resolve `actual_closed_at`;
7. load raw data, normalize, load currency rates, write snapshots, and activate in one safe transaction.

Requirements:

- No per-deal N+1 API calls.
- A stage-history API error rolls back the refresh.
- A malformed or unresolved factual close timestamp for a currently closed deal rolls back the refresh with a safe message.
- The previous active dataset remains active and readable after a handled failure.
- Open deals never receive an actual close timestamp from an old history row.
- Reopened/reclosed deals use the latest exact current-final-stage entry.
- Repeated refresh is idempotent.

### 6. Replace planned close usage across analytics

Audit every usage of the legacy close field and explicitly classify it.

All factual close-dependent behavior must use `actual_closed_at`, including at minimum:

- Deals `closed_date` output and sorting;
- deal row `cycle_days`;
- Contacts `last_won_date`;
- Contacts average cycle;
- Deals filter-wide average cycle;
- deal-cycle report mean/median/P75/P90;
- close-date filters on Contacts/Deals where supported;
- ABC base and comparison periods;
- KEV close-date periods;
- won-revenue time series;
- RFM recency and latest won date;
- reactivation/stale-sales logic based on last successful close;
- won revenue and profit period filters;
- currency-rate date selection for won/lost closed deals.

Rules:

- Open deals have no factual close date and are excluded from close-date filters and closed-cycle denominators.
- Won/lost deals with factual close before creation are invalid and excluded from cycle calculations; the refresh should normally reject impossible source resolution before activation.
- Inclusive date-filter behavior remains unchanged, but applies to the factual date.
- Revenue remains won-only.
- Planned close date must not affect ABC, KEV, RFM, revenue series, cycle, or conversion reports.

### 7. Preserve compatible API and frontend behavior

Keep existing response field names and frontend contracts wherever practical.

- `closed_date` in Deals now means factual close date.
- The Deals column label `Дата закрытия` continues to display the factual date.
- Existing close-date filter controls now filter factual close time.
- Do not add a planned-close-date column or new UI screen in this task.
- Existing loading, error, empty, filter, sorting, sticky footer, pagination, auth, and refresh behavior must remain working.
- The frontend must display `—` when the factual date or cycle is unavailable.

### 8. Build deterministic fixtures and regression scenarios

Add synthetic/mocked datasets covering:

1. Planned date differs from actual close:
   - created in January;
   - `CLOSEDATE` in February;
   - final-stage history in June;
   - displayed close date and cycle use June.
2. Open deal with an old final-stage record:
   - current status open;
   - actual close remains null.
3. Reopened and reclosed into the same final stage:
   - multiple matching `TYPE_ID=3` records;
   - latest factual transition wins.
4. Final stage in another funnel or another final stage:
   - mismatched history is ignored.
5. Won and lost semantics:
   - `S` resolves won;
   - `F` resolves lost.
6. Missing exact history with valid `movedTime`:
   - fallback is used.
7. Missing history and missing `movedTime` for a closed deal:
   - refresh fails safely;
   - previous active dataset remains unchanged.
8. Pagination and multiple deal-ID batches.
9. Invalid/malformed history rows.
10. Timezone conversion to UTC and deterministic latest-record tie-breaking.

### 9. Required automated coverage

Add or update tests proving:

- `crm.stagehistory.list` is allowed and all write methods remain rejected;
- exact request parameters, approved select fields, batching, and pagination;
- nested `result.items` response parsing;
- no N+1 per-deal history pattern;
- pure factual-close resolver behavior for every scenario above;
- planned and factual dates are stored separately;
- additive migration opens an existing DuckDB file safely;
- legacy planned values are never consumed as factual close values;
- raw history storage and snapshots contain only approved columns;
- failed history loading preserves the previous active dataset;
- Deals displayed/API close date is factual;
- cycle uses factual close date;
- close-date filters are inclusive on factual close date;
- Contacts last-won date and average cycle use factual dates;
- ABC, KEV, RFM, revenue series, conversion, and period revenue use factual dates;
- currency rate selection for closed deals uses factual close date;
- open deals with old final history remain open with null actual close;
- existing funnel, KEV, contact `661`, summaries, sorting, auth, and read-only tests still pass.

Do not reduce existing coverage to make the suite pass.

### 10. Documentation and operator flow

Update:

- `SPEC.md`;
- `backend/README.md`;
- `frontend/README.md` only if visible semantics need clarification;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/deployment.md`;
- `docs/project-status.md`;
- `.ai/report.md`.

Document clearly:

- `CLOSEDATE` is planned and is not used as factual close time;
- factual close comes from the current final-stage transition;
- `crm.stagehistory.list` is read-only and uses `entityTypeId=2`;
- exact current category/stage/semantic matching;
- reopened deals use the latest matching closure;
- open deals have null actual close;
- `movedTime` is the only permitted fallback;
- no planned-date fallback;
- every close-dependent report uses factual close time;
- deployment requires one manual `Обновить из Bitrix` after updating;
- Docker startup does not refresh automatically.

Replace `.ai/report.md` with a clean report for this task only. Record exact commands and outcomes. Do not claim live verification unless a live call was explicitly performed; live calls are prohibited for implementation verification.

## Out Of Scope

- Displaying the planned close date in the frontend.
- A stage-history timeline screen.
- Time-in-stage analytics.
- Historical as-of reporting.
- Automatic or scheduled refresh.
- Background queues.
- Any Bitrix write method.
- Live Bitrix inspection during implementation.
- Unrelated frontend redesign.
- Production deployment itself.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and current repository documentation.
- Keep Bitrix strictly read-only.
- Allowed new Bitrix method:

```text
crm.stagehistory.list
```

- Existing allowed read methods remain unchanged.
- Never add or call:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Never use wildcard selects.
- Do not make live Bitrix calls.
- Do not expose or commit webhook URLs, credentials, `.env`, DuckDB files, raw private rows, Parquet/CSV exports with real data, logs, caches, `node_modules`, `frontend/dist`, browser artifacts, or temporary tooling.
- Do not modify `.ai/task.md` during implementation.
- Do not use `git add .`.
- Preserve transaction safety and the previous active dataset on handled refresh failure.
- Docker startup must continue to start services only.

## Acceptance Criteria

1. `CLOSEDATE` is preserved only as planned close information and is never used as factual close time.
2. Current open deals always have `actual_closed_at = null`.
3. Current won/lost deals resolve factual close from the latest exact current final-stage history record.
4. `movedTime` is used only as the documented fallback for a current final stage.
5. Missing both history and `movedTime` for a closed deal fails refresh safely.
6. `crm.stagehistory.list` uses read-only allowlisted, batched, paginated requests with approved fields.
7. No per-deal N+1 history loading is introduced.
8. Planned and factual timestamps are represented separately in domain/storage.
9. Existing DuckDB files migrate additively and remain openable.
10. Raw stage history is auditable and contains only approved columns.
11. Failed refresh does not replace or corrupt the previous active dataset.
12. Deals `closed_date` and `cycle_days` use factual close time.
13. Contacts, ABC, KEV, RFM, revenue series, cycle reports, date filters, and currency-rate selection use factual close time.
14. Planned close date has no effect on close analytics.
15. The January/February/June regression displays and calculates through June.
16. Reopened/reclosed deals use the latest exact closure.
17. Existing public API shape remains practical and frontend behavior remains compatible.
18. Full backend suite passes.
19. Frontend build passes.
20. Both Compose configurations pass.
21. Documentation is current and `.ai/report.md` is accurate.
22. No live Bitrix calls, writes, secrets, databases, or generated private data are committed.
23. Docker startup still does not refresh automatically.
24. Manual post-deployment refresh is documented.

## Checks

Before implementation:

```bash
git log --oneline -8
git status --short
```

Focused backend tests while implementing:

```bash
cd backend
python -m pytest tests/test_bitrix_client.py tests/test_bitrix_ingestion.py tests/test_storage.py tests/test_analytics.py tests/test_api_local.py
```

Use the actual existing test filenames if they differ; record them exactly.

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

Local operator flow must use synthetic data and disable live Bitrix:

```bash
BITRIX_WEBHOOK_URL="" docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
```

Exercise synthetic/local endpoints only. Do not click or call `Обновить из Bitrix` with live credentials.

After verification:

```bash
docker compose down -v
```

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src docs
rg 'select[^\n]*\*' backend/app backend/tests
```

Diff validation:

```bash
git diff --check -- ':!AGENTS.md' ':!.ai/task.md' ':!WORKFLOW.md'
git status --short --branch
git diff --name-only --cached
```

## Hard Workflow Gate

Before commit:

- factual close resolver tests pass for planned-vs-actual, open-after-close, reclose, mismatched stage/category, S/F semantics, movedTime fallback, missing fallback, and timezone cases;
- batch and pagination tests prove no N+1 history loading;
- existing-file migration test passes;
- previous-active-dataset preservation test passes;
- all close-dependent analytics are audited and covered;
- the complete backend suite passes;
- Python compileall passes;
- frontend build passes;
- both Compose configs pass;
- synthetic operator flow passes without any live Bitrix call;
- `.ai/report.md` contains exact current-task commands and outcomes only;
- documentation clearly separates planned and factual close dates;
- only task-related files and `.ai/report.md` are staged;
- no `.env`, secrets, databases, snapshots with real data, CSV, logs, caches, `node_modules`, `frontend/dist`, browser artifacts, temporary tooling, or `ui-kits/` changes are staged;
- no Bitrix write method or wildcard select is added;
- Docker startup behavior remains unchanged.

Set `.ai/report.md` status to `done` only after every acceptance criterion and check passes.

Commit message:

```text
codex: TASK-2026-07-20-06 Use actual deal close timestamps
```
