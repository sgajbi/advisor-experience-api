# RFC-0013: Workbench Position Valuation Fields

## Problem Statement
Workbench baseline holdings lacked per-position valuation and weight fields, limiting portfolio review quality and making the UI appear incomplete even when positions were present.

## Root Cause
`WorkbenchPositionView` only exposed security, instrument, asset class, and quantity. Position-level valuation data from PAS holdings payload was not propagated through BFF contracts.

## Proposed Solution
- Extend `WorkbenchPositionView` with:
  - `market_value_base: float | None`
  - `weight_pct: float | None`
- Parse these fields from PAS holdings payload where available.
- If `weight_pct` is absent but `market_value_base` and total market value are available, derive weight in BFF.

## Architectural Impact
- Backward-compatible additive contract update.
- Improves backend-driven UI composition and avoids duplicating valuation derivation logic in frontend.

## Risks and Trade-offs
- Some portfolios may still return `None` for valuation fields if upstream PAS pricing/valuation is incomplete.
- Field mapping relies on known PAS payload key aliases; additional aliases may be required if upstream payload variations expand.

## High-Level Implementation Approach
1. Update BFF contract model with optional valuation fields.
2. Update holdings extraction logic to map and derive valuation context.
3. Add/adjust unit and integration tests.

## Status
IMPLEMENTED
