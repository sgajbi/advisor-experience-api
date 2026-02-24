from fastapi.testclient import TestClient

from app.main import app


def test_platform_capabilities_router_success(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "sourceService": "portfolio-analytics-system",
            "contractVersion": "v1",
            "policyVersion": "pas-default-v1",
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
            "policyVersion": "pa-default-v1",
            "features": [{"key": "pa.analytics.twr", "enabled": True}],
            "workflows": [{"workflow_key": "performance_snapshot", "enabled": True}],
            "supportedInputModes": ["pas_ref", "inline_bundle"],
        }

    async def _dpm(*args, **kwargs):
        return 200, {
            "sourceService": "dpm-rebalance-engine",
            "contractVersion": "v1",
            "policyVersion": "dpm-default-v1",
            "features": [
                {"key": "dpm.proposals.lifecycle", "enabled": True},
                {"key": "dpm.support.run_apis", "enabled": True},
            ],
            "workflows": [{"workflow_key": "proposal_lifecycle", "enabled": True}],
            "supportedInputModes": ["pas_ref", "inline_bundle"],
        }

    async def _pas_policy(*args, **kwargs):
        return 200, {
            "policyProvenance": {
                "policyVersion": "pas-default-v1",
                "policySource": "tenant",
                "matchedRuleId": "tenant.default.consumers.BFF",
                "strictMode": False,
            },
            "allowedSections": ["OVERVIEW", "HOLDINGS"],
            "warnings": [],
        }

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_capabilities", _pas)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_effective_policy", _pas_policy)
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
    assert body["normalized"]["policyVersionsBySource"] == {
        "pas": "pas-default-v1",
        "pa": "pa-default-v1",
        "dpm": "dpm-default-v1",
    }
    assert body["normalized"]["pasPolicyDiagnostics"]["available"] is True


def test_platform_capabilities_router_partial_failure(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "sourceService": "portfolio-analytics-system",
            "contractVersion": "v1",
            "policyVersion": "pas-default-v1",
            "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
            "workflows": [],
            "supportedInputModes": ["pas_ref"],
        }

    async def _pa(*args, **kwargs):
        return 500, {"detail": "upstream failed"}

    async def _dpm(*args, **kwargs):
        raise RuntimeError("upstream exception")

    async def _pas_policy(*args, **kwargs):
        return 503, {"detail": "policy unavailable"}

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_capabilities", _pas)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_effective_policy", _pas_policy)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_capabilities", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/platform/capabilities?consumerSystem=BFF&tenantId=default")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["partialFailure"] is True
    assert set(body["sources"].keys()) == {"pas"}
    assert len(body["errors"]) == 3
    assert body["normalized"]["navigation"]["analytics_studio"] is False
    assert body["normalized"]["moduleHealth"]["pa"] == "unavailable"
    assert body["normalized"]["policyVersionsBySource"]["pas"] == "pas-default-v1"
    assert body["normalized"]["policyVersionsBySource"]["pa"] == "unknown"
    assert body["normalized"]["pasPolicyDiagnostics"]["available"] is False
