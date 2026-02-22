# advisor-experience-api

FastAPI BFF for Advisor Workbench, scoped to DPM-first proposal workflows.

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
