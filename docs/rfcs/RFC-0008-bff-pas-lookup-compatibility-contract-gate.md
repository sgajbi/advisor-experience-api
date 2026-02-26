# RFC-0008: lotus-gateway lotus-core Lookup Compatibility Contract Gate

- Status: IMPLEMENTED
- Date: 2026-02-23
- Owner: lotus-gateway

## Context

lotus-gateway lookup endpoints now delegate to lotus-core canonical `/lookups/*` APIs. If lotus-core payload shape drifts (for example invalid `id`/`label` types), UI selectors can fail silently unless lotus-gateway validates and gates this contract.

## Decision

- Add contract tests for lotus-gateway lookup endpoints:
  - `tests/contract/test_lookup_contract.py`
- Validate passthrough contract shape for:
  - `/api/v1/lookups/portfolios`
  - `/api/v1/lookups/instruments`
  - `/api/v1/lookups/currencies`
- Harden `IntakeService` lookup mapping to return `502 Bad Gateway` when lotus-core lookup payload fails schema validation.

## Rationale

- Fails fast on upstream contract violations.
- Protects UI from malformed selector payloads.
- Keeps lotus-gateway behavior explicit at integration boundaries.

## Consequences

Positive:
- Clearer observability for contract drift (502 vs latent UI runtime errors).
- Stronger CI signal through existing unit+contract stage.

Trade-offs:
- Stricter compatibility checks may surface integration issues earlier, requiring coordinated lotus-core/lotus-gateway updates.

