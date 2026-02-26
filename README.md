# lotus-gateway

FastAPI lotus-gateway for Advisor Workbench, scoped to lotus-manage-first proposal workflows.

## Contribution Standards

- Contribution process: `CONTRIBUTING.md`
- Docs-with-code standard: `docs/documentation/implementation-documentation-standard.md`
- PR checklist template: `.github/pull_request_template.md`
- Platform-wide architecture governance source: `https://github.com/sgajbi/lotus-platform`

## Quickstart

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
make run
```

API docs: `http://localhost:8100/docs`

## Current endpoints

- `POST /api/v1/proposals/simulate` (proxies to lotus-manage `/rebalance/proposals/simulate`)
- `POST /api/v1/proposals` (create draft proposal via lotus-manage lifecycle create)
- `GET /api/v1/proposals` (list proposals)
- `GET /api/v1/proposals/{proposal_id}` (proposal detail)
- `GET /api/v1/proposals/{proposal_id}/versions/{version_no}` (immutable proposal version detail)
- `POST /api/v1/proposals/{proposal_id}/versions` (create proposal version `N+1`)
- `POST /api/v1/proposals/{proposal_id}/submit` (submit draft for review via lotus-manage transition)
- `POST /api/v1/proposals/{proposal_id}/approve-risk` (risk approval action)
- `POST /api/v1/proposals/{proposal_id}/approve-compliance` (compliance approval action)
- `POST /api/v1/proposals/{proposal_id}/record-client-consent` (client consent action)
- `GET /api/v1/proposals/{proposal_id}/workflow-events` (workflow timeline)
- `GET /api/v1/proposals/{proposal_id}/approvals` (approval records)
- `GET /api/v1/platform/capabilities` (aggregated lotus-core+lotus-performance+lotus-manage capability contract for UI)
- `GET /api/v1/workbench/{portfolio_id}/overview` (aggregated lotus-core+lotus-performance+lotus-manage decision-console overview)
- `GET /api/v1/reports/{portfolio_id}/snapshot` (report-ready aggregation rows from lotus-report)
- `POST /api/v1/intake/portfolio-bundle` (lotus-core ingestion bundle pass-through)
- `POST /api/v1/intake/uploads/preview` (lotus-core upload preview pass-through)
- `POST /api/v1/intake/uploads/commit` (lotus-core upload commit pass-through)
- `GET /api/v1/lookups/portfolios` (lotus-core-backed portfolio selector values)
- `GET /api/v1/lookups/instruments` (lotus-core-backed instrument selector values)
- `GET /api/v1/lookups/currencies` (lotus-core-backed currency selector values)

## Docker

```bash
make docker-up
make docker-down

make ci-local-docker
make ci-local-docker-down
```

Live platform-capabilities E2E (lotus-gateway + lotus-core + lotus-performance + lotus-manage):

```bash
export ADVISE_REPO_PATH=/c/Users/sande/dev/lotus-advise
export MANAGE_REPO_PATH=/c/Users/sande/dev/lotus-manage
export PAS_REPO_PATH=/c/Users/sande/dev/lotus-core
export PA_REPO_PATH=/c/Users/sande/dev/lotus-performance
make e2e-up
make test-e2e-live
make e2e-down
```

Coverage gate (local parity with CI threshold):

```bash
python -m pytest --cov=src/app --cov-report=term-missing
```

## Demo Pack

- `docs/demo/README.md`
- `docs/demo/payloads/proposal-create.json`
- `docs/demo/scripts/demo-approval-chain.sh`

## Platform Foundation Commands

- `make migration-smoke`
- `make migration-apply`
- `make security-audit`

Standards documentation:

- `docs/standards/migration-contract.md`
- `docs/standards/data-model-ownership.md`



Split routing notes:
- Advisory lifecycle APIs (/api/v1/proposals/*) use DECISIONING_SERVICE_BASE_URL (lotus-advise).
- lotus-manage/workbench APIs use MANAGEMENT_SERVICE_BASE_URL (lotus-manage) when MANAGE_SPLIT_ENABLED=true.



