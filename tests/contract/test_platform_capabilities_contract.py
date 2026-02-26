from fastapi.testclient import TestClient

from app.main import app


def test_platform_capabilities_contract_shape(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "lotus-core",
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
            "sourceService": "lotus-advise",
            "policyVersion": "dpm-default-v1",
            "features": [],
            "workflows": [],
        }

    async def _ras(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "lotus-report",
            "policyVersion": "ras-default-v1",
            "features": [],
            "workflows": [],
        }

    async def _pas_policy(*args, **kwargs):
        return 200, {
            "policyProvenance": {
                "policyVersion": "pas-default-v1",
                "policySource": "default",
                "matchedRuleId": "default",
                "strictMode": False,
            },
            "allowedSections": ["OVERVIEW"],
            "warnings": [],
        }

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_capabilities", _pas)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_effective_policy", _pas_policy)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_capabilities", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)
    monkeypatch.setattr("app.clients.reporting_client.ReportingClient.get_capabilities", _ras)

    client = TestClient(app)
    response = client.get("/api/v1/platform/capabilities"
        "?consumerSystem=lotus-gateway&tenantId=default")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["contractVersion"] == "v1"
    assert payload["consumerSystem"] == "lotus-gateway"
    assert payload["tenantId"] == "default"
    assert payload["partialFailure"] is False
    assert "normalized" in payload
    assert "navigation" in payload["normalized"]
    assert "workflowFlags" in payload["normalized"]
    assert "moduleHealth" in payload["normalized"]
    assert "policyVersionsBySource" in payload["normalized"]
    assert "pasPolicyDiagnostics" in payload["normalized"]

    for service_name in ("pas", "pa", "dpm", "ras"):
        source = payload["sources"][service_name]
        assert source["contractVersion"] == "v1"
        assert "sourceService" in source
