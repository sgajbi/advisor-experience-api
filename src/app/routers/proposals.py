from uuid import uuid4

from fastapi import APIRouter, Header

from app.clients.dpm_client import DpmClient
from app.config import settings
from app.contracts.proposals import ProposalSimulateRequest, ProposalSimulateResponse
from app.middleware.correlation import correlation_id_var
from app.services.proposal_service import ProposalService

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post("/simulate", response_model=ProposalSimulateResponse)
async def simulate_proposal(
    request: ProposalSimulateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ProposalSimulateResponse:
    service = ProposalService(
        dpm_client=DpmClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        )
    )

    resolved_idempotency_key = idempotency_key or f"bff-{uuid4()}"
    correlation_id = correlation_id_var.get()
    return await service.simulate_proposal(
        body=request.body,
        idempotency_key=resolved_idempotency_key,
        correlation_id=correlation_id,
    )
