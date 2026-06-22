# Task: TASK-2026-06-22-11

Status: planned
Created from: current `main` after `9344093 codex: TASK-2026-06-22-10 Reconcile contact 661 explicit deal IDs`

## Title

Test `crm.item.list` as the fast deal-contact link source

## Goal

Determine whether Bitrix universal CRM methods can provide complete deal-contact links fast enough for normal manual refresh, without doing `crm.deal.contact.items.get` once per deal.

The immediate decision point is the known `contact_id=661` case. Bitrix shows these seven deals for contact `661`:

```text
123
343
1239
14773
19149
23989
24761
```

`TASK-2026-06-22-10` proved that deals `123`, `343`, and `1239` were missed by the normal sync because `crm.deal.list` row fields did not include the secondary relation to contact `661`, while `crm.deal.contact.items.get` did confirm the relation.

This task must run a bounded read-only `crm.item.list` test for these exact deal IDs, decide whether it returns a complete contact list for deals, and implement the fastest safe normal-refresh path if the test proves it.

## Official API Facts To Verify Against

Use official Bitrix REST documentation as the source for API behavior.

Known documented facts:

- `crm.deal.list` is deprecated and its development is halted; Bitrix says to use `crm.item.list`.
- `crm.deal.list` does not support `CONTACT_IDS`; Bitrix says to use `crm.item.list` for deals with a contact list and for contact filtering.
- `crm.item.list` is read-only for users with read permission and uses `entityTypeId=2` for deals.
- `crm.item.list` must use explicit safe `select`; do not use `select: ["*"]` because `*` can return `fm` multiple fields such as phones, e-mail, and messengers.
- Available item fields should be discovered with `crm.item.fields` for `entityTypeId=2`.
- `batch` supports up to 50 sub-requests and is only a fallback, not the preferred normal sync path.

## Facts

- Bitrix is read-only.
- CRM write methods remain forbidden:
  - `crm.*.add`
  - `crm.*.update`
  - `crm.*.delete`
  - `crm.*.set`
- Main analytics entity is the contact.
- A deal is counted once by selecting one analytical contact from all loaded deal-contact links.
- Contact `661` has designer type `[61]`, normalized type `Дизайнер`, region `Беларусь`, priority `1`.
- Priority is not the root cause of the `661` mismatch.
- Normal manual sync currently builds links from deal row fields such as `CONTACT_ID` and `CONTACT_IDS` returned by `crm.deal.list`.
- Normal manual sync must not call `crm.deal.contact.items.get` once per deal.
- `TASK-2026-06-22-10` added a bounded explicit reconciliation helper, but it is not a scalable normal-refresh solution.

## Assumptions

- `crm.item.list` for deals may expose a field such as `contactIds` that contains the full list of contacts linked to each deal.
- If `crm.item.list` returns complete contact IDs for the seven known deals, it should be used for normal deal extraction/link extraction instead of `crm.deal.list`.
- If `crm.item.list` does not return complete contact IDs on this portal, the scalable alternative may be a separate explicit/deep relation sync using `batch`, not a per-deal HTTP loop in the normal refresh.

## Unknowns

- The exact field names returned by `crm.item.fields` for deal contacts on this Bitrix portal.
- Whether `crm.item.list` can select and return the complete deal contact list for deals `123`, `343`, and `1239`.
- Whether `crm.item.list` supports safe filtering by explicit deal IDs on this portal.
- Whether switching normal sync to `crm.item.list` requires field-name mapping changes for current raw deal transformation.

## Scope

### 1. Add safe Bitrix universal item client support

Add read-only support for:

```text
crm.item.fields
crm.item.list
```

Only for explicit read-only use. Keep the method allowlist strict.

For `crm.item.fields`, call it with:

```json
{"entityTypeId": 2}
```

For `crm.item.list`, use:

```json
{"entityTypeId": 2, "select": [...], "filter": {...}, "order": {...}}
```

Do not add `crm.item.add`, `crm.item.update`, `crm.item.delete`, or any other write-capable method.

### 2. Discover the safe deal item field set

Implement a helper that inspects `crm.item.fields` for `entityTypeId=2` and determines the available safe deal fields needed for the current raw model and links.

Minimum desired deal data fields, using the actual supported names from `crm.item.fields`:

- deal ID;
- title/name;
- amount/opportunity;
- currency;
- created time;
- closed time;
- stage;
- category;
- primary contact if available;
- full contact ID list if available.

Hard safety rules:

- never request `*`;
- never request `fm`;
- never request phones, email, addresses, messengers, comments, files, requisites, activities, or arbitrary non-allowlisted custom fields;
- if a field is not known safe, do not select it.

### 3. Run the bounded live `crm.item.list` test

Add an explicitly invoked backend diagnostic or script/helper, then run it if live Bitrix credentials are available in the execution environment.

The test must be bounded to exactly these deal IDs:

```text
123, 343, 1239, 14773, 19149, 23989, 24761
```

It must call only read-only methods:

```text
crm.item.fields
crm.item.list
```

It must report only safe ID-level facts in `.ai/report.md`:

- method names used;
- selected safe field names;
- whether all seven deal IDs were returned;
- for each deal ID, the returned linked contact IDs;
- whether contact `661` is present;
- whether `crm.item.list` agrees with the `TASK-10` `crm.deal.contact.items.get` result;
- whether `crm.item.list` is sufficient for normal refresh.

Do not include raw Bitrix payloads, webhook values, secrets, personal fields, contact names, comments, files, local paths, or generated data contents.

If live Bitrix credentials are not available, commit the code/tests/report as `blocked` or `partial` with the exact reason. Do not fake the result.

### 4. Decide and implement the normal refresh path

If the bounded live test proves that `crm.item.list` returns the complete contact ID list for all seven known deals, update normal manual Bitrix deal ingestion to use `crm.item.list` for deal rows and deal-contact link extraction.

Requirements for the switched path:

- preserve current raw deal columns and semantics;
- extract all contact links from the complete item contact list;
- preserve primary-contact information when available;
- keep `raw_deal_contact_links` uniqueness by `deal_id + contact_id`;
- keep one analytical contact per deal through existing normalization rules;
- ensure contact `661` would naturally get all seven supplied deals after a normal refresh, without explicit reconciliation;
- keep Docker Compose startup unchanged: no automatic Bitrix refresh;
- keep UI refresh manual via existing operator action.

If `crm.item.list` does not return complete contact IDs or cannot safely expose the needed field, do not switch normal sync. Instead, document the fastest safe fallback design in `.ai/report.md`: a separate explicit/deep relation sync using Bitrix `batch` with up to 50 `crm.deal.contact.items.get` sub-requests per HTTP call, guarded by progress/status and not run automatically.

### 5. Tests

Add focused backend tests for:

- `crm.item.fields` and `crm.item.list` are allowed read-only methods;
- CRM write methods remain rejected/not introduced;
- `crm.item.list` request uses explicit safe select and never `*` or `fm`;
- explicit-ID `crm.item.list` diagnostic is bounded to the supplied deal IDs;
- transform/parsing supports Bitrix item field casing used by `crm.item.list`;
- multi-contact deal links from the item contact list are not lost;
- designer priority `1` still wins when a deal has primary lower-priority contact plus designer `661` as secondary;
- analytics count matches normalized/link facts in a scenario equivalent to the seven supplied deal IDs;
- forbidden personal fields are not returned/logged by diagnostics.

### 6. Documentation/report

Update `.ai/report.md` with:

- the exact `crm.item.fields` contact-related field names discovered;
- the exact bounded `crm.item.list` result for the seven deal IDs, as safe ID-level facts only;
- the decision: switch normal sync to `crm.item.list`, or do not switch and use fallback design;
- if switched, changed files and how normal refresh now builds complete links;
- if not switched, why the test failed or was unavailable;
- all checks run;
- confirmation that no write methods were added or called.

Update `docs/development.md` and `docs/data-model.md` if normal sync behavior changes.

## Out Of Scope

- New frontend screens or UI redesign.
- Automatic background refresh or scheduled sync.
- Broad unbounded per-deal `crm.deal.contact.items.get` scan in normal refresh.
- Companies, leads, products, calls, emails, comments, activities, files, requisites.
- Any Bitrix write operation.
- Exporting raw Bitrix data.
- Changing contact type priority rules.
- Changing analytics formulas, revenue, profit, ABC, or RFM semantics.
- Modifying `ui-kits/`.

## Constraints

- Bitrix remains read-only.
- Do not add or call methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not use `select: ["*"]`.
- Do not request or expose `fm`, phones, emails, addresses, messengers, comments, files, requisites, activities, or arbitrary non-allowlisted custom fields.
- Do not print webhook URLs or tokens.
- Do not commit `.env`, local databases, Parquet snapshots, raw exports, logs, caches, build artifacts, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Do not make Docker Compose auto-refresh Bitrix data.
- Keep the live test bounded to the seven supplied deal IDs.
- If a broad relation-refresh design is needed, document it but do not run it in this task.

## Acceptance Criteria

- `.ai/report.md` states whether `crm.item.list` returned complete contact IDs for deals `123`, `343`, `1239`, `14773`, `19149`, `23989`, and `24761`.
- `.ai/report.md` states whether contact `661` was present for each of those seven deals in the `crm.item.list` result.
- The decision is explicit: normal sync switched to `crm.item.list`, or normal sync not switched with a clear reason.
- If switched, a normal refresh path no longer relies on `crm.deal.list CONTACT_IDS` for complete deal-contact links.
- If switched, backend tests prove multi-contact links are preserved and designer `661` wins over lower-priority primary contacts.
- If not switched, no risky partial implementation is left behind; fallback is documented as a separate future operator/deep-sync path.
- Diagnostics and reports expose only safe ID-level facts.
- No Bitrix write methods are added or called.
- No forbidden personal fields are selected, stored, logged, returned, or documented.
- Relevant backend tests pass.
- Frontend build is run only if frontend code changes.
- The implementation commit uses the exact required message:

```text
codex: TASK-2026-06-22-11 Test crm.item.list deal contact links
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
- official Bitrix docs were checked for `crm.deal.list`, `crm.item.fields`, `crm.item.list`, and `batch` constraints;
- the `crm.item.list` live test was either run for exactly the seven supplied deal IDs or explicitly reported as unavailable with reason;
- if the live test was run, `.ai/report.md` includes only safe ID-level results;
- if normal sync is switched, backend tests cover multi-contact link completeness and designer priority for a secondary contact;
- if normal sync is not switched, no incomplete normal-sync migration remains in the code;
- every required check is either run and reported, or explicitly documented as not run with reason;
- `.ai/report.md` explicitly states whether any live Bitrix call was or was not run;
- `.ai/report.md` explicitly states that no Bitrix write methods were added or called;
- staged files are only files intentionally changed for `TASK-2026-06-22-11` plus `.ai/report.md`;
- `.env`, generated data, DuckDB files, Parquet snapshots, CSV exports, logs, caches, `node_modules`, `frontend/dist`, and `ui-kits/` are not staged;
- `.ai/task.md` is not staged by Codex unless the user explicitly requested changing the task;
- the final commit message exactly matches the required `codex:` message above.

If any condition is not true, stop and report the blocker instead of committing.
