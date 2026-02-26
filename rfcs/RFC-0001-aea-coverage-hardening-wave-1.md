# RFC-0001: AEA Coverage Hardening Wave 1

## Status

Proposed

## Date

2026-02-24

## Problem Statement

`lotus-gateway` had low meaningful coverage (~90%) and important backend orchestration branches were not sufficiently validated, especially in workbench orchestration, reporting error propagation, and upstream client fallback handling.

## Decision

Deliver an incremental hardening wave that raises meaningful coverage and expands behavioral assertions across unit/integration layers while preserving existing contracts.

## Scope

- Add integration tests for:
  - main app health/readiness and unhandled exception problem+json contract
  - reporting summary/review upstream error propagation
- Add unit tests for:
  - upstream clients (workbench analytics route, ingestion/reporting fallback payload handling)
  - workbench service edge paths (policy/offline paths, analytics payload guards, projected state guards, parsing edge cases)

## Current Result (Wave 1 + Wave 2 on same PR)

- Tests: 127 passing
- Coverage: 99% (`src/app`)
- `workbench_service` increased to 98% with broad branch hardening
- All AEA client adapters reached 100% line coverage

## Follow-up

Wave 3 can focus on final branch-coverage gaps and deprecation warning cleanup.

