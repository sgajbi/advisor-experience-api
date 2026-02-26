# RFC-0004 Platform Capabilities Aggregation Contract

- Status: Accepted
- Date: 2026-02-23

## Summary

Add lotus-gateway endpoint `GET /api/v1/platform/capabilities` to aggregate lotus-core, lotus-performance, and lotus-manage integration capability contracts for UI consumption.

## Contract

Inputs:
- `consumerSystem`
- `tenantId`

Output envelope:
- `data.contractVersion`
- `data.consumerSystem`
- `data.tenantId`
- `data.sources` (`pas`, `pa`, `dpm`)
- `data.partialFailure`
- `data.errors[]`

## Behavior

1. Calls lotus-core, lotus-performance, and lotus-manage `/integration/capabilities`.
2. Returns partial results when one or more upstream services fail.
3. Preserves failure metadata in `errors[]` for UI diagnostics.

## Rationale

1. Keeps integration complexity in backend/lotus-gateway.
2. Prevents UI hardcoding of service capability assumptions.
3. Provides one stable contract for platform-level feature/workflow control.
