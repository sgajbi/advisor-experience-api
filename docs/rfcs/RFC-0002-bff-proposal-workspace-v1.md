# RFC-0002: lotus-gateway Proposal Workspace v1 (Create/List/Detail/Submit)

- Status: IMPLEMENTED
- Date: 2026-02-22
- Depends on: RFC-0001

## Goal

Extend the lotus-manage-first lotus-gateway slice from simulation-only to a minimal end-to-end proposal workspace contract for UI integration.

## Decision

Expose and standardize these lotus-gateway endpoints:

- `POST /api/v1/proposals` -> lotus-manage `POST /rebalance/proposals`
- `GET /api/v1/proposals` -> lotus-manage `GET /rebalance/proposals`
- `GET /api/v1/proposals/{proposal_id}` -> lotus-manage `GET /rebalance/proposals/{proposal_id}`
- `POST /api/v1/proposals/{proposal_id}/submit` -> lotus-manage `POST /rebalance/proposals/{proposal_id}/transitions`

Submit mapping in lotus-gateway:

- `review_type=RISK` maps to `event_type=SUBMITTED_FOR_RISK_REVIEW`
- `review_type=COMPLIANCE` maps to `event_type=SUBMITTED_FOR_COMPLIANCE_REVIEW`

## Out of Scope

- Full approval workflow and execution orchestration.
- Multi-service aggregation beyond lotus-manage.

## Acceptance Criteria

- Contract and integration tests cover create/list/detail/submit routes.
- `make check` and `make test-integration` pass.
- README endpoint documentation updated in same PR.
