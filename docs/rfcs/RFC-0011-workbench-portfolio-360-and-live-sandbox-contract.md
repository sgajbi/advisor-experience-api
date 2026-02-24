# RFC-0011: Workbench Portfolio 360 and Live Sandbox Contract

- Status: IMPLEMENTED
- Date: 2026-02-24
- Owners: Advisor Experience API

## Problem Statement

The UI needs a single BFF surface for current portfolio state plus iterative projected state during advisory simulation. Existing BFF contracts expose point-in-time overview and proposal APIs, but not a unified Portfolio 360 + live sandbox loop.

## Root Cause

- No first-class Portfolio 360 read model in BFF.
- PAS simulation session APIs were not orchestrated through BFF for UI consumption.
- No session-based BFF contract combining projected positions, summary deltas, and optional policy evaluation feedback.

## Proposed Solution

Add BFF workbench lifecycle endpoints:

1. `GET /api/v1/workbench/{portfolio_id}/portfolio-360`
   - Returns current Portfolio 360 state and optional projected state for a provided session.
2. `POST /api/v1/workbench/{portfolio_id}/sandbox/sessions`
   - Creates PAS simulation session for iterative lifecycle editing.
3. `POST /api/v1/workbench/{portfolio_id}/sandbox/sessions/{session_id}/changes`
   - Applies scenario changes, returns projected positions/summary, and optional DPM policy simulation feedback.

## Architectural Impact

- BFF becomes explicit orchestration layer for PAS simulation sessions.
- UI receives stable lifecycle contract without direct PAS session coupling.
- DPM policy feedback becomes opt-in at sandbox update time.

## Risks and Trade-offs

- Adds orchestration complexity and cross-service error handling paths.
- Policy feedback may be partial/unavailable depending on upstream simulation payload quality.
- Requires additional contract/integration tests to prevent drift.

## High-Level Implementation Approach

1. Extend BFF workbench contracts with Portfolio 360 and sandbox response models.
2. Add PAS client support for simulation-session operations.
3. Implement service orchestration for current + projected states.
4. Add router endpoints, OpenAPI contract checks, and integration tests.
