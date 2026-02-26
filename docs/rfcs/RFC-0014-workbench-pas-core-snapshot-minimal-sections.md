# RFC-0014 Workbench lotus-core Core Snapshot Minimal Sections

## Problem
Workbench overview currently requests `PERFORMANCE` from lotus-core core snapshot even though performance is owned by lotus-performance.

## Decision
- lotus-gateway workbench should request only lotus-core core data sections needed for overview composition:
  - `OVERVIEW`
  - `HOLDINGS`
- Performance snapshot remains sourced from lotus-performance.

## Architectural Impact
- Cleaner lotus-core/lotus-performance boundaries in the lotus-gateway orchestration layer.
- Reduced coupling to deprecated lotus-core analytics sections in `core-snapshot`.

## Implementation
1. Update workbench overview lotus-core request to remove `PERFORMANCE`.
2. Keep lotus-performance performance call as the single performance source for the response contract.

