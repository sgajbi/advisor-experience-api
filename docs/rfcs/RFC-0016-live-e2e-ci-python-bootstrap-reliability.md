# RFC-0016 Live E2E CI Python Bootstrap Reliability

## Problem Statement
AEA `E2E Platform Capabilities (Live Upstreams)` CI job fails before test execution with `No module named pytest`.

## Root Cause
The live E2E job does not set up Python or install project test dependencies before running `make test-e2e-live`.

## Proposed Solution
In the live E2E CI job:
1. Add `actions/setup-python`.
2. Install dependencies with `pip install -e ".[dev]"`.

## Architectural Impact
No runtime or API changes. CI execution reliability improvement only.

## Risks and Trade-offs
- Slightly longer E2E CI job startup time due to dependency installation.
- Substantially reduced false-negative CI failures.

## High-Level Implementation Approach
1. Update `.github/workflows/ci.yml` live E2E job steps.
2. Re-run CI and confirm job reaches actual live E2E assertions.
