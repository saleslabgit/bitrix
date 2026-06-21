# Testing

## Current Checks

The current scaffold has backend tests for the health endpoint, analytical contact selection, DuckDB schema initialization, synthetic fixture, local normalization pipeline, and local read API:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

Current domain test coverage includes:

- best configured contact type priority wins;
- `is_primary` breaks equal priority ties;
- minimum `contact_id` breaks remaining ties;
- deals without contacts return `None`;
- unknown or missing contact type uses a neutral fallback without hardcoded business-specific type values.

Current health endpoint coverage avoids `fastapi.testclient.TestClient` because it hangs in the current WSL temporary dependency target. It verifies that `GET /health` is registered and that the endpoint function returns the expected payload.

Current storage schema coverage verifies:

- `initialize_schema()` runs on an in-memory DuckDB connection;
- all expected MVP scaffold tables are created;
- expected columns exist;
- forbidden personal/out-of-scope field names are absent;
- schema initialization is idempotent.

Current fixture coverage verifies that `backend/tests/fixtures/synthetic_dataset.py` includes the required synthetic shape: contacts, deals, currencies, won/open/lost statuses, multiple contacts on one deal, equal type priorities, one deal without a contact, an old high-value contact scenario, a single-won-deal contact, and a long-open deal.

Current pipeline coverage verifies:

- synthetic raw data loads into DuckDB idempotently;
- normalized contacts include active type/region mappings and `Не определено` fallbacks;
- normalized deals contain exactly one row per deal;
- multi-contact deal assignment follows priority/primary/id rules;
- deal without contact is preserved as `Без контакта`;
- won/open/lost statuses are represented.

Current API coverage calls endpoint functions directly instead of `fastapi.testclient.TestClient`, because the earlier health task documented hangs in this environment. It verifies local synthetic status, filters, contact summaries, and absence of forbidden field names in responses.

Docker Compose configuration can be validated from the repository root:

```bash
docker compose config
```

## Future Required Test Areas

According to `SPEC.md`, backend test coverage must later include:

- analytical contact selection for a deal;
- equal contact type priorities;
- deals without contacts;
- contact type and region normalization;
- deal status derivation;
- currency conversion to USD;
- historical rate selection;
- revenue and estimated profit;
- deal cycle metrics;
- ABC boundaries at 80% and 95%;
- `Нет продаж` status;
- ABC migration;
- RFM scores and segments;
- stale open deals;
- revenue concentration.

The current synthetic fixture covers the minimum integration shape and is reused by the local storage-backed pipeline. Future tests should reuse normalized tables for analytics once those layers exist.
