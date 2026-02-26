# RFC-0006: lotus-core Intake and Lookup Pass-Through in lotus-gateway

- Status: IMPLEMENTED
- Date: 2026-02-23
- Owner: lotus-gateway

## Context

Advisor Workbench intake screens call lotus-gateway routes for lotus-core ingestion and selector lookups, but lotus-gateway only exposed proposal and capability aggregation endpoints. This left intake UX dependent on non-existent lotus-gateway APIs and prevented lotus-core-backed onboarding from becoming a real integrated flow.

## Decision

Add first-class lotus-gateway passthrough APIs for lotus-core ingestion and lookup catalogs:

- `POST /api/v1/intake/portfolio-bundle` -> lotus-core ingestion `/ingest/portfolio-bundle`
- `POST /api/v1/intake/uploads/preview` -> lotus-core ingestion `/ingest/uploads/preview`
- `POST /api/v1/intake/uploads/commit` -> lotus-core ingestion `/ingest/uploads/commit`
- `GET /api/v1/lookups/portfolios` -> lotus-core query `/portfolios`
- `GET /api/v1/lookups/instruments` -> lotus-core query `/instruments`
- `GET /api/v1/lookups/currencies` -> derived from lotus-core portfolio base currencies + instrument currencies

Implementation details:
- Introduce `PasIngestionClient` and extend `PasClient` for lookup sources.
- Add `IntakeService` for envelope shaping and upstream error handling parity.
- Add `portfolio_data_ingestion_base_url` config (default `http://localhost:8200`).

## Rationale

- Keeps domain logic in lotus-core while lotus-gateway orchestrates and shapes contracts for UI.
- Removes dead/missing endpoints and makes intake calls production-realistic.
- Establishes a single lotus-gateway contract layer for UI selector catalogs.

## Consequences

Positive:
- UI intake APIs now map to live backend services.
- Upload preview/commit workflows can be consumed by UI without direct lotus-core coupling.

Trade-offs:
- lotus-gateway now depends on both lotus-core query and lotus-core ingestion service base URLs.
- Currency lookups are currently derived heuristically from existing lotus-core reference data.

## Follow-ups

- Add lotus-core-native lookup endpoint(s) for canonical currency catalogs to replace derivation.
- Add a live multi-service E2E for intake->lookup visibility once lotus-core persistence/event timing is stabilized in CI.

