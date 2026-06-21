# Architecture

## Target Flow

```text
Bitrix CRM -> read-only extraction -> raw local layer -> normalization -> analytics tables -> backend API -> web interface
```

## Layers

### Bitrix Read-Only Extraction

Bitrix is used only as a read-only source. Future sync code must request an explicit allowlist of fields and must not use `select: ["*"]`. The MVP must not download phones, emails, addresses, messengers, requisites, comments, files, activity fields, or arbitrary non-allowlisted fields.

### Raw Local Layer

Stores data in the form received from Bitrix for allowed entities only: contacts, deals, deal-contact links, and required stage dictionaries. Raw exports and local data files must not be committed.

### Normalization

Transforms Bitrix identifiers, stage semantics, contact type mapping, region mapping, deal-contact selection, timestamps, and currencies into stable local representations. Contact type priorities and region rules are configuration or data, not hardcoded business constants.

### Analytics Tables

Stores reproducible outputs for reports: revenue, estimated profit, ABC, RFM, reactivation, type and region aggregates, deal-cycle metrics, stale deals, and concentration. Revenue and ABC/RFM are based only on won deals.

### Backend API

FastAPI exposes health, sync, metadata, and report endpoints. Only `GET /health` exists in the current scaffold.

### Web Interface

The frontend will consume the backend API after the design system is approved. It must follow `SPEC.md` and must not query Bitrix directly.

## Current Implementation

The repository currently contains a minimal backend package:

- `backend/app/main.py` creates the FastAPI app and `/health`.
- `backend/app/core/config.py` defines environment-based settings.
- `backend/tests/test_health.py` verifies the health endpoint.

No business data modules are implemented yet.
