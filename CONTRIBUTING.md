# Contributing

## Working model

This repository follows a docs-with-code rule: every implementation change must include the required documentation updates in the same pull request.

## Documentation requirements by change type

- API contract or payload changes:
  - Update `README.md` endpoint/contract notes.
  - Update or add contract/integration tests.
  - If behavior is material, add/update an RFC in `docs/rfcs` and update `docs/rfcs/README.md`.
- Architecture or service boundary changes:
  - Add/update an RFC in `docs/rfcs`.
  - Update architecture docs under `docs/documentation`.
- Tooling/CI/quality gate changes:
  - Update docs under `docs/documentation` and relevant runbooks.
- Operations/startup/environment changes:
  - Update run commands and environment variable documentation in `README.md`.

## Definition of done

- Tests added/updated for the behavior change.
- `make check` passes locally.
- Required docs are updated in the same PR.
- PR template checklist is fully completed.

## Branch + PR policy

- Target branch: `main` via pull request only.
- Required status checks must pass.
- Linear history is enforced.
- Auto-merge is enabled for CI-passing PRs.

## RFC flow

- Use one RFC per focused architectural change.
- Keep RFC status current in `docs/rfcs/README.md`.
- When implemented, mark status as `IMPLEMENTED` and link the PR.
