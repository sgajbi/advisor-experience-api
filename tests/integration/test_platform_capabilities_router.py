from fastapi.testclient import TestClient

from app.main import app


def test_platform_capabilities_router_success(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "sourceService": "portfolio-analytics-system",
            "contractVersion": "v1",
            "features": [
                {"key": "pas.integration.core_snapshot", "enabled": True},
                {"key": "pas.ingestion.bulk_upload", "enabled": True},
            ],
            "workflows": [{"workflow_key": "portfolio_bulk_onboarding", "enabled": True}],
            "supportedInputModes": ["pas_ref"],
        }

    async def _pa(*args, **kwargs):
        return 200, {
            "sourceService": "performance-analytics",
            "contractVersion": "v1",
            "features": [{"key": "pa.analytics.twr", "enabled": True}],
            "workflows": [{"workflow_key": "performance_snapshot", "enabled": True}],
            "supportedInputModes": ["pas_ref", "inline_bundle"],
        }

    async def _dpm(*args, **kwargs):
        return 200, {
            "sourceService": "dpm-rebalance-engine",
            "contractVersion": "v1",
            "features": [
                {"key": "dpm.proposals.lifecycle", "enabled": True},
                {"key": "dpm.support.run_apis", "enabled": True},
            ],
            "workflows": [{"workflow_key": "proposal_lifecycle", "enabled": True}],
            "supportedInputModes": ["pas_ref", "inline_bundle"],
        }

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_capabilities", _pas)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_capabilities", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/platform/capabilities?consumerSystem=BFF&tenantId=default")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["partialFailure"] is False
    assert set(body["sources"].keys()) == {"pas", "pa", "dpm"}
    assert body["normalized"]["navigation"]["decision_console"] is True
    assert body["normalized"]["workflowFlags"]["proposal_lifecycle"] is True


def test_platform_capabilities_router_partial_failure(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "sourceService": "portfolio-analytics-system",
            "contractVersion": "v1",
            "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
            "workflows": [],
            "supportedInputModes": ["pas_ref"],
        }

    async def _pa(*args, **kwargs):
        return 500, {"detail": "upstream failed"}

    async def _dpm(*args, **kwargs):
        raise RuntimeError("upstream exception")

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_capabilities", _pas)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_capabilities", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/platform/capabilities?consumerSystem=BFF&tenantId=default")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["partialFailure"] is True
    assert set(body["sources"].keys()) == {"pas"}
    assert len(body["errors"]) == 2
    assert body["normalized"]["navigation"]["analytics_studio"] is False
    assert body["normalized"]["moduleHealth"]["pa"] == "unavailable"
