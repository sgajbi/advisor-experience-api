# RFC-0003 - AEA E2E Workflow Coverage Wave 1

## Problem Statement

AEA currently has a single live-upstream E2E test. That is not enough to represent key BFF workflows in the E2E test bucket.

## Root Cause

E2E coverage was initially limited to one platform capability live check.

## Proposed Solution

Add workflow-oriented E2E tests that validate:

- platform capability aggregation and health endpoints
- proposal lifecycle orchestration through DPM-facing endpoints
- workbench simulation/sandbox orchestration across PAS + PA + DPM adapters
- reporting snapshot/summary/review orchestration through RAS adapter

## Architectural Impact

No production code changes. Test-only governance and confidence improvement.

## Risks and Trade-offs

- Slight increase in E2E runtime.
- Uses mocked upstream adapters to keep deterministic feedback in local/CI test runs.

## High-Level Implementation

1. Add E2E workflow tests under `tests/e2e`.
2. Reuse TestClient and adapter monkeypatch strategy for deterministic orchestration checks.
3. Keep existing live-upstream test as a separate external integration gate.
