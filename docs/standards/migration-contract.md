# Migration Contract Standard

- Service: `lotus-gateway` (BFF)
- Persistence mode: **no persistent schema**.
- Migration policy: **versioned migration contract is mandatory** even in no-schema mode.

## Deterministic Checks

- `make migration-smoke` validates this migration contract document.
- CI executes `make migration-smoke` for every PR.

## Rollback and Forward-Fix

- No runtime schema rollback applies in no-schema mode.
- Any contract drift is resolved through **forward-fix** and re-validation.

## Future Upgrade Path

If a persistent store is introduced:

1. Add versioned migrations.
2. Add deterministic migration apply checks in CI.
3. Keep forward-only migration policy with rollback strategy documented.

