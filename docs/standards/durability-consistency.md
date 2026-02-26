# Durability and Consistency Standard (lotus-gateway/lotus-gateway)

- Standard reference: `lotus-platform/Durability and Consistency Standard.md`
- Scope: lotus-gateway orchestration and write-through proposal/advisory workflows.
- Change control: RFC required for rule changes; ADR required for temporary deviation.

## Workflow Consistency Classification

- Strong consistency:
  - proposal create/version/submit/approval/consent orchestration
  - write-through lotus-manage workflow invocations
- Eventual consistency:
  - read-side dashboards and analytics composition from lotus-core/lotus-performance/lotus-report

## Idempotency and Retry Semantics

- Critical proposal write APIs accept/propagate `Idempotency-Key`.
- lotus-gateway propagates idempotency to downstream services and preserves replay-safe behavior.
- Evidence:
  - `src/app/routers/proposals.py`
  - `src/app/services/proposal_service.py`
  - `tests/unit/test_proposal_service.py`

## Atomicity Boundaries

- Business write transitions are delegated to authoritative domain services (lotus-manage/lotus-core).
- lotus-gateway orchestration must fail fast on downstream write failure and never mask partial commits.
- Evidence:
  - `src/app/clients/http_resilience.py`
  - `src/app/services/proposal_service.py`

## As-Of and Reproducibility Semantics

- As-of fields from downstream services are preserved without mutation.
- lotus-gateway contract metadata includes deterministic identifiers for traceability.
- Evidence:
  - `src/app/contracts/workbench.py`
  - `src/app/routers/reporting.py`

## Concurrency and Conflict Policy

- Upstream conflict responses (e.g., idempotency hash mismatch or version conflict) are surfaced to callers.
- Retry is bounded and explicit.
- Evidence:
  - `src/app/clients/http_resilience.py`
  - `tests/unit/test_http_resilience.py`

## Integrity Constraints

- Request schema validation is enforced at API boundary via Pydantic models.
- Invalid payloads are rejected; no partial write fallback is allowed.
- Evidence:
  - `src/app/contracts/*.py`
  - `tests/unit/test_intake_service.py`

## Release-Gate Tests

- Unit: `tests/unit/test_proposal_service.py`, `tests/unit/test_http_resilience.py`
- Integration: `tests/integration/*`
- Contract: `tests/contract/*`

## Deviations

- Any deviation from strong-consistency/write idempotency requirements requires ADR with expiry review date.



