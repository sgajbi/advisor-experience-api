# RFC-0001: DPM-First BFF Proposal Simulation Slice

- Status: IMPLEMENTING
- Date: 2026-02-22

## Goal

Scope BFF to DPM first and deliver proposal simulation as the first production UX path.

## Decision

- BFF exposes `POST /api/v1/proposals/simulate`.
- BFF forwards payload to DPM `POST /rebalance/proposals/simulate`.
- BFF enforces correlation id propagation and idempotency handling.

## Out of Scope

- Portfolio core and performance integrations in this phase.
- Non-DPM workflows.

## Acceptance Criteria

- Endpoint covered by unit/contract/integration tests.
- CI green with `make check` and `make test-integration`.
