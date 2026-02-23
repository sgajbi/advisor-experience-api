from fastapi.testclient import TestClient

from app.main import app


def test_workbench_router_success(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "portfolio": {
                "portfolio_id": "PF_1001",
                "base_currency": "USD",
                "booking_center": "SG",
                "cif_id": "CIF_1001",
            },
            "snapshot": {
                "as_of_date": "2026-02-23",
                "overview": {"total_market_value": 1000.0, "total_cash": 250.0},
                "holdings": {"holdingsByAssetClass": {"Equity": [{"id": "EQ_1"}]}},
            },
        }

    async def _pa(*args, **kwargs):
        return 200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 2.5}}}

    async def _dpm(*args, **kwargs):
        return 200, {
            "items": [
                {
                    "rebalance_run_id": "rr_100",
                    "status": "PENDING_REVIEW",
                    "created_at": "2026-02-23T01:00:00Z",
                }
            ]
        }

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_core_snapshot", _pas)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_pas_snapshot_twr", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio"]["portfolio_id"] == "PF_1001"
    assert body["overview"]["position_count"] == 1
    assert body["performance_snapshot"]["period"] == "YTD"
    assert body["rebalance_snapshot"]["status"] == "PENDING_REVIEW"


def test_workbench_router_partial_failure(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "portfolio": {"portfolio_id": "PF_1001", "base_currency": "USD"},
            "snapshot": {
                "as_of_date": "2026-02-23",
                "overview": {"total_market_value": 1000.0, "total_cash": 100.0},
            },
        }

    async def _pa(*args, **kwargs):
        return 503, {"detail": "paused"}

    async def _dpm(*args, **kwargs):
        return 503, {"detail": "paused"}

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_core_snapshot", _pas)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_pas_snapshot_twr", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["performance_snapshot"] is None
    assert body["rebalance_snapshot"] is None
    assert len(body["partial_failures"]) == 2
