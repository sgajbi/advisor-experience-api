# advisor-experience-api

FastAPI BFF for Advisor Workbench.

## Quickstart

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
make run
```

API docs: `http://localhost:8100/docs`

## First endpoint

- `GET /api/v1/workbench/{portfolio_id}/overview`
