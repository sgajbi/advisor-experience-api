from typing import Any

from pydantic import BaseModel, Field


class CapabilitySourceError(BaseModel):
    service: str
    status_code: int
    detail: str


class PlatformCapabilitiesNormalized(BaseModel):
    navigation: dict[str, bool]
    workflow_flags: dict[str, bool] = Field(alias="workflowFlags")
    input_modes_by_source: dict[str, list[str]] = Field(alias="inputModesBySource")
    input_modes_union: list[str] = Field(alias="inputModesUnion")
    module_health: dict[str, str] = Field(alias="moduleHealth")

    model_config = {"populate_by_name": True}


class PlatformCapabilitiesData(BaseModel):
    consumer_system: str = Field(alias="consumerSystem")
    tenant_id: str = Field(alias="tenantId")
    contract_version: str = Field(alias="contractVersion")
    sources: dict[str, dict[str, Any]]
    partial_failure: bool = Field(alias="partialFailure")
    errors: list[CapabilitySourceError] = Field(default_factory=list)
    normalized: PlatformCapabilitiesNormalized

    model_config = {"populate_by_name": True}


class PlatformCapabilitiesResponse(BaseModel):
    data: PlatformCapabilitiesData
