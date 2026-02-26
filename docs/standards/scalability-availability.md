# Scalability and Availability Standard Alignment

Service: AEA (BFF)

This repository adopts the platform-wide standard defined in lotus-platform/Scalability and Availability Standard.md.

## Implemented Baseline

- Stateless service behavior with externalized durable state.
- Explicit timeout and bounded retry/backoff for inter-service communication where applicable.
- Health/liveness/readiness endpoints for runtime orchestration.
- Observability instrumentation for latency/error/throughput diagnostics.

## Required Evidence

- Compliance matrix entry in lotus-platform/output/scalability-availability-compliance.md.
- Service-specific tests covering resilience and concurrency-critical paths.

## Availability Baseline

- Internal SLO baseline: p95 response latency < 300 ms for health and capability endpoints; error rate < 1%.
- Recovery assumptions: RTO 30 minutes, RPO 15 minutes for dependent platform data recovery.
- Backup and restore: persistence-owning upstream services are required to expose validated backup/restore runbooks;
  AEA validates readiness through `/health/ready` and dependency checks during platform startup.

## Database Scalability Fundamentals

- Query plan and index ownership remain with PAS/PA/DPM/RAS persistence domains; AEA does not own tables.
- Growth assumptions for upstream payload sizes are reviewed quarterly and reflected in BFF timeout and pagination policies.
- Retention and archival execution remains upstream, while AEA enforces request shaping to avoid unbounded historical fan-out.

## Caching Policy Baseline

- AEA does not own correctness-critical caches for financial calculations; upstream PAS/PA/RAS remain the source of truth.
- Client-facing response shaping may use explicit TTL request controls where contract-approved (`ttl_hours`), with ownership in BFF read orchestration.
- Invalidation owner is the upstream domain service that owns source data; stale-read tolerance is limited to UI convenience views only.
- Any cache addition requires explicit TTL, invalidation owner, and stale-read behavior documented via ADR/RFC.

## Scale Signal Metrics Coverage

- AEA exports service HTTP metrics via `/metrics` and follows platform label conventions (`service`, `env`, `endpoint`, `status_code`).
- Platform-shared infrastructure metrics for CPU/memory, database, and queue signals are sourced through:
  - `lotus-platform/platform-stack/prometheus/prometheus.yml`
  - `lotus-platform/platform-stack/docker-compose.yml`
  - `lotus-platform/Platform Observability Standards.md`

## Deviation Rule

Any deviation from this standard requires ADR/RFC with remediation timeline.

