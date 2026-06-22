# Task: TASK-2026-06-22-20

Status: planned
Created from: current `main` after accepted review of `TASK-2026-06-22-19`

## Title

Stabilize filter metadata endpoint

## Goal

Fix the remaining runtime console error from the frontend:

```text
GET http://localhost:5173/api/meta/filters 503 (Service Unavailable)
```

The app must keep filter dropdowns stable without relying on a normal `503` response from `/api/meta/filters`.

## User Request

The user reported the current browser console output:

```text
Download the React DevTools for a better development experience: https://react.dev/link/react-devtools
api.ts:239 GET http://localhost:5173/api/meta/filters 503 (Service Unavailable)
```

## Facts

- The React DevTools line is a normal React/Vite development-mode informational message. It is not an application bug and should not be suppressed.
- Current `/api/meta/filters` calls `get_filter_metadata(connection)` and then checks active dataset status.
- Current backend intentionally raises `503` when:
  - an active successful dataset exists;
  - `normalized_contacts_count > 0`;
  - `filters.contact_types` is empty.
- That guard was added to prevent transient/invalid empty metadata from wiping frontend dropdown options.
- In real UI usage this produces a visible network error in the browser console.
- Current `get_filter_metadata()` reads:
  - contact types from `normalized_contacts.contact_type_normalized`;
  - regions from `normalized_contacts.region_normalized`;
  - statuses and date ranges from `normalized_deals`.
- Current data model also has normalized deal type/region fields and active `contact_type_rules` with configured normalized types/regions.
- Frontend already keeps a cached copy of the last valid filter metadata under `bitrix-sales.filter-metadata.v1`.
- Frontend must call only local backend endpoints.
- Report/filter APIs must not call Bitrix, NBRB, or external services.

## Assumptions

- `503` from `/api/meta/filters` is not acceptable as normal behavior for an active local dataset because it creates noisy console errors and can leave the UI without filter options when no cache exists.
- The correct fix is backend-first: make `/api/meta/filters` return a safe stable `200` metadata response for prepared local datasets, rather than making the frontend hide an expected failure.
- A stable metadata response may use safe local fallback sources when normalized contact metadata is temporarily incomplete:
  - distinct non-empty normalized type/region values from `normalized_contacts`;
  - distinct non-empty normalized type/region values from `normalized_deals`;
  - distinct non-empty active configured values from `contact_type_rules`.
- Fallback metadata must not expose raw Bitrix option IDs, raw contact rows, secrets, local paths, phones, emails, addresses, messengers, comments, files, requisites, or arbitrary custom fields.
- If no active/prepared dataset exists, empty filter metadata can still be returned safely as `200`.

## Unknowns

- The exact live local dataset shape that caused empty `contact_types` is unknown. Codex must reproduce the behavior with a minimal local fixture and document the root cause in `.ai/report.md`.
- Browser click-through may depend on the execution environment. If unavailable, document the limitation in `.ai/report.md`.

## Scope

### 1. Diagnose `/api/meta/filters` 503

Investigate the current backend metadata path and identify why the active dataset can produce empty `contact_types`.

Requirements:

- reproduce the current `503` behavior with a focused backend/API test before or during the fix;
- document the root cause in `.ai/report.md`;
- do not use live Bitrix calls for diagnosis;
- do not expose raw rows, secrets, local paths, webhook values, or forbidden personal fields.

### 2. Make metadata stable without normal 503

Change backend metadata generation so `/api/meta/filters` returns `200` for normal prepared local dataset states.

Requirements:

- remove the current normal-path `503` guard for empty `contact_types`;
- prevent dropdowns from collapsing to empty when safe local fallback metadata exists;
- build `contact_types` and `regions` from safe local sources, recommended priority/union:
  1. distinct normalized contact values from `normalized_contacts`;
  2. distinct normalized deal values from `normalized_deals`;
  3. distinct active configured values from `contact_type_rules`;
- filter out `NULL` and blank values;
- de-duplicate and sort deterministically;
- keep statuses/date ranges from local normalized deals;
- do not return raw type IDs or raw contact type strings in `/api/meta/filters`;
- keep empty `200` metadata allowed only when no active/prepared dataset exists or the local database is genuinely empty.

If the chosen implementation differs from the recommended source union, explain why in `.ai/report.md` and cover it with tests.

### 3. Preserve frontend cache protection

Review the frontend metadata handling and keep the useful cache behavior:

- do not clear `bitrix-sales.filter-metadata.v1` when metadata fetch fails unexpectedly;
- do not wipe dropdown options if a transient invalid metadata response is received;
- do not add frontend Bitrix calls;
- avoid noisy expected errors in normal operation.

If backend no longer returns normal-path `503`, frontend changes may be minimal or unnecessary. Do not refactor the whole frontend.

### 4. Documentation and report

Update relevant docs if behavior changes, at minimum consider:

- `docs/development.md` for stable metadata behavior;
- `docs/data-model.md` if metadata fallback sources are documented;
- `frontend/README.md` if frontend cache behavior wording changes;
- `docs/project-status.md` if useful.

Update `.ai/report.md` with:

- actual root cause of the `/api/meta/filters 503`;
- implementation details;
- checks run;
- note that the React DevTools console line is expected in dev mode;
- confirmation that no Bitrix calls/write methods were added.

## Out Of Scope

- New report screens.
- Changing Bitrix ingestion, extraction, contact-deal link logic, reconciliation, or manual refresh behavior.
- Any live Bitrix diagnostic call.
- Any Bitrix write operation.
- Displaying forbidden personal fields or raw Bitrix rows.
- Changing contact priority rules, type normalization semantics, currency loading, report metric formulas, or manual refresh semantics.
- Adding CSV/export, authentication, scheduler, or automatic refresh.
- Modifying `ui-kits/`.

## Constraints

- Work only from current repository files.
- Keep Bitrix read-only.
- Frontend must call only local backend endpoints.
- Metadata/report APIs must read local DuckDB-backed data only.
- Do not add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit `.env`, DuckDB files, Parquet snapshots, raw exports, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Do not expose webhook values, raw rows, local absolute paths, stack traces, or forbidden personal fields.

## Acceptance Criteria

- `/api/meta/filters` no longer returns `503` for the current normal active-dataset case where contact type metadata can be recovered from safe local fallback sources.
- A regression test covers the previous `503` shape: active successful dataset, contacts present, `normalized_contacts.contact_type_normalized` empty or unavailable, and safe fallback values available.
- The response contains stable non-empty `contact_types` and `regions` when fallback local sources have values.
- The response remains deterministic: values are de-duplicated and sorted.
- Empty `200` metadata remains allowed for an unprepared or genuinely empty local database.
- Frontend dropdown cache protection remains intact.
- The browser should not show an expected `GET /api/meta/filters 503` during normal active-dataset operation.
- React DevTools console line is documented as expected dev-mode behavior, not treated as a bug.
- No frontend Bitrix calls are added.
- No backend metadata/report endpoint calls Bitrix, NBRB, or external services.
- No Bitrix write methods are added.
- Relevant backend tests and frontend build pass, or any inability is explicitly documented with reason.
- Documentation and `.ai/report.md` are updated.
- Commit message exactly:

```text
codex: TASK-2026-06-22-20 Stabilize filter metadata endpoint
```

## Checks

Run before implementation:

```bash
git log --oneline -5
git status --short
```

Run backend tests after backend changes:

```bash
cd backend
python -m pytest
```

Use the existing backend dev environment if system Python lacks pytest and document the exact command.

Run frontend build if frontend code changes:

```bash
cd frontend
npm run build
```

Run safety search before committing:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src
```

Before committing:

```bash
git status --short --branch
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

If practical for the environment, run an operator smoke check:

```bash
docker compose config
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
curl -f http://localhost:8000/api/meta/filters
docker compose down
```

If Docker/browser checks cannot be run, document the reason in `.ai/report.md`.

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- latest relevant commit is this planner commit;
- `/api/meta/filters 503` root cause is understood and documented;
- metadata fallback is local-only, safe, deterministic, and tested;
- the endpoint no longer uses `503` as the expected normal protection against empty dropdowns;
- frontend metadata cache protection is preserved;
- no frontend Bitrix calls are added;
- no Bitrix write methods are added anywhere;
- required backend tests and frontend build if applicable are run, or inability is explicitly documented;
- `.ai/report.md` describes implementation, checks, facts, unknowns, and risks;
- staged files are only task files plus `.ai/report.md` and relevant docs;
- forbidden artifacts are not staged;
- final commit message exactly matches the required `codex:` message above.
