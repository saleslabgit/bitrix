# Task: TASK-2026-06-22-09

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-08`

## Title

Fix contact-deal link completeness

## Goal

Investigate and fix the data completeness issue where Bitrix shows more deals for a contact than the local Contacts analytics table.

The concrete user-reported case is contact `661`:

- Bitrix contact card shows `7` deals.
- Local Contacts table currently shows `4` deals.
- This contact has Bitrix type `[61]` / `Дизайнер`, which maps to normalized type `Дизайнер` and priority `1`.

Because `Дизайнер` has the highest active priority, this mismatch is not explained by analytical-contact priority. If a deal is linked to contact `661`, contact `661` should normally win analytical-contact selection over lower-priority linked contacts.

The task must identify where the missing three deals are lost and fix the read-only extraction/local normalization path so local contact analytics can match Bitrix for this case.

## Facts

- Bitrix is read-only in this project.
- No Bitrix CRM write methods may be added or called.
- Current Contacts screen uses `GET /api/reports/contacts/analytics`.
- Current local analytics counts deals by `analytical_contact_id`.
- Current deal-contact links are reconstructed from `crm.deal.list` deal fields `CONTACT_ID` and `CONTACT_IDS` via `transform_deal_contact_links_from_deals`.
- Previous mass per-deal `crm.deal.contact.items.get` style extraction was removed because it was too slow/heavy for live sync.
- The user confirmed the contact type priority is not the cause for contact `661`.
- Local/manual refresh may take several minutes and must remain explicitly user-triggered.

## Assumptions

- The local mismatch is likely caused by incomplete extraction of deal-contact links, incomplete deal ingestion, or a mismatch between Bitrix contact-card deal visibility and the fields currently selected by `crm.deal.list`.
- A targeted diagnostic for one contact is safe if it uses only read-only methods and does not expose secrets or forbidden personal fields.
- Any broader fix must avoid unbounded long per-deal calls without batching, progress visibility, or clear operator expectations.

## Unknowns

- Whether Bitrix `CONTACT_ID` / `CONTACT_IDS` in the current `crm.deal.list` response are complete for all linked contacts.
- Whether the missing contact `661` deals are absent from raw deals, absent from raw deal-contact links, or present but not selected as analytical deals.
- Which read-only Bitrix endpoint/method is the correct scalable source of deal-contact links for this project stage.
- Whether Bitrix contact card includes deals that are visible through a different relation path than the current deal list fields.

## Scope

### 1. Add targeted local diagnostics

Add a backend-only diagnostic capability for a single contact ID, preferably under an internal/debug route or script that is not exposed as a public report screen.

For `contact_id=661`, the diagnostic must report safe aggregate/ID-level information only:

- contact ID;
- contact name if already available in allowed local data;
- raw Bitrix type ID(s);
- normalized type;
- region;
- priority;
- raw/local linked deals from local deal-contact links;
- analytical deals from normalized/local analytics data;
- whether each linked deal exists in raw deals;
- deal status group where already available locally;
- concise explanation of where the count diverges.

Do not expose phone, email, address, messenger, comments, files, requisites, webhook values, raw API payload dumps, or arbitrary Bitrix custom fields.

### 2. Add targeted read-only Bitrix verification if needed

If local-only diagnostics cannot explain the mismatch, add a targeted read-only verification path for one contact ID.

The verification may call Bitrix only when explicitly invoked by the operator/developer, not during Docker startup and not during normal page load.

It must:

- be limited to a supplied contact ID;
- avoid CRM write methods;
- avoid dumping raw private rows;
- compare Bitrix-visible deal IDs for the contact with local deal IDs/link IDs;
- include clear timeout/bounds or pagination handling;
- document which Bitrix read-only method(s) it uses.

Do not run a broad live Bitrix sync as part of tests unless explicitly required. If a live targeted verification for `661` is run, record that fact in `.ai/report.md` including method names, counts, and safety notes, without secrets or raw personal data.

### 3. Fix extraction/local normalization based on findings

Once the missing point is identified, fix the smallest correct part of the pipeline.

Possible acceptable fixes include:

- correcting parsing of `CONTACT_IDS` if the current parser misses a Bitrix response shape;
- expanding the safe allowlist only for non-personal relationship fields if needed;
- adding a bounded/batched read-only link extraction strategy if `CONTACT_ID` / `CONTACT_IDS` are proven incomplete;
- improving normalization so locally present links correctly select the analytical contact.

The fix must preserve these rules:

- deals are counted only once in contact analytics;
- analytical contact selection uses configured active contact-type priorities;
- `Дизайнер` priority `1` outranks dealer/contractor/final-client priorities;
- won revenue uses USD conversion logic already implemented;
- no forbidden personal fields are fetched, stored, logged, displayed, or committed.

### 4. Tests and regression coverage

Add or update tests that reproduce the discovered failure mode where practical.

At minimum, cover:

- contact `Дизайнер` with priority `1` wins analytical selection when linked to a deal;
- multi-contact deal links are not dropped for the Bitrix response shape found during investigation;
- contact analytics count matches the normalized deal/link facts in the tested scenario;
- forbidden Bitrix write methods remain rejected/not introduced.

### 5. Documentation/report

Update `.ai/report.md` with:

- root cause;
- exact files changed;
- whether live Bitrix was called;
- if live Bitrix was called, which read-only methods were used and for which contact ID/counts;
- confirmation that no write methods were added or called;
- how to reproduce/check the diagnostic safely.

Update project docs only if behavior, operator flow, Bitrix extraction rules, or diagnostics become part of the ongoing workflow.

## Out Of Scope

- New frontend report screens.
- Redesign of Contacts UI.
- ABC/RFM/concentration/type-region screens.
- Automatic background refresh.
- Scheduled sync.
- Companies, leads, products, calls, emails, comments, activities, files, requisites.
- Export features.
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
- Keep changes focused on data correctness for contact-deal links and contact analytics.

## Acceptance Criteria

- The implementation explains the `contact_id=661` mismatch: why Bitrix shows `7` deals while local analytics showed `4`.
- The root cause is documented in `.ai/report.md`.
- The extraction/local normalization path is fixed so local contact analytics can include all relevant deals for contact `661` after refresh or targeted correction.
- For a designer contact linked to a deal, priority selection is verified and not blamed for the missing deals.
- Local analytics still counts each deal only once.
- No Bitrix write methods are added or called.
- No forbidden personal fields are fetched beyond the existing allowlist or exposed in API/UI/logs/report.
- Relevant backend tests pass.
- If frontend or operator-visible behavior changes, relevant frontend/build/operator checks are run and reported.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-09 Fix contact-deal link completeness
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

Run Compose smoke checks if runtime/operator flow changes:

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

If this search returns only existing negative tests, state that in `.ai/report.md`.

If any live Bitrix diagnostic is run, it must be targeted and read-only. Record method names and aggregate counts only. Do not include secrets or raw private rows in `.ai/report.md`.

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
- the investigation identifies whether the mismatch is caused by missing raw deals, missing raw links, parsing, normalization, or Bitrix relation semantics;
- `.ai/report.md` is updated with root cause and verification results;
- every required check is either run and reported, or explicitly documented as not run with reason;
- `.ai/report.md` explicitly states whether any live Bitrix call was or was not run;
- `.ai/report.md` explicitly states that no Bitrix write methods were added or called;
- staged files are only files intentionally changed for `TASK-2026-06-22-09` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
