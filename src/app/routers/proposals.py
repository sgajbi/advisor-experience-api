from uuid import uuid4

from fastapi import APIRouter, Header, Query

from app.clients.dpm_client import DpmClient
from app.config import settings
from app.contracts.proposals import (
    ProposalApprovalActionRequest,
    ProposalCreateRequest,
    ProposalEnvelopeResponse,
    ProposalSimulateRequest,
    ProposalSimulateResponse,
    ProposalSubmitRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.proposal_service import ProposalService

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


def _proposal_service() -> ProposalService:
    return ProposalService(
        dpm_client=DpmClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        )
    )


@router.post("/simulate", response_model=ProposalSimulateResponse)
async def simulate_proposal(
    request: ProposalSimulateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ProposalSimulateResponse:
    service = _proposal_service()
    resolved_idempotency_key = idempotency_key or f"bff-{uuid4()}"
    correlation_id = correlation_id_var.get()
    return await service.simulate_proposal(
        body=request.body,
        idempotency_key=resolved_idempotency_key,
        correlation_id=correlation_id,
    )


@router.post("", response_model=ProposalEnvelopeResponse)
async def create_proposal(
    request: ProposalCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    resolved_idempotency_key = idempotency_key or f"bff-{uuid4()}"
    correlation_id = correlation_id_var.get()
    return await service.create_proposal(
        body=request.body,
        idempotency_key=resolved_idempotency_key,
        correlation_id=correlation_id,
    )


@router.get("", response_model=ProposalEnvelopeResponse)
async def list_proposals(
    portfolio_id: str | None = Query(default=None),
    state: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    created_from: str | None = Query(default=None),
    created_to: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    filters = {
        "portfolio_id": portfolio_id,
        "state": state,
        "created_by": created_by,
        "created_from": created_from,
        "created_to": created_to,
        "limit": limit,
        "cursor": cursor,
    }
    return await service.list_proposals(filters=filters, correlation_id=correlation_id)


@router.get("/{proposal_id}", response_model=ProposalEnvelopeResponse)
async def get_proposal(
    proposal_id: str,
    include_evidence: bool = Query(default=False),
) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal(
        proposal_id=proposal_id,
        include_evidence=include_evidence,
        correlation_id=correlation_id,
    )


@router.post("/{proposal_id}/submit", response_model=ProposalEnvelopeResponse)
async def submit_proposal(
    proposal_id: str,
    request: ProposalSubmitRequest,
) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.submit_proposal(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        review_type=request.review_type,
        reason=request.reason,
        related_version_no=request.related_version_no,
        correlation_id=correlation_id,
    )


@router.post("/{proposal_id}/approve-risk", response_model=ProposalEnvelopeResponse)
async def approve_risk(
    proposal_id: str,
    request: ProposalApprovalActionRequest,
) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.approve_risk(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        details=request.details,
        related_version_no=request.related_version_no,
        correlation_id=correlation_id,
    )


@router.post("/{proposal_id}/approve-compliance", response_model=ProposalEnvelopeResponse)
async def approve_compliance(
    proposal_id: str,
    request: ProposalApprovalActionRequest,
) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.approve_compliance(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        details=request.details,
        related_version_no=request.related_version_no,
        correlation_id=correlation_id,
    )


@router.post("/{proposal_id}/record-client-consent", response_model=ProposalEnvelopeResponse)
async def record_client_consent(
    proposal_id: str,
    request: ProposalApprovalActionRequest,
) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.record_client_consent(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        details=request.details,
        related_version_no=request.related_version_no,
        correlation_id=correlation_id,
    )


@router.get("/{proposal_id}/workflow-events", response_model=ProposalEnvelopeResponse)
async def get_workflow_events(proposal_id: str) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workflow_events(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get("/{proposal_id}/approvals", response_model=ProposalEnvelopeResponse)
async def get_approvals(proposal_id: str) -> ProposalEnvelopeResponse:
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_approvals(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )
