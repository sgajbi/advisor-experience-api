import pytest

from app.services.platform_capabilities_service import PlatformCapabilitiesService


class _StubClient:
    def __init__(
        self,
        status_code: int,
        payload: dict,
        policy_status_code: int = 200,
        policy_payload: dict | None = None,
    ):
        self.status_code = status_code
        self.payload = payload
        self.policy_status_code = policy_status_code
        self.policy_payload = policy_payload or {
            "policyProvenance": {
                "policyVersion": "pas-default-v1",
                "policySource": "default",
                "matchedRuleId": "default",
                "strictMode": False,
            },
            "allowedSections": ["OVERVIEW"],
            "warnings": [],
        }

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        return self.status_code, self.payload

    async def get_effective_policy(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        return self.policy_status_code, self.policy_payload


class _ErrorClient:
    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        raise RuntimeError("upstream unavailable")

    async def get_effective_policy(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        raise RuntimeError("upstream unavailable")


@pytest.mark.asyncio
async def test_platform_capabilities_all_sources_success():
    service = PlatformCapabilitiesService(
        dpm_client=_StubClient(
            200,
            {
                "sourceService": "dpm",
                "policyVersion": "dpm-tenant-a-v2",
                "supportedInputModes": ["pas_ref", "inline_bundle"],
                "features": [
                    {"key": "dpm.proposals.lifecycle", "enabled": True},
                    {"key": "dpm.support.run_apis", "enabled": True},
                ],
                "workflows": [{"workflow_key": "proposal_lifecycle", "enabled": True}],
            },
        ),
        pas_client=_StubClient(
            200,
            {
                "sourceService": "pas",
                "policyVersion": "pas-tenant-a-v3",
                "supportedInputModes": ["pas_ref"],
                "features": [
                    {"key": "pas.integration.core_snapshot", "enabled": True},
                    {"key": "pas.ingestion.bulk_upload", "enabled": True},
                ],
                "workflows": [{"workflow_key": "portfolio_bulk_onboarding", "enabled": True}],
            },
            policy_payload={
                "policyProvenance": {
                    "policyVersion": "pas-policy-v7",
                    "policySource": "tenant",
                    "matchedRuleId": "tenant.default.consumers.BFF",
                    "strictMode": True,
                },
                "allowedSections": ["OVERVIEW", "HOLDINGS"],
                "warnings": ["SECTIONS_FILTERED_BY_POLICY"],
            },
        ),
        pa_client=_StubClient(
            200,
            {
                "sourceService": "pa",
                "policyVersion": "pa-tenant-a-v4",
                "supportedInputModes": ["pas_ref", "inline_bundle"],
                "features": [{"key": "pa.analytics.twr", "enabled": True}],
                "workflows": [{"workflow_key": "performance_snapshot", "enabled": True}],
            },
        ),
        reporting_client=_StubClient(
            200,
            {
                "sourceService": "reporting-aggregation-service",
                "policyVersion": "ras-tenant-a-v1",
                "supportedInputModes": ["pas_ref"],
                "features": [
                    {"key": "ras.reporting.portfolio_summary", "enabled": True},
                    {"key": "ras.reporting.portfolio_review", "enabled": True},
                ],
                "workflows": [{"workflow_key": "portfolio_reporting", "enabled": True}],
            },
        ),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="BFF",
        tenant_id="default",
        correlation_id="corr-1",
    )

    assert response.data.partial_failure is False
    assert set(response.data.sources.keys()) == {"pas", "pa", "dpm", "ras"}
    assert response.data.errors == []
    assert response.data.normalized.navigation["portfolio_intake"] is True
    assert response.data.normalized.navigation["analytics_studio"] is True
    assert response.data.normalized.navigation["advisory_pipeline"] is True
    assert response.data.normalized.navigation["reporting_hub"] is True
    assert response.data.normalized.workflow_flags["proposal_lifecycle"] is True
    assert response.data.normalized.workflow_flags["portfolio_reporting"] is True
    assert "inline_bundle" in response.data.normalized.input_modes_union
    assert response.data.normalized.module_health["pas"] == "available"
    assert response.data.normalized.policy_versions_by_source == {
        "pas": "pas-tenant-a-v3",
        "pa": "pa-tenant-a-v4",
        "dpm": "dpm-tenant-a-v2",
        "ras": "ras-tenant-a-v1",
    }
    assert response.data.normalized.pas_policy_diagnostics["available"] is True
    assert response.data.normalized.pas_policy_diagnostics["policyProvenance"] == {
        "policyVersion": "pas-policy-v7",
        "policySource": "tenant",
        "matchedRuleId": "tenant.default.consumers.BFF",
        "strictMode": True,
    }


@pytest.mark.asyncio
async def test_platform_capabilities_partial_failure_on_error():
    service = PlatformCapabilitiesService(
        dpm_client=_ErrorClient(),
        pas_client=_StubClient(
            200,
            {
                "sourceService": "pas",
                "policyVersion": "pas-tenant-default-v1",
                "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
                "workflows": [],
            },
            policy_status_code=503,
            policy_payload={"detail": "service unavailable"},
        ),
        pa_client=_StubClient(502, {"detail": "bad gateway"}),
        reporting_client=_StubClient(503, {"detail": "upstream failed"}),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="BFF",
        tenant_id="default",
        correlation_id="corr-2",
    )

    assert response.data.partial_failure is True
    assert set(response.data.sources.keys()) == {"pas"}
    assert len(response.data.errors) == 4
    assert response.data.normalized.navigation["analytics_studio"] is False
    assert response.data.normalized.navigation["advisory_pipeline"] is False
    assert response.data.normalized.module_health["pa"] == "unavailable"
    assert response.data.normalized.module_health["dpm"] == "unavailable"
    assert response.data.normalized.module_health["ras"] == "unavailable"
    assert response.data.normalized.policy_versions_by_source == {
        "pas": "pas-tenant-default-v1",
        "pa": "unknown",
        "dpm": "unknown",
        "ras": "unknown",
    }
    assert response.data.normalized.pas_policy_diagnostics["available"] is False
    assert (
        "PAS_POLICY_ENDPOINT_UNAVAILABLE"
        in (response.data.normalized.pas_policy_diagnostics["warnings"])
    )
