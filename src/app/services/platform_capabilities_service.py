import asyncio
from typing import Any, cast

from app.clients.dpm_client import DpmClient
from app.clients.pa_client import PaClient
from app.clients.pas_client import PasClient
from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformCapabilitiesData,
    PlatformCapabilitiesNormalized,
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

        normalized = self._build_normalized_capabilities(
            sources=sources,
            errors=errors,
        )
        data = PlatformCapabilitiesData(
            consumerSystem=consumer_system,
            tenantId=tenant_id,
            contractVersion=self._contract_version,
            sources=sources,
            partialFailure=len(errors) > 0,
            errors=errors,
            normalized=normalized,
        )
        return PlatformCapabilitiesResponse(data=data)

    def _build_normalized_capabilities(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
    ) -> PlatformCapabilitiesNormalized:
        input_modes_by_source: dict[str, list[str]] = {}
        input_modes_union: list[str] = []
        for source_name, source_payload in sources.items():
            source_modes = source_payload.get("supportedInputModes", [])
            if not isinstance(source_modes, list):
                source_modes = []
            normalized_modes = [str(mode) for mode in source_modes]
            input_modes_by_source[source_name] = normalized_modes
            for mode in normalized_modes:
                if mode not in input_modes_union:
                    input_modes_union.append(mode)

        feature_enabled = {
            "pas_core_snapshot": self._feature_enabled(
                sources=sources, source_name="pas", feature_key="pas.integration.core_snapshot"
            ),
            "pas_intake": self._feature_enabled(
                sources=sources, source_name="pas", feature_key="pas.ingestion.bulk_upload"
            ),
            "pa_analytics": any(
                self._feature_enabled(sources=sources, source_name="pa", feature_key=key)
                for key in (
                    "pa.analytics.twr",
                    "pa.analytics.mwr",
                    "pa.analytics.contribution",
                    "pa.analytics.attribution",
                )
            ),
            "dpm_lifecycle": self._feature_enabled(
                sources=sources, source_name="dpm", feature_key="dpm.proposals.lifecycle"
            ),
            "dpm_support": self._feature_enabled(
                sources=sources, source_name="dpm", feature_key="dpm.support.run_apis"
            ),
        }

        module_health = self._module_health(sources=sources, errors=errors)
        navigation = {
            "command_center": True,
            "portfolio_intake": feature_enabled["pas_intake"] or feature_enabled["pas_core_snapshot"],
            "analytics_studio": feature_enabled["pa_analytics"],
            "advisory_pipeline": feature_enabled["dpm_lifecycle"],
            "scenario_builder": feature_enabled["dpm_lifecycle"],
            "decision_console": (
                feature_enabled["pas_core_snapshot"]
                and (feature_enabled["dpm_lifecycle"] or feature_enabled["dpm_support"])
            ),
        }
        workflow_flags = {
            "proposal_lifecycle": self._workflow_enabled(
                sources=sources, source_name="dpm", workflow_key="proposal_lifecycle"
            ),
            "proposal_approval_flow": self._workflow_enabled(
                sources=sources, source_name="dpm", workflow_key="proposal_approval_flow"
            ),
            "portfolio_bulk_onboarding": self._workflow_enabled(
                sources=sources, source_name="pas", workflow_key="portfolio_bulk_onboarding"
            ),
            "performance_snapshot": self._workflow_enabled(
                sources=sources, source_name="pa", workflow_key="performance_snapshot"
            ),
        }
        return PlatformCapabilitiesNormalized(
            navigation=navigation,
            workflowFlags=workflow_flags,
            inputModesBySource=input_modes_by_source,
            inputModesUnion=input_modes_union,
            moduleHealth=module_health,
        )

    def _feature_enabled(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
        feature_key: str,
    ) -> bool:
        source_payload = sources.get(source_name, {})
        features = source_payload.get("features", [])
        if not isinstance(features, list):
            return False
        for feature in features:
            if not isinstance(feature, dict):
                continue
            if str(feature.get("key")) == feature_key:
                return bool(feature.get("enabled"))
        return False

    def _workflow_enabled(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
        workflow_key: str,
    ) -> bool:
        source_payload = sources.get(source_name, {})
        workflows = source_payload.get("workflows", [])
        if not isinstance(workflows, list):
            return False
        for workflow in workflows:
            if not isinstance(workflow, dict):
                continue
            if str(workflow.get("workflow_key")) == workflow_key:
                return bool(workflow.get("enabled"))
        return False

    def _module_health(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
    ) -> dict[str, str]:
        errored_sources = {error.service for error in errors}
        health: dict[str, str] = {}
        for source_name in ("pas", "pa", "dpm"):
            if source_name in sources:
                health[source_name] = "available"
            elif source_name in errored_sources:
                health[source_name] = "unavailable"
            else:
                health[source_name] = "unknown"
        return health
