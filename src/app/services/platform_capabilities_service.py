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
            self._pas_client.get_effective_policy(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            return_exceptions=True,
        )

        sources: dict[str, dict[str, Any]] = {}
        errors: list[CapabilitySourceError] = []
        service_names = ["pas", "pa", "dpm"]

        for service_name, result in zip(service_names, results[:3], strict=True):
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

        pas_policy_payload: dict[str, Any] | None = None
        pas_policy_result = results[3]
        if isinstance(pas_policy_result, BaseException):
            errors.append(
                CapabilitySourceError(
                    service="pas_policy",
                    status_code=500,
                    detail=f"upstream_exception: {pas_policy_result}",
                )
            )
        else:
            policy_status_code, policy_payload = cast(tuple[int, dict[str, Any]], pas_policy_result)
            if policy_status_code >= 400:
                errors.append(
                    CapabilitySourceError(
                        service="pas_policy",
                        status_code=policy_status_code,
                        detail=str(policy_payload.get("detail", policy_payload)),
                    )
                )
            else:
                pas_policy_payload = policy_payload

        normalized = self._build_normalized_capabilities(
            sources=sources,
            errors=errors,
            pas_policy=pas_policy_payload,
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
        pas_policy: dict[str, Any] | None,
    ) -> PlatformCapabilitiesNormalized:
        input_modes_by_source: dict[str, list[str]] = {}
        input_modes_union: list[str] = []
        policy_versions_by_source: dict[str, str] = {}
        for source_name, source_payload in sources.items():
            source_modes = source_payload.get("supportedInputModes", [])
            if not isinstance(source_modes, list):
                source_modes = []
            normalized_modes = [str(mode) for mode in source_modes]
            input_modes_by_source[source_name] = normalized_modes
            policy_versions_by_source[source_name] = str(
                source_payload.get("policyVersion", "unknown")
            )
            for mode in normalized_modes:
                if mode not in input_modes_union:
                    input_modes_union.append(mode)
        for source_name in ("pas", "pa", "dpm"):
            policy_versions_by_source.setdefault(source_name, "unknown")

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
            "portfolio_intake": (
                feature_enabled["pas_intake"] or feature_enabled["pas_core_snapshot"]
            ),
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
        pas_policy_diagnostics = self._pas_policy_diagnostics(
            pas_policy=pas_policy,
            errors=errors,
        )
        return PlatformCapabilitiesNormalized(
            navigation=navigation,
            workflowFlags=workflow_flags,
            inputModesBySource=input_modes_by_source,
            inputModesUnion=input_modes_union,
            moduleHealth=module_health,
            policyVersionsBySource=policy_versions_by_source,
            pasPolicyDiagnostics=pas_policy_diagnostics,
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

    def _pas_policy_diagnostics(
        self,
        *,
        pas_policy: dict[str, Any] | None,
        errors: list[CapabilitySourceError],
    ) -> dict[str, Any]:
        diagnostics: dict[str, Any] = {
            "available": False,
            "allowedSections": [],
            "warnings": [],
            "policyProvenance": {
                "policyVersion": "unknown",
                "policySource": "unknown",
                "matchedRuleId": "unknown",
                "strictMode": False,
            },
        }

        if pas_policy is not None:
            diagnostics["available"] = True
            allowed_sections = pas_policy.get("allowedSections", [])
            warnings = pas_policy.get("warnings", [])
            provenance = pas_policy.get("policyProvenance", {})
            diagnostics["allowedSections"] = (
                [str(section) for section in allowed_sections]
                if isinstance(allowed_sections, list)
                else []
            )
            diagnostics["warnings"] = (
                [str(warning) for warning in warnings] if isinstance(warnings, list) else []
            )
            if isinstance(provenance, dict):
                diagnostics["policyProvenance"] = {
                    "policyVersion": str(provenance.get("policyVersion", "unknown")),
                    "policySource": str(provenance.get("policySource", "unknown")),
                    "matchedRuleId": str(provenance.get("matchedRuleId", "unknown")),
                    "strictMode": bool(provenance.get("strictMode", False)),
                }

        if any(error.service == "pas_policy" for error in errors):
            diagnostics["warnings"] = list(diagnostics["warnings"]) + [
                "PAS_POLICY_ENDPOINT_UNAVAILABLE"
            ]
        return diagnostics
