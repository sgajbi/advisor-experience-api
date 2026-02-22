from typing import Any

from pydantic import BaseModel, Field


class ProposalSimulateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Raw payload passed through to DPM /rebalance/proposals/simulate."
    )


class ProposalSimulateResponse(BaseModel):
    correlation_id: str
    contract_version: str = "v1"
    data: dict[str, Any]
