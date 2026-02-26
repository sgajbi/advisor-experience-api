from typing import Any

from pydantic import BaseModel, Field


class IntakeBundleRequest(BaseModel):
    body: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw payload passed through to lotus-core ingestion /ingest/portfolio-bundle.",
    )


class EnvelopeResponse(BaseModel):
    correlation_id: str
    contract_version: str
    data: dict[str, Any]


class LookupItem(BaseModel):
    id: str
    label: str


class LookupResponse(BaseModel):
    correlation_id: str
    contract_version: str
    items: list[LookupItem]
