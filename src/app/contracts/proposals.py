from typing import Any, Literal

from pydantic import BaseModel, Field


class ProposalSimulateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Raw payload passed through to DPM /rebalance/proposals/simulate."
    )


class ProposalSimulateResponse(BaseModel):
    correlation_id: str
    contract_version: str = "v1"
    data: dict[str, Any]


class ProposalCreateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Raw payload passed through to DPM /rebalance/proposals."
    )


class ProposalSubmitRequest(BaseModel):
    actor_id: str = Field(description="Actor id requesting submit transition.")
    expected_state: str = Field(
        default="DRAFT",
        description="Expected current state for optimistic concurrency check.",
    )
    review_type: Literal["RISK", "COMPLIANCE"] = Field(
        default="RISK",
        description="Target first review stage for submit.",
    )
    related_version_no: int | None = Field(
        default=None,
        description="Optional related version number for audit linkage.",
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured reason payload captured in workflow event.",
    )


class ProposalApprovalActionRequest(BaseModel):
    actor_id: str = Field(description="Actor id recording approval action.")
    expected_state: str = Field(description="Expected current workflow state.")
    related_version_no: int | None = Field(
        default=None,
        description="Optional related version number for audit linkage.",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured approval metadata/details.",
    )


class ProposalEnvelopeResponse(BaseModel):
    correlation_id: str
    contract_version: str = "v1"
    data: dict[str, Any]
