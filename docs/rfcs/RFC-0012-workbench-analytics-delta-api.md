# RFC-0012: Workbench Analytics Delta API

- Status: IMPLEMENTED
- Date: 2026-02-24
- Owners: Advisor Experience API

## Problem Statement

Workbench UI needs backend-driven analytics for current vs proposed portfolio state, but today analytics views are mostly client-side approximations.

## Root Cause

- No dedicated lotus-gateway analytics endpoint for simulation-session deltas.
- No standardized response for grouped allocation changes, top movers, active return, and concentration proxy.

## Proposed Solution

Add `GET /api/v1/workbench/{portfolio_id}/analytics` with:

1. Grouped allocation deltas (`ASSET_CLASS` or `SECURITY`).
2. Top projected changes by quantity delta.
3. Benchmark-relative return snapshot (`portfolio`, `benchmark`, `active`).
4. Concentration risk proxy (HHI current vs proposed).

## Architectural Impact

- Keeps analytics shaping in lotus-gateway layer.
- Enables UI consistency and reduces client-side analytics duplication.

## Risks and Trade-offs

- Quantity-based proxy analytics are not full valuation/risk analytics.
- Requires future lotus-performance integration for richer attribution/risk dimensions.

## High-Level Implementation Approach

1. Extend Workbench contracts with analytics response models.
2. Add analytics aggregation logic in Workbench service.
3. Expose analytics endpoint via Workbench router.
4. Add unit/integration/contract tests for API behavior and schema.
