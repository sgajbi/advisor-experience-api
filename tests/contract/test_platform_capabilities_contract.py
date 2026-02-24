from fastapi.testclient import TestClient

from app.main import app


def test_platform_capabilities_contract_shape(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "portfolio-analytics-system",
            "policyVersion": "pas-default-v1",
            "features": [],
            "workflows": [],
        }

    async def _pa(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "performance-analytics",
            "policyVersion": "pa-default-v1",
            "features": [],
            "workflows": [],
        }

    async def _dpm(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "dpm-rebalance-engine",
            "policyVersion": "dpm-default-v1",
            "features": [],
            "workflows": [],
        }

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_capabilities", _pas)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_capabilities", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/platform/capabilities?consumerSystem=BFF&tenantId=default")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["contractVersion"] == "v1"
    assert payload["consumerSystem"] == "BFF"
    assert payload["tenantId"] == "default"
    assert payload["partialFailure"] is False
    assert "normalized" in payload
    assert "navigation" in payload["normalized"]
    assert "workflowFlags" in payload["normalized"]
    assert "moduleHealth" in payload["normalized"]
    assert "policyVersionsBySource" in payload["normalized"]

    for service_name in ("pas", "pa", "dpm"):
        source = payload["sources"][service_name]
        assert source["contractVersion"] == "v1"
        assert "sourceService" in source
