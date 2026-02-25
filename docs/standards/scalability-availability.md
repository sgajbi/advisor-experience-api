# Scalability and Availability Standard Alignment

Service: AEA (BFF)

This repository adopts the platform-wide standard defined in pbwm-platform-docs/Scalability and Availability Standard.md.

## Implemented Baseline

- Stateless service behavior with externalized durable state.
- Explicit timeout and bounded retry/backoff for inter-service communication where applicable.
- Health/liveness/readiness endpoints for runtime orchestration.
- Observability instrumentation for latency/error/throughput diagnostics.

## Required Evidence

- Compliance matrix entry in pbwm-platform-docs/output/scalability-availability-compliance.md.
- Service-specific tests covering resilience and concurrency-critical paths.

## Availability Baseline

- Internal SLO baseline: p95 response latency < 300 ms for health and capability endpoints; error rate < 1%.
- Recovery assumptions: RTO 30 minutes, RPO 15 minutes for dependent platform data recovery.
- Backup and restore: persistence-owning upstream services are required to expose validated backup/restore runbooks;
  AEA validates readiness through `/health/ready` and dependency checks during platform startup.

## Deviation Rule

Any deviation from this standard requires ADR/RFC with remediation timeline.
