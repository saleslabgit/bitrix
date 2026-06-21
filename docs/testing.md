# Testing

## Current Checks

The current scaffold has backend tests for the health endpoint, analytical contact selection, DuckDB schema initialization, and the synthetic integration fixture:

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

The current synthetic fixture covers the minimum integration shape. Future tests should reuse it for normalization, storage-backed pipeline checks, and analytics once those layers exist.
