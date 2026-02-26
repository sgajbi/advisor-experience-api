# RFC-0015 E2E Pyramid Wave 2 - Resilience and Failure Paths

## Problem Statement
lotus-gateway E2E test count is below target pyramid distribution and does not sufficiently validate failure-path orchestration behavior for key lotus-gateway contracts.

## Root Cause
Existing E2E journeys primarily cover happy-path workflows, with limited checks for:
- partial upstream capability aggregation failures
- reporting upstream outage mapping
- sandbox policy evaluation degradation behavior

## Proposed Solution
Add E2E journey tests for:
1. Platform capabilities aggregation with one upstream error (`partialFailure` behavior).
2. Reporting snapshot upstream failure mapped to lotus-gateway gateway error.
3. Workbench sandbox apply-changes flow where lotus-manage policy simulation is unavailable but lotus-core changes succeed.

## Architectural Impact
No runtime or API contract changes. This is verification-depth improvement for existing orchestrated contracts.

## Risks and Trade-offs
- Low runtime risk (tests only).
- Slight CI runtime increase due to additional E2E journeys.

## High-Level Implementation Approach
1. Extend `tests/e2e/test_workflow_journeys.py` with resilience-path tests.
2. Validate with targeted E2E execution.
3. Merge and re-measure pyramid distribution.
