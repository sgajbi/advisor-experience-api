from typing import Any

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.config import settings
from app.contracts.proposals import ProposalSimulateResponse


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
