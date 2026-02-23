import asyncio
from typing import Any, cast

from app.clients.dpm_client import DpmClient
from app.clients.pa_client import PaClient
from app.clients.pas_client import PasClient
from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformCapabilitiesData,
    PlatformCapabilitiesResponse,
)


class PlatformCapabilitiesService:
    def __init__(
        self,
        dpm_client: DpmClient,
        pas_client: PasClient,
        pa_client: PaClient,
        contract_version: str,
    ):
        self._dpm_client = dpm_client
        self._pas_client = pas_client
        self._pa_client = pa_client
        self._contract_version = contract_version

    async def get_platform_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> PlatformCapabilitiesResponse:
        results = await asyncio.gather(
            self._pas_client.get_capabilities(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._pa_client.get_capabilities(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._dpm_client.get_capabilities(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            return_exceptions=True,
        )

        sources: dict[str, dict[str, Any]] = {}
        errors: list[CapabilitySourceError] = []
        service_names = ["pas", "pa", "dpm"]

        for service_name, result in zip(service_names, results, strict=True):
            if isinstance(result, BaseException):
                errors.append(
                    CapabilitySourceError(
                        service=service_name,
                        status_code=500,
                        detail=f"upstream_exception: {result}",
                    )
                )
                continue

            status_code, payload = cast(tuple[int, dict[str, Any]], result)
            if status_code >= 400:
                errors.append(
                    CapabilitySourceError(
                        service=service_name,
                        status_code=status_code,
                        detail=str(payload.get("detail", payload)),
                    )
                )
                continue

            sources[service_name] = payload

        data = PlatformCapabilitiesData(
            consumerSystem=consumer_system,
            tenantId=tenant_id,
            contractVersion=self._contract_version,
            sources=sources,
            partialFailure=len(errors) > 0,
            errors=errors,
        )
        return PlatformCapabilitiesResponse(data=data)
