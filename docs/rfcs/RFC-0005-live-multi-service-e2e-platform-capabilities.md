# RFC-0005: Live Multi-Service E2E for Platform Capabilities

- Status: IMPLEMENTED
- Date: 2026-02-23
- Owner: advisor-experience-api

## Context

`GET /api/v1/platform/capabilities` is an aggregation API that depends on three upstream services:
- DPM: `dpm-rebalance-engine`
- PAS: `portfolio-analytics-system`
- PA: `performanceAnalytics`

Unit and local integration tests validated orchestration logic, but they did not validate runtime wiring to live upstream containers.

## Decision

Introduce a containerized live E2E validation path in `advisor-experience-api`:
- Add `docker-compose.e2e.yml` to start DPM + PAS query stack + PA + BFF on one Docker network.
- Add `tests/e2e/test_platform_capabilities_live.py` to assert BFF returns non-partial aggregation with PAS/PA/DPM sources.
- Add Make targets:
  - `make e2e-up`
  - `make test-e2e-live`
  - `make e2e-down`
- Add CI job `E2E Platform Capabilities (Live Upstreams)` to clone upstream repos, start stack, execute assertions, and teardown.

## Rationale

- Detects real integration regressions (routing, env wiring, network contracts, startup dependencies).
- Keeps BFF business behavior validated against actual upstream contract implementations.
- Aligns with platform strategy where BFF is thin orchestration and backend services own domain complexity.

## Consequences

Positive:
- Higher confidence in cross-service integration before merge.
- Explicitly validated `PAS + PA + DPM -> BFF` capability path.

Trade-offs:
- CI runtime increases due to multi-repo clone/build.
- PAS stack startup remains the slowest stage because query service requires DB migration bootstrapping.

## Follow-ups

- Add a nightly, broader E2E suite for proposal lifecycle paths once PAS and PA expose additional integrated APIs needed by UI workflows.
- Consider publishing versioned upstream Docker images to reduce CI build time.
