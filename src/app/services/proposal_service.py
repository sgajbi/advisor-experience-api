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

    async def get_proposal_version(
        self,
        proposal_id: str,
        version_no: int,
        include_evidence: bool,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_proposal_version(
            proposal_id=proposal_id,
            version_no=version_no,
            include_evidence=include_evidence,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def create_proposal_version(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._dpm_client.create_proposal_version(
            proposal_id=proposal_id,
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

    async def approve_risk(
        self,
        proposal_id: str,
        actor_id: str,
        expected_state: str,
        details: dict[str, Any],
        related_version_no: int | None,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        return await self._record_approval(
            proposal_id=proposal_id,
            approval_type="RISK",
            actor_id=actor_id,
            expected_state=expected_state,
            details=details,
            related_version_no=related_version_no,
            correlation_id=correlation_id,
        )

    async def approve_compliance(
        self,
        proposal_id: str,
        actor_id: str,
        expected_state: str,
        details: dict[str, Any],
        related_version_no: int | None,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        return await self._record_approval(
            proposal_id=proposal_id,
            approval_type="COMPLIANCE",
            actor_id=actor_id,
            expected_state=expected_state,
            details=details,
            related_version_no=related_version_no,
            correlation_id=correlation_id,
        )

    async def record_client_consent(
        self,
        proposal_id: str,
        actor_id: str,
        expected_state: str,
        details: dict[str, Any],
        related_version_no: int | None,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        return await self._record_approval(
            proposal_id=proposal_id,
            approval_type="CLIENT_CONSENT",
            actor_id=actor_id,
            expected_state=expected_state,
            details=details,
            related_version_no=related_version_no,
            correlation_id=correlation_id,
        )

    async def get_workflow_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_workflow_events(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_approvals(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def _record_approval(
        self,
        proposal_id: str,
        approval_type: str,
        actor_id: str,
        expected_state: str,
        details: dict[str, Any],
        related_version_no: int | None,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        payload: dict[str, Any] = {
            "approval_type": approval_type,
            "approved": True,
            "actor_id": actor_id,
            "expected_state": expected_state,
            "details": details,
        }
        if related_version_no is not None:
            payload["related_version_no"] = related_version_no

        upstream_status, upstream_payload = await self._dpm_client.record_approval(
            proposal_id=proposal_id,
            body=payload,
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
