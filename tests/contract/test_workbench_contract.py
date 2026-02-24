from fastapi.testclient import TestClient

from app.contracts.workbench import WorkbenchOverviewResponse
from app.main import app


def test_workbench_response_model_contract_shape() -> None:
    payload = WorkbenchOverviewResponse(
        correlation_id="corr_1",
        contract_version="v1",
        as_of_date="2026-02-23",
        portfolio={
            "portfolio_id": "PF_1001",
            "client_id": "CIF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
        },
        overview={
            "market_value_base": 1000.0,
            "cash_weight_pct": 0.2,
            "position_count": 5,
        },
    )
    assert payload.portfolio.portfolio_id == "PF_1001"
    assert payload.overview.position_count == 5


def test_workbench_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    assert "/api/v1/workbench/{portfolio_id}/overview" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/portfolio-360" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/sandbox/sessions" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/sandbox/sessions/{session_id}/changes" in spec["paths"]
