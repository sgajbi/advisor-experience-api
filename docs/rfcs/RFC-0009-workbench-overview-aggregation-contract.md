# RFC-0009 Workbench Overview Aggregation Contract

- Status: IMPLEMENTED
- Date: 2026-02-23

## Summary

Add `GET /api/v1/workbench/{portfolio_id}/overview` to provide a single decision-console payload for UI.

## Contract

Output fields:
- `correlation_id`
- `contract_version`
- `as_of_date`
- `portfolio`
- `overview`
- `performance_snapshot` (nullable)
- `rebalance_snapshot` (nullable)
- `warnings[]`
- `partial_failures[]`

## Integration Behavior

1. PAS core snapshot is required and drives portfolio/overview baseline.
2. PA performance snapshot and DPM latest rebalance status are optional enrichments.
3. Upstream enrichment failures are returned as partial failures instead of hard endpoint failure.

## Rationale

1. Gives CA/PM users one coherent workbench payload.
2. Preserves resilience with partial-failure semantics.
3. Keeps orchestration and integration complexity in BFF, not UI.
