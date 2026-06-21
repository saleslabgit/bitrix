# Testing

## Current Checks

The current scaffold has backend tests for the health endpoint and analytical contact selection:

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

Integration fixtures must later cover contacts, deals, currencies, multiple contact links, equal priorities, missing contacts, old A-segment contacts without recent sales, one-deal contacts, and long-open deals. The fixture plan is documented in `docs/fixtures.md`.
