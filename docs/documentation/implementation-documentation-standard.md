# Implementation + Documentation Standard

## Objective

Keep implementation and documentation synchronized so every merged PR is executable, testable, and understandable without tribal knowledge.

## Required updates per PR

- Code change: add/update tests.
- Contract/behavior change: update `README.md` and relevant API/flow docs.
- Architecture change: add/update RFC under `docs/rfcs` and index entry in `docs/rfcs/README.md`.
- Tooling/CI change: document new commands and pipeline behavior under `docs/documentation`.

## Minimum evidence before merge

- `make check` succeeds locally.
- PR template documentation checklist completed.
- RFC status updated (`PROPOSED`, `IMPLEMENTING`, `IMPLEMENTED`, `SUPERSEDED`) when applicable.

## Practical rule

If a new engineer cannot run and understand the change from repo docs alone, documentation is incomplete.
