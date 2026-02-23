# RFC-0006: PAS Intake and Lookup Pass-Through in BFF

- Status: IMPLEMENTED
- Date: 2026-02-23
- Owner: advisor-experience-api

## Context

Advisor Workbench intake screens call BFF routes for PAS ingestion and selector lookups, but BFF only exposed proposal and capability aggregation endpoints. This left intake UX dependent on non-existent BFF APIs and prevented PAS-backed onboarding from becoming a real integrated flow.

## Decision

Add first-class BFF passthrough APIs for PAS ingestion and lookup catalogs:

- `POST /api/v1/intake/portfolio-bundle` -> PAS ingestion `/ingest/portfolio-bundle`
- `POST /api/v1/intake/uploads/preview` -> PAS ingestion `/ingest/uploads/preview`
- `POST /api/v1/intake/uploads/commit` -> PAS ingestion `/ingest/uploads/commit`
- `GET /api/v1/lookups/portfolios` -> PAS query `/portfolios`
- `GET /api/v1/lookups/instruments` -> PAS query `/instruments`
- `GET /api/v1/lookups/currencies` -> derived from PAS portfolio base currencies + instrument currencies

Implementation details:
- Introduce `PasIngestionClient` and extend `PasClient` for lookup sources.
- Add `IntakeService` for envelope shaping and upstream error handling parity.
- Add `portfolio_data_ingestion_base_url` config (default `http://localhost:8200`).

## Rationale

- Keeps domain logic in PAS while BFF orchestrates and shapes contracts for UI.
- Removes dead/missing endpoints and makes intake calls production-realistic.
- Establishes a single BFF contract layer for UI selector catalogs.

## Consequences

Positive:
- UI intake APIs now map to live backend services.
- Upload preview/commit workflows can be consumed by UI without direct PAS coupling.

Trade-offs:
- BFF now depends on both PAS query and PAS ingestion service base URLs.
- Currency lookups are currently derived heuristically from existing PAS reference data.

## Follow-ups

- Add PAS-native lookup endpoint(s) for canonical currency catalogs to replace derivation.
- Add a live multi-service E2E for intake->lookup visibility once PAS persistence/event timing is stabilized in CI.
