import pytest

from app.services.platform_capabilities_service import PlatformCapabilitiesService


class _StubClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        return self.status_code, self.payload


class _ErrorClient:
    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        raise RuntimeError("upstream unavailable")


@pytest.mark.asyncio
async def test_platform_capabilities_all_sources_success():
    service = PlatformCapabilitiesService(
        dpm_client=_StubClient(200, {"sourceService": "dpm"}),
        pas_client=_StubClient(200, {"sourceService": "pas"}),
        pa_client=_StubClient(200, {"sourceService": "pa"}),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="BFF",
        tenant_id="default",
        correlation_id="corr-1",
    )

    assert response.data.partial_failure is False
    assert set(response.data.sources.keys()) == {"pas", "pa", "dpm"}
    assert response.data.errors == []


@pytest.mark.asyncio
async def test_platform_capabilities_partial_failure_on_error():
    service = PlatformCapabilitiesService(
        dpm_client=_ErrorClient(),
        pas_client=_StubClient(200, {"sourceService": "pas"}),
        pa_client=_StubClient(502, {"detail": "bad gateway"}),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="BFF",
        tenant_id="default",
        correlation_id="corr-2",
    )

    assert response.data.partial_failure is True
    assert set(response.data.sources.keys()) == {"pas"}
    assert len(response.data.errors) == 2
