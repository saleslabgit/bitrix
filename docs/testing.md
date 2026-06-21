# Testing

## Current Checks

The current scaffold has one backend test for the health endpoint:

```bash
cd backend
pytest
```

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

Integration fixtures must later cover contacts, deals, currencies, multiple contact links, equal priorities, missing contacts, old A-segment contacts without recent sales, one-deal contacts, and long-open deals.
