# RFC-0002: BFF Proposal Workspace v1 (Create/List/Detail/Submit)

- Status: IMPLEMENTED
- Date: 2026-02-22
- Depends on: RFC-0001

## Goal

Extend the DPM-first BFF slice from simulation-only to a minimal end-to-end proposal workspace contract for UI integration.

## Decision

Expose and standardize these BFF endpoints:

- `POST /api/v1/proposals` -> DPM `POST /rebalance/proposals`
- `GET /api/v1/proposals` -> DPM `GET /rebalance/proposals`
- `GET /api/v1/proposals/{proposal_id}` -> DPM `GET /rebalance/proposals/{proposal_id}`
- `POST /api/v1/proposals/{proposal_id}/submit` -> DPM `POST /rebalance/proposals/{proposal_id}/transitions`

Submit mapping in BFF:

- `review_type=RISK` maps to `event_type=SUBMITTED_FOR_RISK_REVIEW`
- `review_type=COMPLIANCE` maps to `event_type=SUBMITTED_FOR_COMPLIANCE_REVIEW`

## Out of Scope

- Full approval workflow and execution orchestration.
- Multi-service aggregation beyond DPM.

## Acceptance Criteria

- Contract and integration tests cover create/list/detail/submit routes.
- `make check` and `make test-integration` pass.
- README endpoint documentation updated in same PR.
