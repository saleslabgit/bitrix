# Task: TASK-2026-07-20-06

Status: planned
Created from: `16bd3ef49e046e7072b4113e50df31c5439b0382`

## Title

Complete factual close timestamp handling in explicit deal reconciliation

## Goal

Repair the remaining rejected path in the factual deal-close implementation.

The normal manual Bitrix refresh now separates planned `CLOSEDATE` from factual `actual_closed_at` and resolves the factual timestamp from exact final-stage history with `movedTime` as the only fallback. Preserve that implementation.

The explicit contact-deal reconciliation path must follow the same factual-close contract before it inserts, normalizes, or activates any closed deal.

## Review Status

The following implementation commit was reviewed and rejected:

```text
16bd3ef49e046e7072b4113e50df31c5439b0382
```

The implementation is mostly correct. Do not revert the stage-history client, additive migration, factual-close analytics, documentation, or completed tests.

One blocking defect remains in `backend/app/reports/contact_deal_diagnostics.py`.

## Verified Remaining Defect

`reconcile_explicit_contact_deals()` can currently activate a closed deal without a factual close timestamp.

The current flow:

1. loads explicit deal rows from Bitrix;
2. calls `transform_deals()` for missing local deals;
3. `transform_deals()` sets `actual_closed_at = None` before history resolution;
4. inserts the deal through `_insert_raw_deals()`;
5. normalizes data and records a successful active reconciliation run.

The reconciliation path does not:

- call `crm.stagehistory.list`;
- call `transform_deal_stage_history()`;
- call `apply_actual_close_times()`;
- persist approved history rows;
- reject a closed deal that has neither exact history nor `movedTime`.

`_insert_raw_deals()` also does not currently preserve the complete approved deal state. It omits at least:

- `planned_close_at`;
- `kev_held`;
- approved stage-history rows.

This can produce an active closed deal with:

- `actual_closed_at = NULL`;
- no factual `closed_date` in reports;
- no cycle;
- missing planned close information;
- a wrong default KEV value;
- no auditable local final-stage history.

## Facts

- Bitrix remains strictly read-only.
- `CLOSEDATE` / `closedTime` is planned close information only.
- `actual_closed_at` is the factual timestamp used by all close-dependent analytics.
- A current open deal always has `actual_closed_at = NULL`.
- A current won/lost deal must resolve factual close from:
  1. the latest exact current final-stage history record; or
  2. current-stage `movedTime` as the only fallback.
- `CLOSEDATE` must never be used as a factual fallback.
- The existing `BitrixClient.list_deal_stage_history()` already provides bounded batched and paginated read-only loading.
- The existing `apply_actual_close_times()` already implements the approved resolver contract.
- The normal manual refresh already stores approved raw history transactionally.
- Explicit reconciliation is bounded to a small operator-supplied deal-ID set.
- The previous active dataset must remain unchanged on handled reconciliation failure.
- Docker startup must not call Bitrix or refresh data automatically.

## Assumptions

- Reuse the existing stage-history client, transformer, and factual-close resolver rather than implementing a second version.
- For every confirmed reconciliation deal that is closed and either missing locally or missing `actual_closed_at`, reconciliation must resolve the current factual close before activation.
- Existing local deals that already contain a valid factual timestamp do not need to be overwritten unnecessarily.
- Approved history rows for the affected deals may be inserted with an idempotent upsert/replace strategy consistent with the current raw dataset model.
- The existing public reconciliation response shape should remain compatible unless a small additive safe field is required.

## Unknowns

- Live tenant history completeness and webhook permission remain intentionally unverified.
- Do not make live Bitrix calls while implementing or testing this correction.

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

Inspect at minimum:

- `reconcile_explicit_contact_deals()`;
- `_collect_bitrix_explicit_deal_facts()`;
- `_insert_raw_deals()`;
- the reconciliation API endpoint and response handling;
- `BitrixClient.list_deal_stage_history()`;
- `transform_deals()`;
- `transform_deal_stage_history()`;
- `apply_actual_close_times()`;
- raw history storage and normalization;
- reconciliation tests.

Before editing run:

```bash
git log --oneline -8
git status --short
```

Do not overwrite unknown local changes.

### 2. Resolve factual close timestamps in explicit reconciliation

For confirmed deals that reconciliation will insert or materially update:

1. collect current Bitrix deal rows using the existing bounded explicit-deal flow;
2. transform current stages and statuses using the existing exact `(stage_id, category_id)` directory;
3. identify current won/lost deals that require factual resolution;
4. call `client.list_deal_stage_history()` once for the bounded set, not once per deal;
5. transform history with `transform_deal_stage_history()`;
6. resolve deals with `apply_actual_close_times()`;
7. only then begin or continue the local write/activation transaction.

Requirements:

- No per-deal history N+1 pattern.
- Open deals remain `actual_closed_at = NULL` even if old final history exists.
- Won deals require exact semantic `S`; lost deals require exact semantic `F`.
- Category and stage must match the deal's current values.
- Reopened/reclosed deals use the latest exact matching transition.
- Exact history wins over `movedTime`.
- `movedTime` is the only fallback.
- Never use `CLOSEDATE` as factual close.
- A factual timestamp before `created_at` is invalid.
- Missing both exact history and `movedTime` for a current closed deal must fail safely before activation.

### 3. Cover existing confirmed deals with missing factual timestamps

Do not limit the correction only to brand-new raw deal rows.

For each operator-confirmed deal involved in reconciliation:

- if the deal is currently won/lost and the local row has no `actual_closed_at`, resolve and update it transactionally;
- if the deal is open, ensure the factual value is `NULL`;
- if a valid local factual value already exists and the current deal facts have not changed, avoid unnecessary destructive rewriting;
- do not promote legacy `closed_at` into `actual_closed_at`.

The reconciliation must not report success while any affected current closed deal remains without a valid factual timestamp.

### 4. Preserve the full approved deal fields

Update `_insert_raw_deals()` or the appropriate shared loader so reconciled deal rows preserve:

- `deal_id`;
- `deal_name`;
- `amount_original`;
- `currency_original`;
- `created_at`;
- deprecated physical `closed_at` as `NULL`;
- `planned_close_at` from `CLOSEDATE`;
- `actual_closed_at` from factual resolution;
- `stage_id`;
- `category_id`;
- `status_group`;
- `kev_held`.

Do not rely on database defaults for approved values already returned and transformed from Bitrix.

Keep the insert/update idempotent and limited to explicitly confirmed deal IDs.

### 5. Persist approved stage history transactionally

Store the transformed approved history rows for affected reconciliation deals in `raw_deal_stage_history`.

Requirements:

- only the seven approved columns are stored;
- no full Bitrix payload is persisted;
- repeated reconciliation is idempotent;
- history writes, deal writes, link writes, normalization, status storage, and activation succeed or fail together;
- do not delete unrelated history rows;
- use deterministic conflict handling for existing `history_id` values.

### 6. Preserve previous active data on failure

A handled failure during:

- history loading;
- history transformation;
- factual-close resolution;
- deal/history/link storage;
- normalization;
- activation;

must not leave partial raw or normalized changes and must not replace the previous active dataset.

Requirements:

- no transaction begins before remote facts are sufficiently validated, where practical;
- any exception after transaction start rolls back all task writes;
- store or return a safe reconciliation error consistent with the existing API/operator contract;
- error text must not expose the webhook URL, token, raw private rows, or full Bitrix payload;
- `.ai/report.md` must describe the exact failure behavior tested.

### 7. Preserve the completed TASK-06 implementation

Do not regress:

- read-only `crm.stagehistory.list` allowlisting;
- approved select fields;
- batching and pagination;
- official `result.items` parsing;
- exact factual-close resolver semantics;
- additive DuckDB migration;
- normal manual refresh safety;
- factual close usage in Deals, Contacts, ABC, KEV, RFM, revenue series, cycle reports, filters, metadata, profile, and currency-rate selection;
- sticky table footers;
- authentication;
- contact `661` assignment regression;
- funnel/category semantics;
- KEV behavior;
- Docker startup behavior.

### 8. Add focused reconciliation regression tests

Add tests covering at minimum:

#### New closed deal: planned February, actual June

- explicit deal created in January;
- Bitrix `CLOSEDATE` is in February;
- exact final-stage history is in June;
- `movedTime` may differ to prove exact history wins;
- reconciliation succeeds;
- `planned_close_at` stores February;
- `actual_closed_at` stores June;
- deprecated physical `closed_at` remains `NULL`;
- `kev_held` preserves the transformed Bitrix value;
- raw approved history is stored;
- normalized deal and Deals API display June;
- cycle is calculated through June.

#### Open deal with old close history

- current status is open;
- old final-stage history exists;
- reconciliation stores or preserves `actual_closed_at = NULL`.

#### Reopened/reclosed deal

- several exact final-stage records exist;
- latest exact current-stage record wins.

#### Existing local closed deal missing factual close

- raw deal already exists with `actual_closed_at = NULL`;
- reconciliation confirms it;
- factual history is resolved and the local row is updated transactionally.

#### `movedTime` fallback

- exact history is missing;
- valid current-stage `movedTime` exists;
- factual close is populated from `movedTime`.

#### Safe failure

- closed confirmed deal has neither exact history nor `movedTime`, or history loading fails;
- no raw deal, history, or link partial write remains;
- normalized data remains unchanged;
- previous active dataset remains active;
- reconciliation is not reported as successful.

#### Batching

- multiple closed reconciliation deals use the existing bounded batched history method;
- prove there is no one-history-request-per-deal implementation.

#### Idempotency

- running the same successful reconciliation twice does not duplicate history, deals, or links and does not corrupt status.

### 9. Documentation and report

Update only documentation that needs to describe the corrected operator path, including as applicable:

- `backend/README.md`;
- `docs/data-model.md`;
- `docs/development.md`;
- `docs/project-status.md`;
- `.ai/report.md`.

Document that explicit reconciliation follows the same factual-close contract as normal refresh and cannot activate a current closed deal without history or `movedTime`.

Replace `.ai/report.md` with an accurate report for this correction. The previous `done` report is not proof and must not remain unchanged.

## Out Of Scope

- Changing the approved factual-close business rule.
- Displaying planned close date in the frontend.
- New UI screens or stage-history timelines.
- Time-in-stage analytics.
- Historical as-of reporting.
- Automatic or scheduled refresh.
- Broad reconciliation redesign unrelated to factual close correctness.
- Any Bitrix write operation.
- Live Bitrix inspection.
- Production deployment.

## Constraints

- Follow current repository instructions and documentation.
- Keep Bitrix strictly read-only.
- Reuse the existing approved read method:

```text
crm.stagehistory.list
```

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
- Do not expose or commit secrets, real `.env`, DuckDB files, real Parquet/CSV data, raw private rows, logs, caches, `node_modules`, `frontend/dist`, browser artifacts, or temporary tooling.
- Keep history loading bounded to explicit deal IDs.
- Preserve previous active data on every handled failure.
- Docker startup must continue to start services only.

## Acceptance Criteria

1. Explicit reconciliation uses the existing batched read-only stage-history boundary for affected closed deals.
2. No history N+1 request pattern is introduced.
3. Newly inserted won/lost deals cannot remain with `actual_closed_at = NULL` after successful reconciliation.
4. Existing confirmed won/lost deals missing factual close are repaired before successful activation.
5. Open deals always keep `actual_closed_at = NULL`.
6. Exact current category/stage/semantic history wins and latest exact reclose is selected.
7. `movedTime` is the only fallback.
8. `CLOSEDATE` is stored only as `planned_close_at` and never used factually.
9. Reconciled deals preserve `planned_close_at`, `actual_closed_at`, and `kev_held`.
10. Deprecated physical `closed_at` remains unused and is not populated from planned data.
11. Approved raw history is stored transactionally and idempotently.
12. Failed resolution/history loading causes no partial deal, history, link, normalized, or activation changes.
13. Previous active dataset remains active after handled reconciliation failure.
14. The January/February/June explicit reconciliation regression displays and calculates through June.
15. Existing normal refresh and all factual-close analytics remain correct.
16. Full backend suite passes.
17. Frontend build passes.
18. Both Compose configurations pass.
19. Documentation and `.ai/report.md` are accurate.
20. No live Bitrix calls, writes, wildcard selects, secrets, databases, or generated private data are committed.
21. Docker startup remains unchanged.

## Checks

Before implementation:

```bash
git log --oneline -8
git status --short
```

Focused backend tests:

```bash
cd backend
python -m pytest tests/test_bitrix_client.py tests/test_bitrix_ingestion.py tests/test_contact_deal_diagnostics.py tests/test_analytics.py tests/test_api_bitrix.py tests/test_api_local.py
```

Use actual existing test filenames and record the exact command.

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

Do not call the live reconciliation or refresh endpoints with real credentials.

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

- explicit reconciliation January/February/June regression passes;
- new and existing closed-deal factual resolution tests pass;
- open-after-close, reclose, exact match, `movedTime` fallback, and missing fallback tests pass;
- batching proves no N+1 history requests;
- planned date, factual date, KEV, and approved raw history persistence are verified;
- failed reconciliation preserves raw, normalized, and active dataset state;
- idempotency test passes;
- complete backend suite passes;
- Python compileall passes;
- frontend build passes;
- both Compose configurations pass;
- synthetic/mocked operator flow passes without live Bitrix access;
- `.ai/report.md` contains exact current correction results only;
- only task-related files and `.ai/report.md` are staged;
- no `.env`, secrets, databases, real snapshots, CSV, raw private data, logs, caches, `node_modules`, `frontend/dist`, browser artifacts, temporary tooling, or `ui-kits/` changes are staged;
- no Bitrix write method or wildcard select is added;
- Docker startup behavior remains unchanged.

Set `.ai/report.md` status to `done` only after every acceptance criterion and hard gate passes.

Commit message:

```text
codex: TASK-2026-07-20-06 Fix reconciliation factual close timestamps
```
