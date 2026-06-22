# Task: TASK-2026-06-22-10

Status: planned
Created from: current `main` at `92674a6` after review of `TASK-2026-06-22-09`

## Title

Reconcile contact 661 explicit deal IDs

## Goal

Finish the contact-deal completeness investigation using the exact Bitrix deal IDs now supplied by the user.

The user says Bitrix shows these 7 deals for `contact_id=661`:

```text
24761
23989
19149
14773
1239
343
123
```

`TASK-2026-06-22-09` found that local data and `crm.deal.list` filtered by `CONTACT_ID=661` both return only 4 deals:

```text
14773
19149
23989
24761
```

Therefore the concrete missing deals are:

```text
123
343
1239
```

This task must determine exactly where these three IDs diverge from the current pipeline and implement the smallest safe fix so contact analytics for `661` can be reconciled to the explicit Bitrix-visible deal list when the Bitrix per-deal relation data confirms the contact relationship.

## Facts

- Bitrix is read-only.
- CRM write methods remain forbidden:
  - `crm.*.add`
  - `crm.*.update`
  - `crm.*.delete`
  - `crm.*.set`
- Contact `661` has raw type `[61]`, normalized type `Дизайнер`, region `Беларусь`, priority `1`.
- Priority is not the root cause. `Дизайнер` priority `1` should win over lower-priority linked contacts.
- `TASK-2026-06-22-09` added local diagnostics and a `crm.deal.list CONTACT_ID` verification endpoint.
- `TASK-2026-06-22-09` was not accepted in review because it did not explain the three concrete missing deals and added a mutating `apply_local_correction` diagnostic path that bypasses dataset run/activation semantics.
- The existing normal sync source reconstructs links from `crm.deal.list` fields `CONTACT_ID` and `CONTACT_IDS`.
- The previous broad per-deal `crm.deal.contact.items.get` scan was removed from normal sync because it was too slow/heavy.
- Targeted use of `crm.deal.contact.items.get` for a supplied small list of deal IDs is acceptable if explicitly invoked, bounded, read-only, and reported without raw private rows.

## Assumptions

- The three missing deals may be present in local `raw_deals` but missing a local `raw_deal_contact_links` row for contact `661`.
- Or the deals may be absent from local `raw_deals` entirely.
- Or Bitrix per-deal contact relation data may show contact `661` even though `crm.deal.list CONTACT_ID=661` does not.
- Or the user-visible Bitrix card may count a relation that is not available through the currently allowed read-only relation methods.

## Unknowns

- Whether deals `123`, `343`, and `1239` exist in local `raw_deals`.
- Whether local `raw_deal_contact_links` contains any links for those deal IDs, and whether any link points to `661`.
- Whether local `normalized_deals` assigns those deal IDs to another analytical contact, no contact, or contact `661`.
- Whether Bitrix `crm.deal.contact.items.get` for deal IDs `123`, `343`, and `1239` includes contact `661`.
- Whether `crm.deal.list` filtered by explicit deal IDs returns safe deal rows for all seven supplied IDs.

## Scope

### 1. Add exact-ID local diagnostic

Extend the backend diagnostic capability to compare one contact ID against an explicit supplied deal ID list.

For contact `661` and deal IDs `123`, `343`, `1239`, `14773`, `19149`, `23989`, `24761`, it must report safe ID-level facts only:

- supplied contact ID;
- supplied deal IDs;
- which supplied deals exist in `raw_deals`;
- which supplied deals have a local `raw_deal_contact_links` row to contact `661`;
- all local linked contact IDs for each supplied deal, without contact phones/emails/addresses/etc.;
- normalized analytical contact ID for each supplied deal;
- whether each supplied deal would count in contact `661` analytics;
- concise per-deal divergence reason.

Do not expose forbidden personal fields, raw API payloads, webhook values, comments, files, requisites, phone, email, address, messengers, arbitrary custom fields, local paths, or generated data contents.

### 2. Add exact-ID read-only Bitrix verification

Add or adjust a targeted live verification path for explicit deal IDs.

It must be explicitly invoked only; no Docker startup, page load, report endpoint, or normal refresh may call it automatically.

Allowed targeted read-only methods for this task:

- `crm.deal.list` with safe `select` from the existing deal allowlist and a filter bounded to the supplied deal IDs;
- `crm.deal.contact.items.get` for exactly the supplied deal IDs, one call per supplied ID, with a hard count bound.

Do not add `crm.deal.get` unless there is a clear reason and the implementation prevents forbidden fields from being stored, logged, or returned. Prefer `crm.deal.list` with explicit safe `select`.

The verification must report only aggregate/ID-level facts:

- which supplied deal IDs Bitrix returned via safe deal list;
- for each supplied deal ID, whether `crm.deal.contact.items.get` contains contact `661`;
- returned contact IDs for each supplied deal link set, if safe and needed;
- method names used;
- counts and divergence categories.

### 3. Fix the data path for this reconciliation

If Bitrix per-deal relation data confirms that deals `123`, `343`, and `1239` are linked to contact `661`, implement a safe correction path so local analytics can include them for `661`.

Important: do not keep a mutating diagnostic endpoint that silently edits local raw tables outside dataset run/activation semantics.

Acceptable approaches:

- make the explicit-ID correction a deliberate backend/operator helper that records a local dataset run/status and reruns normalization; or
- integrate a bounded, explicitly invoked reconciliation function into the existing local refresh/ingestion pipeline without changing Docker startup behavior; or
- if only a diagnostic result is safe in this task, remove/disable mutating `apply_local_correction` and mark the task `blocked` with exact evidence and the next required product decision.

If a correction is applied, it must:

- affect only supplied deal IDs and supplied contact ID;
- use only read-only Bitrix data;
- preserve all existing deal fields from local raw data when the deal already exists;
- insert only allowed safe deal fields if a supplied deal is missing from local `raw_deals`;
- insert only allowed link fields into `raw_deal_contact_links`;
- rerun normalization;
- keep each deal counted only once through analytical contact selection;
- ensure contact `661` wins for these deals when its confirmed link exists and lower-priority contacts are also linked;
- avoid changing unrelated contacts/deals.

### 4. Clean up TASK-09 diagnostic mutation risk

Review the `apply_local_correction` path added in `TASK-2026-06-22-09`.

Do one of the following:

- remove the public/API ability to mutate local raw/normalized data through `/api/internal/diagnostics/.../verify-bitrix-deals`; or
- refactor it into the safe explicit-ID reconciliation path described above with proper bounds, tests, and status/reporting.

By default, diagnostics should be read-only. Mutating reconciliation must be explicit, bounded, documented, and not disguised as a verification endpoint.

### 5. Tests

Add focused backend tests for:

- exact-ID local diagnostic categorizes: missing raw deal, missing local link, assigned to another analytical contact, assigned to contact `661`;
- exact-ID Bitrix verification calls only allowed read-only methods and is bounded to the supplied deal IDs;
- if per-deal link data includes contact `661`, the reconciliation path inserts/repairs only the missing links for supplied IDs and analytics count for `661` becomes 7 in the test scenario;
- designer priority `1` still wins over lower-priority primary contacts;
- diagnostics do not expose forbidden personal fields;
- CRM write methods remain rejected/not introduced.

### 6. Documentation/report

Update `.ai/report.md` with:

- exact root cause for deals `123`, `343`, and `1239`;
- local status of all seven supplied deal IDs;
- whether live Bitrix was called;
- if live Bitrix was called, method names, supplied IDs, aggregate counts, and safe divergence summary only;
- whether any local correction/reconciliation was applied;
- if correction was applied, exactly which deal IDs/links were changed and how analytics changed;
- confirmation that no write methods were added or called;
- checks run and results.

Update `docs/development.md` and/or `docs/data-model.md` only if diagnostic/reconciliation behavior changes.

## Out Of Scope

- New frontend screens.
- Redesign of Contacts UI.
- ABC/RFM/concentration/type-region screens.
- Automatic background refresh.
- Scheduled sync.
- Broad unbounded scan of all deals with `crm.deal.contact.items.get`.
- Companies, leads, products, calls, emails, comments, activities, files, requisites.
- CSV export.
- Any Bitrix write operation.
- Large unrelated refactors.

## Constraints

- Bitrix remains read-only.
- Do not add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit `.env`, local databases, Parquet snapshots, raw exports, logs, caches, build artifacts, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Do not print webhook URLs or tokens.
- Do not expose forbidden personal fields.
- Do not make Docker Compose auto-refresh Bitrix data.
- Keep changes focused on reconciling contact `661` and the seven explicit deal IDs.
- If exact-ID live Bitrix verification cannot be run safely, stop and mark blocked with the reason.

## Acceptance Criteria

- `.ai/report.md` explains each supplied deal ID: `123`, `343`, `1239`, `14773`, `19149`, `23989`, `24761`.
- The report identifies the exact root cause for why `123`, `343`, and `1239` were not counted locally for contact `661`.
- If Bitrix per-deal relation data confirms contact `661` on the missing deals, local analytics can be reconciled so contact `661` counts 7 deals after the explicit correction/reconciliation path.
- If Bitrix per-deal relation data does not confirm contact `661`, the report states that clearly and no local data is changed.
- The mutating `apply_local_correction` risk from `TASK-09` is removed or refactored into a bounded explicit reconciliation path with tests.
- Diagnostics remain read-only by default.
- No Bitrix write methods are added or called.
- No forbidden personal fields are fetched beyond allowlists, stored, logged, returned, or documented.
- Relevant backend tests pass.
- Frontend build is run only if frontend code changes.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-10 Reconcile contact 661 explicit deal IDs
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

Run frontend build only if frontend code changes:

```bash
cd frontend
npm run build
```

Run Compose smoke checks only if runtime/operator startup behavior changes:

```bash
docker compose config
docker compose up --build -d
curl -f http://localhost:8000/health
curl -f http://localhost:5173/
docker compose down -v
```

Run safety search before committing:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests
```

Before committing:

```bash
git status --short --branch
git diff --stat HEAD
git diff --name-only --cached
git diff --check -- ':!AGENTS.md' ':!.ai/task.md'
```

## Hard Workflow Gate

Codex must not commit until all conditions below are true:

- the latest relevant commit is this planner commit;
- the seven supplied deal IDs have been checked locally;
- if live Bitrix verification is run, it is limited to the seven supplied deal IDs and read-only methods only;
- `.ai/report.md` documents the exact result for deals `123`, `343`, and `1239`;
- the `TASK-09` mutating diagnostic endpoint risk is removed or safely refactored;
- every required check is either run and reported, or explicitly documented as not run with reason;
- `.ai/report.md` explicitly states whether any live Bitrix call was or was not run;
- `.ai/report.md` explicitly states that no Bitrix write methods were added or called;
- staged files are only files intentionally changed for `TASK-2026-06-22-10` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
