# RFC-0014 Workbench PAS Core Snapshot Minimal Sections

## Problem
Workbench overview currently requests `PERFORMANCE` from PAS core snapshot even though performance is owned by PA.

## Decision
- BFF workbench should request only PAS core data sections needed for overview composition:
  - `OVERVIEW`
  - `HOLDINGS`
- Performance snapshot remains sourced from PA.

## Architectural Impact
- Cleaner PAS/PA boundaries in the BFF orchestration layer.
- Reduced coupling to deprecated PAS analytics sections in `core-snapshot`.

## Implementation
1. Update workbench overview PAS request to remove `PERFORMANCE`.
2. Keep PA performance call as the single performance source for the response contract.

