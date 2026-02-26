# RFC-0005: Live Multi-Service E2E for Platform Capabilities

- Status: IMPLEMENTED
- Date: 2026-02-23
- Owner: lotus-gateway

## Context

`GET /api/v1/platform/capabilities` is an aggregation API that depends on three upstream services:
- lotus-manage: `lotus-advise`
- lotus-core: `lotus-core`
- lotus-performance: `lotus-performance`

Unit and local integration tests validated orchestration logic, but they did not validate runtime wiring to live upstream containers.

## Decision

Introduce a containerized live E2E validation path in `lotus-gateway`:
- Add `docker-compose.e2e.yml` to start lotus-manage + lotus-core query stack + lotus-performance + lotus-gateway on one Docker network.
- Add `tests/e2e/test_platform_capabilities_live.py` to assert lotus-gateway returns non-partial aggregation with lotus-core/lotus-performance/lotus-manage sources.
- Add Make targets:
  - `make e2e-up`
  - `make test-e2e-live`
  - `make e2e-down`
- Add CI job `E2E Platform Capabilities (Live Upstreams)` to clone upstream repos, start stack, execute assertions, and teardown.

## Rationale

- Detects real integration regressions (routing, env wiring, network contracts, startup dependencies).
- Keeps lotus-gateway business behavior validated against actual upstream contract implementations.
- Aligns with platform strategy where lotus-gateway is thin orchestration and backend services own domain complexity.

## Consequences

Positive:
- Higher confidence in cross-service integration before merge.
- Explicitly validated `lotus-core + lotus-performance + lotus-manage -> lotus-gateway` capability path.

Trade-offs:
- CI runtime increases due to multi-repo clone/build.
- lotus-core stack startup remains the slowest stage because query service requires DB migration bootstrapping.

## Follow-ups

- Add a nightly, broader E2E suite for proposal lifecycle paths once lotus-core and lotus-performance expose additional integrated APIs needed by UI workflows.
- Consider publishing versioned upstream Docker images to reduce CI build time.

