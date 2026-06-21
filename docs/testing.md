# Testing

## Current Checks

The current backend tests cover the health endpoint, analytical contact selection, DuckDB schema initialization, synthetic fixture, local normalization pipeline, local analytics calculations, local read API, and the mocked read-only Bitrix boundary:

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

Current analytics coverage verifies:

- USD conversion for USD, EUR, and BYN using only local synthetic `currency_rates`;
- latest-rate selection on or before the deal target date;
- won-only revenue and estimated profit as `revenue_usd * 0.50`;
- contact analytics counts, dates, no-sales handling, and sales flags;
- ABC 80% and 95% boundaries, `Нет продаж`, and deterministic full-period vs last-12-month comparison;
- RFM old high-value, recent, single-won-deal, and no-sales cases;
- reactivation signal for old repeat buyers;
- stale open deal detection for the long-open synthetic deal;
- deal-cycle duration aggregates;
- deterministic concentration output;
- type, region, and fallback aggregate rows.

Current report API coverage verifies the local analytics endpoints by calling endpoint functions directly:

```text
GET /api/reports/contacts/analytics
GET /api/reports/abc
GET /api/reports/rfm
GET /api/reports/stale-deals
GET /api/reports/deal-cycle
GET /api/reports/concentration
GET /api/reports/type-region
GET /api/reports/types-regions
```

Current Bitrix boundary coverage uses mocked responses only. It verifies:

- Bitrix settings can be absent without breaking tests;
- read-only client allowlists methods and rejects write methods;
- pagination works for list methods;
- API errors do not expose webhook secrets;
- contact/deal select fields never use `*` and exclude forbidden field names;
- configured contact type field is included only when explicitly configured;
- forbidden configured contact type fields are rejected;
- discovery reports present and missing contact type fields;
- forbidden fields in mocked payloads are ignored during storage;
- manual ingestion loads contacts, deals, deal-contact links, and stages idempotently;
- existing normalization runs after mocked Bitrix raw loading;
- `GET /api/bitrix/discovery`, `POST /api/bitrix/sync/run`, and `GET /api/bitrix/sync/status` fail safely without live credentials.

Docker Compose configuration can be validated from the repository root:

```bash
docker compose config
```

## Future Required Test Areas

According to `SPEC.md`, backend test coverage must later include production-oriented areas that are still outside the local synthetic milestone:

- historical rate selection;
- live Bitrix smoke checks with a read-only credential, kept outside the regular test suite;
- NBRB integration and missing-rate failure behavior;
- production dataset activation/swap mechanics;
- persisted analytics tables if they are added later;
- authentication once implemented.

The current synthetic fixture covers the minimum integration shape and is reused by the local storage-backed pipeline and analytics tests.
