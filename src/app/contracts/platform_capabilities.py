from typing import Any

from pydantic import BaseModel, Field


class CapabilitySourceError(BaseModel):
    service: str
    status_code: int
    detail: str


class PlatformCapabilitiesData(BaseModel):
    consumer_system: str = Field(alias="consumerSystem")
    tenant_id: str = Field(alias="tenantId")
    contract_version: str = Field(alias="contractVersion")
    sources: dict[str, dict[str, Any]]
    partial_failure: bool = Field(alias="partialFailure")
    errors: list[CapabilitySourceError] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class PlatformCapabilitiesResponse(BaseModel):
    data: PlatformCapabilitiesData
