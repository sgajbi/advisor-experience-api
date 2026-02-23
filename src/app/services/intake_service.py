from typing import Any

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.clients.pas_client import PasClient
from app.clients.pas_ingestion_client import PasIngestionClient
from app.config import settings
from app.contracts.intake import EnvelopeResponse, LookupResponse


class IntakeService:
    def __init__(
        self,
        pas_ingestion_client: PasIngestionClient,
        pas_query_client: PasClient,
    ):
        self._pas_ingestion_client = pas_ingestion_client
        self._pas_query_client = pas_query_client

    async def ingest_portfolio_bundle(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> EnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._pas_ingestion_client.ingest_portfolio_bundle(
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, data=upstream_payload)

    async def preview_upload(
        self,
        entity_type: str,
        filename: str,
        content: bytes,
        sample_size: int,
        correlation_id: str,
    ) -> EnvelopeResponse:
        upstream_status, upstream_payload = await self._pas_ingestion_client.preview_upload(
            entity_type=entity_type,
            filename=filename,
            content=content,
            sample_size=sample_size,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, data=upstream_payload)

    async def commit_upload(
        self,
        entity_type: str,
        filename: str,
        content: bytes,
        allow_partial: bool,
        correlation_id: str,
    ) -> EnvelopeResponse:
        upstream_status, upstream_payload = await self._pas_ingestion_client.commit_upload(
            entity_type=entity_type,
            filename=filename,
            content=content,
            allow_partial=allow_partial,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, data=upstream_payload)

    async def get_portfolio_lookups(self, correlation_id: str) -> LookupResponse:
        upstream_status, upstream_payload = await self._pas_query_client.get_portfolio_lookups(
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._lookup_response(
            correlation_id=correlation_id, upstream_payload=upstream_payload
        )

    async def get_instrument_lookups(self, limit: int, correlation_id: str) -> LookupResponse:
        upstream_status, upstream_payload = await self._pas_query_client.get_instrument_lookups(
            limit=limit,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._lookup_response(
            correlation_id=correlation_id, upstream_payload=upstream_payload
        )

    async def get_currency_lookups(self, correlation_id: str) -> LookupResponse:
        upstream_status, upstream_payload = await self._pas_query_client.get_currency_lookups(
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._lookup_response(
            correlation_id=correlation_id, upstream_payload=upstream_payload
        )

    def _envelope(self, correlation_id: str, data: dict[str, Any]) -> EnvelopeResponse:
        return EnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=data,
        )

    def _lookup_response(
        self, correlation_id: str, upstream_payload: dict[str, Any]
    ) -> LookupResponse:
        try:
            return LookupResponse(
                correlation_id=correlation_id,
                contract_version=settings.contract_version,
                items=upstream_payload.get("items", []),
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid PAS lookup contract payload: {exc}",
            ) from exc

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
