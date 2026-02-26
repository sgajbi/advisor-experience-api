# RFC-0007: BFF Lookup Delegation to PAS Canonical Lookup APIs

- Status: IMPLEMENTED
- Date: 2026-02-23
- Owner: lotus-gateway

## Context

Initial BFF intake implementation translated PAS reference APIs (`/portfolios`, `/instruments`) into lookup contracts and derived currency lists inside BFF. PAS now provides canonical lookup endpoints.

## Decision

Refactor BFF lookup paths to call PAS lookup APIs directly:

- `GET /api/v1/lookups/portfolios` -> PAS `GET /lookups/portfolios`
- `GET /api/v1/lookups/instruments` -> PAS `GET /lookups/instruments`
- `GET /api/v1/lookups/currencies` -> PAS `GET /lookups/currencies`

BFF now preserves the PAS `items` list shape and only wraps with BFF envelope metadata (`correlation_id`, `contract_version`).

## Rationale

- Reduces mapping/derivation logic in BFF.
- Keeps lookup vocabulary ownership in PAS.
- Improves consistency between PAS and BFF selector catalogs.

## Consequences

Positive:
- Lower BFF complexity and lower risk of lookup drift.
- Clearer backend boundary (PAS owns reference catalog semantics).

Trade-offs:
- BFF depends on PAS lookup endpoint availability and contract stability.

## Follow-ups

- Add PAS lookup contract smoke checks to BFF live E2E suite.

