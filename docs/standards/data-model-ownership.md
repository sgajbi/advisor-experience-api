# Data Model Ownership

- Service: `lotus-gateway`
- Ownership status: no persisted domain entities.
- Responsibility: UI/BFF orchestration and response shaping.

## Boundaries

- PAS is the source for core portfolio data.
- PA is the source for advanced analytics.
- DPM is the source for advisory/discretionary workflow computations.
- RAS is the source for reporting and aggregation outputs.

## Vocabulary

- Use canonical terms from `lotus-platform/Domain Vocabulary Glossary.md`.
- Do not introduce parallel aliases for portfolio, position, transaction, valuation, performance, risk.

