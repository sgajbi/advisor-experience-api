# RFC-0001: lotus-manage-First lotus-gateway Proposal Simulation Slice

- Status: IMPLEMENTED
- Date: 2026-02-22

## Goal

Scope lotus-gateway to lotus-manage first and deliver proposal simulation as the first production UX path.

## Decision

- lotus-gateway exposes `POST /api/v1/proposals/simulate`.
- lotus-gateway forwards payload to lotus-manage `POST /rebalance/proposals/simulate`.
- lotus-gateway enforces correlation id propagation and idempotency handling.

## Out of Scope

- Portfolio core and performance integrations in this phase.
- Non-lotus-manage workflows.

## Acceptance Criteria

- Endpoint covered by unit/contract/integration tests.
- CI green with `make check` and `make test-integration`.
