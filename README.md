# advisor-experience-api

FastAPI BFF for Advisor Workbench, scoped to DPM-first proposal workflows.

## Contribution Standards

- Contribution process: `CONTRIBUTING.md`
- Docs-with-code standard: `docs/documentation/implementation-documentation-standard.md`
- PR checklist template: `.github/pull_request_template.md`
- Platform-wide architecture governance source: `https://github.com/sgajbi/pbwm-platform-docs`

## Quickstart

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
make run
```

API docs: `http://localhost:8100/docs`

## Current endpoints

- `POST /api/v1/proposals/simulate` (proxies to DPM `/rebalance/proposals/simulate`)
- `POST /api/v1/proposals` (create draft proposal via DPM lifecycle create)
- `GET /api/v1/proposals` (list proposals)
- `GET /api/v1/proposals/{proposal_id}` (proposal detail)
- `GET /api/v1/proposals/{proposal_id}/versions/{version_no}` (immutable proposal version detail)
- `POST /api/v1/proposals/{proposal_id}/versions` (create proposal version `N+1`)
- `POST /api/v1/proposals/{proposal_id}/submit` (submit draft for review via DPM transition)
- `POST /api/v1/proposals/{proposal_id}/approve-risk` (risk approval action)
- `POST /api/v1/proposals/{proposal_id}/approve-compliance` (compliance approval action)
- `POST /api/v1/proposals/{proposal_id}/record-client-consent` (client consent action)
- `GET /api/v1/proposals/{proposal_id}/workflow-events` (workflow timeline)
- `GET /api/v1/proposals/{proposal_id}/approvals` (approval records)
- `GET /api/v1/platform/capabilities` (aggregated PAS+PA+DPM capability contract for UI)
- `GET /api/v1/workbench/{portfolio_id}/overview` (aggregated PAS+PA+DPM decision-console overview)
- `GET /api/v1/reports/{portfolio_id}/snapshot` (report-ready aggregation rows from reporting-aggregation-service)
- `POST /api/v1/intake/portfolio-bundle` (PAS ingestion bundle pass-through)
- `POST /api/v1/intake/uploads/preview` (PAS upload preview pass-through)
- `POST /api/v1/intake/uploads/commit` (PAS upload commit pass-through)
- `GET /api/v1/lookups/portfolios` (PAS-backed portfolio selector values)
- `GET /api/v1/lookups/instruments` (PAS-backed instrument selector values)
- `GET /api/v1/lookups/currencies` (PAS-backed currency selector values)

## Docker

```bash
make docker-up
make docker-down

make ci-local-docker
make ci-local-docker-down
```

Live platform-capabilities E2E (BFF + PAS + PA + DPM):

```bash
export DPM_REPO_PATH=/c/Users/sande/dev/dpm-rebalance-engine
export PAS_REPO_PATH=/c/Users/sande/dev/portfolio-analytics-system
export PA_REPO_PATH=/c/Users/sande/dev/performanceAnalytics
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
