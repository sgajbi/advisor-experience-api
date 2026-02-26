# RFC-0008: BFF PAS Lookup Compatibility Contract Gate

- Status: IMPLEMENTED
- Date: 2026-02-23
- Owner: lotus-gateway

## Context

BFF lookup endpoints now delegate to PAS canonical `/lookups/*` APIs. If PAS payload shape drifts (for example invalid `id`/`label` types), UI selectors can fail silently unless BFF validates and gates this contract.

## Decision

- Add contract tests for BFF lookup endpoints:
  - `tests/contract/test_lookup_contract.py`
- Validate passthrough contract shape for:
  - `/api/v1/lookups/portfolios`
  - `/api/v1/lookups/instruments`
  - `/api/v1/lookups/currencies`
- Harden `IntakeService` lookup mapping to return `502 Bad Gateway` when PAS lookup payload fails schema validation.

## Rationale

- Fails fast on upstream contract violations.
- Protects UI from malformed selector payloads.
- Keeps BFF behavior explicit at integration boundaries.

## Consequences

Positive:
- Clearer observability for contract drift (502 vs latent UI runtime errors).
- Stronger CI signal through existing unit+contract stage.

Trade-offs:
- Stricter compatibility checks may surface integration issues earlier, requiring coordinated PAS/BFF updates.

