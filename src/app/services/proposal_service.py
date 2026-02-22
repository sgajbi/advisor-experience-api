from typing import Any

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.config import settings
from app.contracts.proposals import ProposalEnvelopeResponse, ProposalSimulateResponse


class ProposalService:
    def __init__(self, dpm_client: DpmClient):
        self._dpm_client = dpm_client

    async def simulate_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalSimulateResponse:
        upstream_status, upstream_payload = await self._dpm_client.simulate_proposal(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            detail: str | dict[str, Any] = upstream_payload
            if not isinstance(detail, str):
                detail = str(detail)
            raise HTTPException(status_code=upstream_status, detail=detail)

        return ProposalSimulateResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def create_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._dpm_client.create_proposal(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def list_proposals(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_proposals(
            params=filters,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_proposal(
            proposal_id=proposal_id,
            include_evidence=include_evidence,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def submit_proposal(
        self,
        proposal_id: str,
        actor_id: str,
        expected_state: str,
        review_type: str,
        reason: dict[str, Any],
        related_version_no: int | None,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        event_type = (
            "SUBMITTED_FOR_COMPLIANCE_REVIEW"
            if review_type == "COMPLIANCE"
            else "SUBMITTED_FOR_RISK_REVIEW"
        )
        transition_body: dict[str, Any] = {
            "event_type": event_type,
            "actor_id": actor_id,
            "expected_state": expected_state,
            "reason": reason,
        }
        if related_version_no is not None:
            transition_body["related_version_no"] = related_version_no

        upstream_status, upstream_payload = await self._dpm_client.transition_proposal(
            proposal_id=proposal_id,
            body=transition_body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            detail: str | dict[str, Any] = upstream_payload
            if not isinstance(detail, str):
                detail = str(detail)
            raise HTTPException(status_code=upstream_status, detail=detail)
