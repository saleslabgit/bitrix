# Task: TASK-2026-06-21-08

Status: planned
Created from commit: 0a479a7431be7fc89237b0671038447652175272

## Title

Implement local analytics engine and report API milestone

## Goal

Build the next backend milestone on top of the local synthetic pipeline from TASK-07: implement local analytics calculations over normalized DuckDB data and expose them through typed read API endpoints.

This task should move the project from normalized local data to usable analytical outputs for the MVP, still without real Bitrix integration, without NBRB external calls, without frontend implementation, and without authentication.

## Facts

- `TASK-2026-06-21-07` implemented local synthetic raw loading, normalization, pipeline status, and minimal read API endpoints.
- Current normalized tables are `normalized_contacts` and `normalized_deals`.
- Current local status table is `local_dataset_status`.
- Current synthetic dataset includes 10 contacts, 30 deals, won/open/lost statuses, several currencies, multi-contact deal, deal without contact, equal type priorities, old high-value contact scenario, single-won-deal contact, and long-open deal.
- Current currency rates are synthetic local records in `currency_rates`.
- `SPEC.md` requires revenue to be counted only from won deals.
- `SPEC.md` requires estimated profit to always be `revenue_usd * 0.50`.
- `SPEC.md` requires all financial analytics to be normalized to USD.
- `SPEC.md` requires periods and reports to be calculated from local data, not by querying Bitrix.
- `SPEC.md` requires one analytical contact per deal for contact analytics.
- `SPEC.md` requires ABC, ABC comparison for full period vs last 12 months, RFM, reactivation, type/region analytics, deal cycle, stale open deals, and concentration analytics in MVP.
- `ui-kits/` now exists and contains the design system for future frontend work. It is not a ready interface and is not in scope for this backend task.

## Assumptions

- The synthetic fixture remains the source of truth for this milestone.
- It is acceptable to implement analytics as service/query modules backed by DuckDB before final production repository abstractions exist.
- It is acceptable to use synthetic local currency rates for USD conversion tests, but not to call NBRB yet.
- It is acceptable to expose compact API shapes that are useful for future frontend screens and can evolve later.
- It is acceptable to calculate analytics on demand from normalized local tables rather than persisting all report output tables in this milestone.
- If an endpoint needs data and the local synthetic pipeline has not run yet, either return an empty typed response or run no implicit sync. Do not silently call Bitrix or external APIs.

## Unknowns

- Actual Bitrix webhook URL and access method.
- Actual Bitrix custom field code for contact type.
- Actual production contact type values, priorities, and region mapping.
- Actual production pipelines, stages, and currencies in Bitrix.
- Final production storage layout, migration strategy, dataset activation mechanics, and Parquet snapshot format.
- Final frontend screen composition and exact response-shape needs.

## Scope

Implement this as one coherent backend analytics milestone. Keep modules small and explicit. Do not start frontend implementation.

### 1. Add Currency Conversion Helpers

Add local analytics helpers that convert deal amounts to USD using local `currency_rates`.

Minimum behavior:

- convert `amount_original` to `amount_usd` using `currency_rates`;
- use the rate for the deal close date when available, otherwise created date for open deals;
- use the latest available rate on or before the target date where practical;
- treat USD as USD via the local rate formula, not via a hardcoded production shortcut unless tests justify it;
- keep all conversion deterministic on the synthetic dataset;
- do not call NBRB or any external API.

Expected formula for local rates:

```text
amount_usd = amount_original * source_rate_byn / usd_rate_byn
```

### 2. Add Contact Analytics

Add an analytics module for contact-level metrics over normalized deals.

Minimum metrics per contact/report row:

- `contact_id` and `contact_name`;
- normalized contact type and region;
- total deals count;
- won/open/lost deals count;
- won revenue in USD;
- estimated profit in USD as `revenue_usd * 0.50`;
- first won date and last won date where available;
- last activity date based on latest deal created/closed date where practical;
- `has_sales` or equivalent flag for contacts with won revenue.

Period filters must apply to local data only. Revenue must count only won deals.

### 3. Add ABC Analysis

Implement ABC classification for contacts based on won revenue in USD.

Minimum behavior:

- classify contacts with no won revenue as `Нет продаж`;
- sort revenue contributors deterministically;
- classify cumulative revenue up to 80% as `A`, up to 95% as `B`, remaining revenue as `C`;
- expose both full-period ABC and last-12-month ABC;
- expose a comparison/migration output per contact, for example `abc_full`, `abc_12m`, and `abc_change` or equivalent.

Use the synthetic fixture dates to make last-12-month behavior deterministic. If the calculation needs an anchor date, use either the max local deal date or an explicit parameter, and document the choice.

### 4. Add RFM And Reactivation Signals

Implement a first local RFM calculation on won deals.

Minimum behavior:

- recency from latest won closed date;
- frequency from won deal count;
- monetary from won revenue USD;
- deterministic 1-5 style scores or clearly documented segment buckets;
- segment output usable by frontend later;
- contacts with no won deals handled explicitly.

Add a reactivation signal for contacts whose last won deal is old enough and who have earlier sales history. Use a documented threshold constant if `SPEC.md` does not define the exact threshold in current docs.

### 5. Add Deal Cycle And Stale Open Deals

Implement local deal lifecycle analytics.

Minimum behavior:

- deal cycle duration for won/lost deals using created and closed timestamps;
- aggregate cycle metrics by contact type and/or region where practical;
- stale open deal detection based on open deal age;
- long-open synthetic deal must be detected by tests;
- deals without analytical contact remain represented as `Без контакта` / `Не определено` where relevant.

### 6. Add Concentration And Type/Region Analytics

Implement local aggregate outputs needed by the MVP.

Minimum behavior:

- revenue concentration: top contacts share of won revenue, including at least top 1 / top 3 / top 5 or a similarly useful compact output;
- type analytics: revenue, profit, contact count, deal counts by normalized contact type;
- region analytics: revenue, profit, contact count, deal counts by normalized region;
- all financial fields in USD;
- no forbidden personal fields in outputs.

### 7. Add API Endpoints

Expose typed read-only FastAPI endpoints for the new analytics.

Suggested endpoints, adjust names only if a cleaner local pattern emerges:

- `GET /api/reports/contacts/analytics`;
- `GET /api/reports/abc`;
- `GET /api/reports/rfm`;
- `GET /api/reports/stale-deals`;
- `GET /api/reports/deal-cycle`;
- `GET /api/reports/concentration`;
- `GET /api/reports/type-region`.

Requirements:

- endpoints use local DuckDB data only;
- no Bitrix calls;
- no NBRB calls;
- response models are Pydantic typed;
- period parameters are supported where meaningful;
- responses do not expose forbidden fields;
- existing TASK-07 endpoints continue to work.

### 8. Tests

Add focused storage-backed tests for the analytics milestone.

Minimum coverage:

- USD conversion works for USD, EUR, and BYN synthetic deals using local rates;
- revenue counts only won deals;
- estimated profit equals `revenue_usd * 0.50`;
- contact analytics returns expected rows/counts and handles no-sales contacts;
- ABC boundaries at 80% and 95% are covered;
- `Нет продаж` is assigned for contacts without won revenue;
- full-period vs last-12-month ABC comparison is deterministic;
- RFM handles high-value old contact, recent sales, single-won-deal contact, and no-sales contact;
- stale open deal test detects the long-open synthetic deal;
- deal cycle metrics calculate durations from local timestamps;
- concentration output is deterministic;
- type/region aggregates use normalized values and `Не определено` fallback;
- API endpoints return typed local data without forbidden fields;
- existing tests continue to pass.

### 9. Documentation

Update documentation concisely:

- `docs/data-model.md` — document analytics calculations and report outputs added in this task;
- `docs/project-status.md` — update current phase, done/not done, and next likely milestone;
- `docs/testing.md` — add analytics test coverage and expected command;
- `docs/development.md` or `backend/README.md` — document local analytics endpoints;
- `.ai/report.md` — full implementation report with changed files, checks, facts, assumptions, unknowns, and next step.

Also mention that `ui-kits/` is the future frontend design-system source, but do not implement frontend work in this task.

## Out Of Scope

- Real Bitrix integration.
- Bitrix API clients, real webhook calls, pagination, retries, or field allowlist discovery.
- NBRB API integration or external currency calls.
- Parquet snapshot writing.
- Production dataset activation/swap mechanics.
- Frontend implementation.
- Copying, changing, or restructuring `ui-kits/`.
- Authentication implementation.
- CI/GitHub Actions setup.
- Production deployment, HTTPS, backups.
- Complex BI constructor or arbitrary report builder.
- Machine learning or forecasting.

## Constraints

- Follow `AGENTS.md`, `WORKFLOW.md`, and `SPEC.md`.
- Keep all data synthetic and local.
- Do not query Bitrix or external APIs.
- Do not invent real Bitrix field codes or present synthetic values as production config.
- Do not add forbidden personal fields anywhere in schema, fixtures, API responses, docs, logs, or tests.
- Do not commit local DuckDB database files, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, generated artifacts, raw data, or secrets.
- Do not implement frontend screens in this task.
- Do not modify `ui-kits/` unless a documentation-only reference is absolutely necessary.
- Prefer explicit analytics code and focused tests over broad abstractions.

## Acceptance Criteria

- Local USD conversion works from synthetic `currency_rates` without external calls.
- Contact analytics calculates won revenue USD, profit USD, counts, and dates correctly.
- Revenue and profit include only won deals.
- ABC full-period and last-12-month classifications are implemented and tested.
- Contacts without won sales are classified as `Нет продаж` or equivalent documented no-sales state.
- RFM and reactivation signals are implemented and tested on synthetic edge cases.
- Deal cycle and stale open deal analytics are implemented and tested.
- Concentration, type analytics, and region analytics are implemented and tested.
- New API endpoints return typed local analytics data and no forbidden fields.
- Existing TASK-07 pipeline/API tests continue to pass.
- Documentation and `.ai/report.md` reflect the new analytics milestone and note `ui-kits/` as future frontend design-system input.
- No real secrets, raw data, databases, Parquet snapshots, CSV exports, dependency folders, virtual environments, caches, generated artifacts, or frontend builds are committed.
- The implementation commit uses the required prefix:

```text
codex: TASK-2026-06-21-08 Implement local analytics engine and report API milestone
```

## Checks

Run from `backend/` in the configured dev environment:

```bash
python -m pytest
```

If dependencies are not installed in the current environment, install the backend dev package first:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Run syntax/import-level checks if useful:

```bash
python -m py_compile app/*.py app/**/*.py tests/*.py tests/**/*.py
```

Run from repository root:

```bash
docker compose config
```

Before committing:

```bash
git status --short
git diff --stat HEAD
```

If any check cannot be run, document the exact reason in `.ai/report.md`.

## Notes

Before starting implementation, Codex must run:

```bash
git log --oneline -5
git status --short
```

Codex must stop if the latest relevant commit is not a planner commit for this task.

After implementation, Codex must update `.ai/report.md`, stage only files related to this task and `.ai/report.md`, and avoid `git add .` unless explicitly allowed by the user.
