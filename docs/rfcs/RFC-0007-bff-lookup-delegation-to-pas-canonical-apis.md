# RFC-0007: lotus-gateway Lookup Delegation to lotus-core Canonical Lookup APIs

- Status: IMPLEMENTED
- Date: 2026-02-23
- Owner: lotus-gateway

## Context

Initial lotus-gateway intake implementation translated lotus-core reference APIs (`/portfolios`, `/instruments`) into lookup contracts and derived currency lists inside lotus-gateway. lotus-core now provides canonical lookup endpoints.

## Decision

Refactor lotus-gateway lookup paths to call lotus-core lookup APIs directly:

- `GET /api/v1/lookups/portfolios` -> lotus-core `GET /lookups/portfolios`
- `GET /api/v1/lookups/instruments` -> lotus-core `GET /lookups/instruments`
- `GET /api/v1/lookups/currencies` -> lotus-core `GET /lookups/currencies`

lotus-gateway now preserves the lotus-core `items` list shape and only wraps with lotus-gateway envelope metadata (`correlation_id`, `contract_version`).

## Rationale

- Reduces mapping/derivation logic in lotus-gateway.
- Keeps lookup vocabulary ownership in lotus-core.
- Improves consistency between lotus-core and lotus-gateway selector catalogs.

## Consequences

Positive:
- Lower lotus-gateway complexity and lower risk of lookup drift.
- Clearer backend boundary (lotus-core owns reference catalog semantics).

Trade-offs:
- lotus-gateway depends on lotus-core lookup endpoint availability and contract stability.

## Follow-ups

- Add lotus-core lookup contract smoke checks to lotus-gateway live E2E suite.

