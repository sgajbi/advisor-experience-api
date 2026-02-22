# advisor-experience-api

FastAPI BFF for Advisor Workbench, scoped to DPM-first proposal workflows.

## Contribution Standards

- Contribution process: `CONTRIBUTING.md`
- Docs-with-code standard: `docs/documentation/implementation-documentation-standard.md`
- PR checklist template: `.github/pull_request_template.md`

## Quickstart

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
make run
```

API docs: `http://localhost:8100/docs`

## Current endpoint

- `POST /api/v1/proposals/simulate` (proxies to DPM `/rebalance/proposals/simulate`)
- `POST /api/v1/proposals` (create draft proposal via DPM lifecycle create)
- `GET /api/v1/proposals` (list proposals)
- `GET /api/v1/proposals/{proposal_id}` (proposal detail)
- `POST /api/v1/proposals/{proposal_id}/submit` (submit draft for review via DPM transition)
