# RFC-0003: BFF Approval Chain v1 and Supportability Pass-Through

- Status: IMPLEMENTED
- Date: 2026-02-22
- Depends on: RFC-0002

## Goal

Expose explicit approval-chain orchestration endpoints for UI workflow progression and supportability panels.

## Decision

Add BFF endpoints:

- `POST /api/v1/proposals/{proposal_id}/approve-risk`
- `POST /api/v1/proposals/{proposal_id}/approve-compliance`
- `POST /api/v1/proposals/{proposal_id}/record-client-consent`
- `GET /api/v1/proposals/{proposal_id}/workflow-events`
- `GET /api/v1/proposals/{proposal_id}/approvals`

All routes forward to DPM lifecycle/supportability endpoints with correlation id propagation and strict upstream error passthrough.

## Acceptance Criteria

- Unit, contract, and integration tests validate payload mapping and error behavior.
- CI green for lint/typecheck/unit/integration and Docker parity jobs.
