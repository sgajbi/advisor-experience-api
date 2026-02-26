# Enterprise Readiness Baseline (lotus-gateway/lotus-gateway)

- Standard reference: `lotus-platform/Enterprise Readiness Standard.md`
- Scope: lotus-gateway orchestration, API gateway behavior, downstream API integration controls.
- Change control: RFC required for platform rule changes; ADR required for temporary deviations.

## Security and IAM Baseline

- Service-level audit middleware captures privileged write actions (`POST/PUT/PATCH/DELETE`).
- Audit records include actor, tenant, role, and correlation identifiers.
- Sensitive fields are redacted before logging.

Evidence:
- `src/app/enterprise_readiness.py`
- `src/app/main.py`
- `tests/unit/test_enterprise_readiness.py`

## API Governance Baseline

- OpenAPI remains contract-first with versioned service metadata.
- Backward-compatibility and deprecation decisions are governed by RFC workflow.
- Contract and integration tests are part of CI gates.

Evidence:
- `src/app/main.py`
- `tests/contract`
- `tests/integration`

## Configuration and Feature Management Baseline

- Feature flags are centrally loaded from `ENTERPRISE_FEATURE_FLAGS_JSON`.
- Flags support tenant and role scoping with deterministic fallback order.
- Invalid config payload defaults to deny-by-default behavior.

Evidence:
- `src/app/enterprise_readiness.py`
- `tests/unit/test_enterprise_readiness.py`

## Data Quality and Reconciliation Baseline

- Request contract validation uses typed schemas; invalid payloads are rejected.
- Critical write orchestration remains fail-fast on downstream errors.

Evidence:
- `src/app/contracts`
- `src/app/services/proposal_service.py`

## Reliability and Operations Baseline

- Standard resilient HTTP client behavior (timeouts, bounded retries, explicit failures).
- Runbooks and migration/change controls are standardized in shared PPD standards.

Evidence:
- `src/app/clients/http_resilience.py`
- `docs/standards/scalability-availability.md`
- `docs/standards/migration-contract.md`

## Privacy and Compliance Baseline

- Sensitive fields are redacted in audit metadata.
- Correlation IDs and actor context provide audit-trail traceability.

Evidence:
- `src/app/enterprise_readiness.py`
- `tests/unit/test_enterprise_readiness.py`

## Deviations

- Any deviation from the enterprise readiness baseline requires ADR with expiry/review date.


