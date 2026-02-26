# Data Model Ownership

- Service: `lotus-gateway`
- Ownership status: no persisted domain entities.
- Responsibility: UI/lotus-gateway orchestration and response shaping.

## Boundaries

- lotus-core is the source for core portfolio data.
- lotus-performance is the source for advanced analytics.
- lotus-manage is the source for advisory/discretionary workflow computations.
- lotus-report is the source for reporting and aggregation outputs.

## Vocabulary

- Use canonical terms from `lotus-platform/Domain Vocabulary Glossary.md`.
- Do not introduce parallel aliases for portfolio, position, transaction, valuation, performance, risk.


