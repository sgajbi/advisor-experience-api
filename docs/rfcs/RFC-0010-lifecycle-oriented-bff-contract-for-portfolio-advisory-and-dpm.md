# RFC-0010: Lifecycle-Oriented BFF Contract for Portfolio Foundation, Advisory Iteration, and DPM Iteration

- Status: PROPOSED
- Date: 2026-02-24
- Owners: Advisor Experience API

## Problem Statement

Frontend lifecycle experiences require cohesive domain data and iterative simulation feedback, but BFF contracts are currently optimized for point-in-time feature surfaces rather than end-to-end lifecycle orchestration.

## Root Cause

- BFF endpoints are mostly feature-specific aggregations.
- No single lifecycle session contract for iterative edits and impact refresh.
- Limited first-class abstraction for universal portfolio foundation views.

## Proposed Solution

Introduce lifecycle-oriented BFF surfaces:

1. Portfolio Foundation APIs
   - Unified portfolio list/detail payloads with positions, transactions, health, and analytics summaries.
2. Advisory Iteration Session APIs
   - Session-scoped endpoints for delta updates (trade/cash changes) and immediate impact snapshots.
3. DPM Iteration Session APIs
   - Parallel session model with DPM-specific controls and governance states.
4. Lifecycle Progression APIs
   - Proposal generation, consent state transitions, and execution handoff orchestration.

## Architectural Impact

- BFF becomes explicit orchestration layer for lifecycle UX.
- Clearer service boundary: UI consumes product contracts; domain systems remain system-of-record engines.
- Enables responsive iterative frontend with stable schema and correlation tracing.

## Risks and Trade-offs

- More orchestration logic in BFF increases contract ownership burden.
- Session semantics require clear idempotency and timeout policies.
- Additional integration tests required for cross-service consistency.

## High-Level Implementation Approach

1. Define canonical lifecycle payload schemas and error model.
2. Add foundation endpoints first, then iteration session endpoints.
3. Integrate PAS/PA/DPM responses under deterministic correlation IDs.
4. Add contract and e2e-live tests for iterative loop latency and correctness.

## Downstream/Upstream Dependencies

- Upstream: PAS RFC-046, PA RFC-032, DPM RFC-0029
- Downstream: AW RFC-0007
